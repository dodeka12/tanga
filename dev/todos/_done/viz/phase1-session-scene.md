# Phase 1: Visualizer Session & Scene State Manager

**Files:** `py/pytanga/viz/visualizer.py`, `py/pytanga/viz/scene.py`

**Goal:** Create the top-level `Visualizer` class (user-facing API) and the internal
`Scene` state manager that tracks entities, generates unique IDs, computes diffs,
and holds camera/scene configuration.

**Prerequisites:** None (greenfield)

---

## 1. Scene Configuration (`scene.py`)

### 1.1 CameraConfig Dataclass

A dataclass for camera settings that flows from Python to the JS frontend:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class CameraConfig:
    """Camera configuration for the 3D viewer.

    All fields are optional. When a field is None, the browser uses its default
    or computes the value automatically from scene bounds (auto-fit).
    """
    position: tuple[float, float, float] | None = None  # (x, y, z) camera position
    target: tuple[float, float, float] | None = None    # (x, y, z) look-at point
    fov: float | None = None                             # vertical field of view in degrees
    near: float | None = None                            # near clipping plane
    far: float | None = None                             # far clipping plane

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict, omitting None values."""
        result = {}
        if self.position is not None:
            result["position"] = list(self.position)
        if self.target is not None:
            result["target"] = list(self.target)
        if self.fov is not None:
            result["fov"] = self.fov
        if self.near is not None:
            result["near"] = self.near
        if self.far is not None:
            result["far"] = self.far
        return result
```

### 1.2 SceneConfig Dataclass

Top-level configuration for the rendered 3D space:

```python
@dataclass
class SceneConfig:
    """Configuration for the 3D viewer scene.

    Sent to the browser on initial WebSocket handshake, before any entity data.
    """
    space_extent: float = 10.0       # half-extent of visible space; affects grid size
    show_grid: bool = True           # show ground grid
    show_axes: bool = True           # show RGB axes helper
    background_color: str = "#1a1a2e"
    camera: CameraConfig | None = None  # None = auto-fit from entities

    def to_dict(self) -> dict:
        result = {
            "type": "scene_config",
            "space_extent": self.space_extent,
            "show_grid": self.show_grid,
            "show_axes": self.show_axes,
            "background_color": self.background_color,
        }
        if self.camera is not None:
            cam = self.camera.to_dict()
            if cam:
                result["camera"] = cam
        return result
```

### 1.3 Scene State Manager

The `Scene` class now also holds the `SceneConfig` and `CameraConfig`:

```python
class Scene:
    """Manages the state of all entities and scene configuration."""

    def __init__(self, config: SceneConfig | None = None) -> None:
        self._entities: Dict[str, SceneEntity] = {}
        self._order: List[str] = []
        self.config = config or SceneConfig()
        self._config_sent = False  # track whether scene_config was already pushed

    def add(
        self,
        entity: GeoEntity | None,
        *,
        kind: str | None = None,
        entity_id: str | None = None,
        **properties: Any,
    ) -> str:
        """Add an entity and return its ID.

        Args:
            entity: A pytanga.geometry Entity or None (for MV-backed or custom).
            kind: Override the entity kind string. Auto-detected from type if None.
            entity_id: Explicit ID. Auto-generated UUID if None.
            **properties: Rendering properties (color, opacity, size, wireframe, etc.)
        """
        ...

    def update(self, entity_id: str, **properties: Any) -> None:
        """Update rendering properties of an existing entity. Marks it dirty."""
        ...

    def update_entity(self, entity_id: str, entity: GeoEntity) -> None:
        """Replace the geometry entity for an existing ID. Marks it dirty."""
        ...

    def remove(self, entity_id: str) -> None:
        """Remove an entity. It will be included in the next 'removed' list, then forgotten."""
        ...

    def clear(self) -> None:
        """Remove all entities."""
        ...

    def flush(
        self, *, defaults: Dict[str, Any] | None = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Compute the JSON payload for the current state.

        The ``defaults`` dict (from Visualizer._defaults) is forwarded to the
        serializer to resolve per-entity-kind colors and extent values.

        Returns:
            (entities_list, removed_ids): entities_list contains full state for all
            dirty entities and new entities. Removed_ids lists entities to destroy
            on the client.

        After this call, all entities are marked clean and the removed list is cleared.
        """
        ...

    def full_state(
        self, *, defaults: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Return the complete scene state (all entities, full serialization).

        The ``defaults`` dict is forwarded to the serializer. Used for initial
        sync when a new client connects.
        """
        ...

    @staticmethod
    def _kind_from_entity(entity: GeoEntity) -> str:
        """Determine the kind string from a geometry entity type."""
        return type(entity).__name__


def generate_id() -> str:
    """Generate a short, unique entity ID."""
    return uuid4().hex[:8]
```

### 1.2 Key Design Decisions

1. **Dirty tracking:** Only changed entities are serialized on `flush()`. This enables
   efficient frame streaming where Python pushes 60 FPS updates for only the moving
   entities — stationary entities incur zero serialization cost.

2. **Entity reference vs. properties:** The `SceneEntity` stores both the original
   `pytanga.geometry.Entity` (for the serializer to extract geometry) and a `properties`
   dict (for rendering attributes like color, opacity). The serializer combines both.

3. **ID stability:** IDs are stable across updates. The JS side uses them as keys in
   a `Map<id, THREE.Object3D>` for O(1) lookup on updates.

4. **No algebra dependency:** The `Scene` class only depends on `pytanga.geometry.entities`.
   It does not know about MVs, algebras, or bases. MV-backed visualization will go through
   the geometry submodule analysis first.

---

## 2. Visualizer Class (`visualizer.py`)

### 2.1 Design

The `Visualizer` is the single user-facing class. It owns:
- A `Scene` instance (with `SceneConfig` and `CameraConfig`)
- A `Server` instance (Phase 3)
- Configuration (port, auto-open-browser)

```python
# py/pytanga/viz/visualizer.py

from __future__ import annotations
from typing import Any, Optional

from pytanga.geometry.entities import Entity as GeoEntity

from .scene import Scene, SceneConfig, CameraConfig


class Visualizer:
    """Interactive 3D visualization of geometric entities via Three.js in a browser.

    Camera can be configured explicitly or computed automatically from entities.

    Usage:
        # Simple: auto-fit camera from entities
        viz = Visualizer()

        # Explicit camera
        viz = Visualizer(
            camera=CameraConfig(
                position=(10, 6, 12),
                target=(0, 0, 0),
                fov=50,
            ),
            space_extent=15,
        )

        viz.add(Point(1, 2, 3), color="#ff4444")
        viz.run()  # blocks until browser window is closed
    """

    def __init__(
        self,
        *,
        port: int = 8765,
        host: str = "localhost",
        open_browser: bool = True,
        title: str = "Tanga 3D Viewer",
        # Scene configuration
        space_extent: float = 10.0,
        show_grid: bool = True,
        show_axes: bool = True,
        background_color: str = "#1a1a2e",
        # Camera configuration (None = auto-fit from entities)
        camera: CameraConfig | None = None,
    ) -> None:
        self._config = SceneConfig(
            space_extent=space_extent,
            show_grid=show_grid,
            show_axes=show_axes,
            background_color=background_color,
            camera=camera,
        )
        self._scene = Scene(self._config)
        self._port = port
        self._host = host
        self._open_browser = open_browser
        self._title = title
        self._server = None  # Set in start() / run() (Phase 3)

        # Default rendering properties — applied when no per-entity override is given.
        # These are stored on the Visualizer, not SceneConfig, because they only
        # affect the serializer defaults, not the JS frontend.
        self._defaults: dict[str, Any] = {
            # Per-entity-kind color overrides
            "color_point": "#ff4444",
            "color_direction": "#ffffff",
            "color_homogeneous_point": "#ff8844",
            "color_point_pair": "#44ff44",
            "color_line": "#44ff44",
            "color_plane": "#4488ff",
            "color_circle": "#ff44ff",
            "color_sphere": "#ffaa00",
            "color_space": "#888888",
            # Infinite-object extent defaults
            "line_length": 20.0,
            "line_thickness": 0.03,
            "plane_extent": 10.0,
            "space_extent_render": 10.0,
            # Label defaults
            "label_offset_y": 0.3,      # vertical offset above entity center
            "label_font_size": 14,      # CSS font-size in px
            "label_color": "#ffffff",
            "label_background": "rgba(0, 0, 0, 0.6)",
        }

    # --- Default Render Property Getters/Setters ---

    @property
    def defaults(self) -> dict[str, Any]:
        """Return a copy of the current default render properties dict.

        Keys include:
            color_point, color_direction, color_line, color_plane,
            color_circle, color_sphere, color_space, color_homogeneous_point,
            color_point_pair,
            line_length, line_thickness, plane_extent, space_extent_render.
        """
        return dict(self._defaults)

    def set_defaults(self, **kwargs: Any) -> None:
        """Bulk-set default rendering properties.

        Valid keys are the same as returned by the ``defaults`` property.
        Unknown keys raise KeyError.
        """
        for key, value in kwargs.items():
            if key not in self._defaults:
                raise KeyError(
                    f"Unknown default property {key!r}. Valid keys: "
                    f"{list(self._defaults.keys())}"
                )
            self._defaults[key] = value

    def set_default_color(
        self,
        kind: str,
        color: str | tuple[float, float, float] | tuple[float, float, float, float],
    ) -> None:
        """Set the default color for a given entity kind.

        Args:
            kind: ``"point"``, ``"direction"``, ``"line"``, ``"plane"``,
                  ``"circle"``, ``"sphere"``, ``"space"``,
                  ``"homogeneous_point"``, or ``"point_pair"``.
            color: Hex string (``"#ff4444"``) or RGB tuple ``(1.0, 0.2, 0.2)``
                   or RGBA tuple ``(1.0, 0.2, 0.2, 0.5)``.
        """
        key = f"color_{kind.lower()}"
        if key not in self._defaults:
            raise ValueError(f"Unknown entity kind: {kind!r}")
        self._defaults[key] = _normalize_color(color)

    @staticmethod
    def _normalize_color(
        color: str | tuple[float, float, float] | tuple[float, float, float, float],
    ) -> str:
        """Convert a color value to a hex string.

        Accepts:
            - ``"#ff4444"`` — passed through unchanged.
            - ``(1.0, 0.2, 0.2)`` — RGB floats in [0, 1] → ``"#ff3333"``.
            - ``(1.0, 0.2, 0.2, 0.5)`` — RGBA → alpha discarded, RGB → hex.
        """
        if isinstance(color, str):
            return color
        if isinstance(color, tuple):
            if len(color) == 3:
                r, g, b = color
            elif len(color) == 4:
                r, g, b, _ = color
            else:
                raise ValueError(f"Color tuple must have 3 or 4 elements, got {len(color)}")
            # Clamp to [0, 1] and convert to 0-255 hex
            r_byte = max(0, min(255, round(r * 255)))
            g_byte = max(0, min(255, round(g * 255)))
            b_byte = max(0, min(255, round(b * 255)))
            return f"#{r_byte:02x}{g_byte:02x}{b_byte:02x}"
        raise TypeError(f"Color must be str or tuple, got {type(color).__name__}")

    def set_default_extent(
        self,
        *,
        line_length: float | None = None,
        line_thickness: float | None = None,
        plane_extent: float | None = None,
        space_extent: float | None = None,
    ) -> None:
        """Set default extent values for infinite entities.

        All parameters are optional; only provided values are updated.
        """
        if line_length is not None:
            self._defaults["line_length"] = float(line_length)
        if line_thickness is not None:
            self._defaults["line_thickness"] = float(line_thickness)
        if plane_extent is not None:
            self._defaults["plane_extent"] = float(plane_extent)
        if space_extent is not None:
            self._defaults["space_extent_render"] = float(space_extent)

    # --- Entity Management ---

    def add(
        self,
        obj: GeoEntity | Any = None,  # GeoEntity, or pytanga.MV (multivector)
        *,
        kind: str | None = None,
        entity_id: str | None = None,
        opns: bool = True,           # only used when obj is an MV
        **properties: Any,
    ) -> str | list[str]:
        """Add a geometric entity or multivector to the scene.

        If a pytanga.geometry Entity is passed, it is serialized directly.
        If a pytanga.MV (multivector) is passed, it is analyzed via
        pytanga.geometry.analyze() first, and the resulting entity is added.
        If the MV decomposes into multiple entities, a list of IDs is returned.

        Properties can include:
            color: str | tuple[float, float, float] | tuple[float, float, float, float]
                Hex string (``"#ff4444"``) or RGB/RGBA float tuple. Normalized to hex.
            opacity: float (0.0–1.0)
            size: float (point radius, line thickness, etc.)
            wireframe: bool (show wireframe overlay)
            extent: float (for planes: half-extent of the rendered quad)
            length: float (for lines/directions: rendered length)
            label: str | None
                Text annotation displayed next to the entity.
                Rendered via CSS2DRenderer — crisp HTML text that follows
                the entity in 3D space but always faces the camera.

        Returns:
            Entity ID string, or list of strings if the MV resolves to
            multiple entities.
        """
        # Normalize color if provided
        if "color" in properties:
            properties["color"] = self._normalize_color(properties["color"])

        entity = self._resolve(obj, opns=opns)
        # If resolve returned a list, add each one
        if isinstance(entity, list):
            ids = []
            for ent in entity:
                eid = self._scene.add(ent, kind=kind, entity_id=entity_id if len(entity) == 1 else None, **properties)
                ids.append(eid)
            return ids
        return self._scene.add(entity, kind=kind, entity_id=entity_id, **properties)

    def update_entity(self, entity_id: str, obj: GeoEntity | Any, *, opns: bool = True) -> None:
        """Replace the geometry for an existing entity. Accepts Entity or MV.

        Used for animation. If an MV is passed, it is analyzed first.
        """
        entity = self._resolve(obj, opns=opns)
        if isinstance(entity, list):
            raise ValueError(
                f"update_entity expects a single entity, but the MV resolved to "
                f"{len(entity)} entities. Use the first one explicitly."
            )
        self._scene.update_entity(entity_id, entity)

    def _resolve(self, obj: Any, *, opns: bool = True) -> GeoEntity | list[GeoEntity]:
        """Resolve an MV or Entity to one or more geo entities.

        If obj is already a pytanga.geometry Entity, return it as-is.
        If obj is a pytanga.MV, call pytanga.geometry.analyze() to
        extract the geometric meaning.
        """
        from pytanga.geometry.entities import Entity as GeoEntityType

        if isinstance(obj, GeoEntityType):
            return obj

        # Assume it's an MV — try to analyze
        try:
            from pytanga.geometry import analyze
            result = analyze(obj, opns=opns)
            if result is None:
                raise ValueError(f"Could not analyze object: {obj}")
            return result  # may be Entity or list[Entity]
        except ImportError:
            raise TypeError(
                f"Object of type {type(obj).__name__} is not a recognized "
                f"geometry entity or multivector."
            )

    def remove(self, entity_id: str) -> None:
        """Remove an entity from the scene."""
        self._scene.remove(entity_id)

    def clear(self) -> None:
        """Remove all entities."""
        self._scene.clear()

    # --- Lifecycle ---

    def start(self) -> None:
        """Start the WebSocket server in a background thread (non-blocking)."""
        ...  # Phase 3

    def stop(self) -> None:
        """Stop the server and clean up."""
        ...  # Phase 3

    def flush(self) -> None:
        """Push the current scene state to all connected clients."""
        ...  # Phase 3 — calls self._scene.flush() and sends over WebSocket

    def run(self) -> None:
        """Start the server, open the browser, and block until stopped.

        This is the recommended entry point for scripts.
        """
        ...  # Phase 3

    # --- Properties ---

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"
```

### 2.2 Design Decisions

1. **Minimal API surface:** `add()`, `update()`, `update_entity()`, `remove()`, `clear()`,
   `start()`, `stop()`, `flush()`, `run()`. That's it. Nine methods.

2. **Properties as kwargs:** Instead of a config object or dict, rendering properties are
   passed as keyword arguments to `add()`. This gives IDE autocompletion and is Pythonic.

3. **Returns IDs:** `add()` returns the entity ID so users can update/remove later.

4. **Non-blocking mode:** `start()` + `flush()` enable scripting patterns where entities
   are added/updated over time without blocking the main thread. `run()` is the simple
   blocking mode for one-shot scripts.

5. **Camera auto-fit:** When `camera=None` (the default), the browser computes camera
   position and target from the bounding box of all entities. When explicit camera
   settings are provided via `CameraConfig`, those are used directly. Users can also
   set `CameraConfig(position=..., target=...)` with `fov=None` to get auto-computed
   FOV with explicit framing.

6. **Space extent:** `space_extent` controls the grid size and the default rendering
   extent for infinite entities (planes, lines, space box). Default is ±10 units.

7. **MV transparency:** `add()` and `update_entity()` accept both `pytanga.geometry`
   Entity objects and `pytanga.MV` (multivector) objects. When an MV is passed,
   `pytanga.geometry.analyze()` is called internally to extract the geometric entity.
   If the MV resolves to multiple entities (e.g., a Motor resolves to Rotor +
   Translator), all are added and a list of IDs is returned.

8. **Configurable default rendering:** The `Visualizer` stores a `_defaults` dict
   with per-entity-kind colors and extent values for infinite objects (line length/
   thickness, plane extent, space extent). Users can override these globally via
   `set_default_color()`, `set_default_extent()`, and `set_defaults()`. The
   serializer layer (Phase 2) applies a priority chain: per-entity `**properties` >
   `Visualizer._defaults` > hardcoded built-in defaults.

9. **Jupyter compatibility:** The `Visualizer` detects Jupyter/IPython environments
   automatically. In notebooks, `open_browser` defaults to `False` (no popup),
   `run()` is unavailable (would block the kernel), and the non-blocking
   `start()` / `flush()` / `stop()` pattern is used instead. A `_repr_html_()`
   method renders the viewer inline as an `<iframe>`. See Phase 7 for details.

---

## 3. Implementation Steps

1. Create `py/pytanga/viz/` directory.
2. Create `py/pytanga/viz/scene.py` with `CameraConfig`, `SceneConfig`, `SceneEntity`, and `Scene` class.
3. Create `py/pytanga/viz/visualizer.py` with `Visualizer` class (stub out `start`/`stop`/`run`/`flush`).
4. Write unit test: Create `CameraConfig` with various combinations of set/unset fields, verify `to_dict()`.
5. Write unit test: Create `SceneConfig`, verify `to_dict()` produces correct `scene_config` message format.
6. Write unit test: Create a `Scene`, add entities, call `flush()`, verify dirty tracking.
7. Write unit test: Update entity properties, verify dirty flag, verify clean after flush.

## 4. Verification Checklist

### CameraConfig
- [x] `CameraConfig.to_dict()` omits `None` fields, includes set fields as lists/scalars.
- [x] All `CameraConfig` fields are optional (can set only `fov`, only `position`, or any combination).

### SceneConfig
- [x] `SceneConfig.to_dict()` produces `{"type": "scene_config", ...}` with all fields.

### Scene State Manager
- [x] `SceneEntity` dataclass is properly defined with all fields.
- [x] `Scene.add()` generates unique IDs and stores entities.
- [x] `Scene.flush()` returns only dirty entities on first call, empty on second call (no changes).
- [x] `Scene.flush()` returns `removed_ids` for entities that were removed.
- [x] `Scene.full_state()` returns all entities regardless of dirty state.
- [x] `Scene.config` is accessible and mutable.

### Visualizer Entity Management
- [x] `Visualizer.add()` delegates to `Scene.add()` and returns the ID.
- [x] `Visualizer.add()` accepts `pytanga.geometry` Entity objects and passes them through.
- [x] `Visualizer.add()` accepts `pytanga.MV` objects, analyzes them via `pytanga.geometry.analyze()`, and adds the resulting entity.
- [x] `Visualizer.add()` returns a `list[str]` when an MV resolves to multiple entities.
- [x] `Visualizer.add()` normalizes color tuples via `_normalize_color()` (RGB → hex, RGBA → hex).
- [x] `Visualizer.update_entity()` works with both Entity and MV objects.
- [x] `Visualizer.update_entity()` raises `ValueError` if the MV resolves to multiple entities.

### Visualizer Configuration
- [x] `Visualizer` accepts `camera=CameraConfig(...)`, `space_extent`, `show_grid`, `show_axes`, `background_color`.
- [x] No circular imports between `pytanga.viz` and `pytanga.geometry`.
