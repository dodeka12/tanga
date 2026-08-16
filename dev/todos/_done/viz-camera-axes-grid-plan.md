# Viz: Camera View, Axes, and Grid Specification Plan

**Date:** 12 August 2026

Summary of changes needed across the entire tanga codebase to replace hard-coded
grid/axes in the frontend with explicit `SceneObject`s, and to provide rich 2D/3D
camera specifications.

---

## 1. Backend Data Structures

### 1.1 New dataclasses in `py/pytanga/viz/scene.py`

Add `View2DConfig` and `ViewPlaneConfig`; extend `CameraConfig`.

```python
@dataclass
class View2DConfig:
    """2D camera view defined by a rectangle centred at `center`."""
    extent_x: float          # full width of the view rectangle
    extent_y: float          # full height
    center: tuple[float, float] = (0.0, 0.0)  # point appearing at camera center

@dataclass
class ViewPlaneConfig:
    """3D camera via virtual plane. Camera optical axis = plane normal."""
    point: tuple[float, float, float]       # point on the plane
    normal: tuple[float, float, float]      # camera optical axis
    extent_u: float                          # full horizontal extent of plane
    extent_v: float                          # full vertical extent
    center: tuple[float, float, float] | None = None  # defaults to `point`
    span_u: tuple[float, float, float] | None = None   # optional horizontal direction
    fov: float = 50.0

@dataclass
class CameraConfig:
    # Existing fields (backward compat when view_2d/view_plane both None)
    position: tuple[float, float, float] | None = None
    target: tuple[float, float, float] | None = None
    fov: float | None = None
    near: float | None = None
    far: float | None = None
    # New
    view_2d: View2DConfig | None = None
    view_plane: ViewPlaneConfig | None = None

    def to_dict(self) -> dict:
        # Extend to serialize view_2d and view_plane
```

**Remove** `space_extent`, `show_grid`, `show_axes` from `SceneConfig`.

### 1.2 New file: `py/pytanga/viz/_scene_objects.py`

```python
@dataclass
class Axis:
    """Single coordinate axis with ticks and optional value labels."""
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    major_interval: float = 1.0
    minor_interval: float | None = None
    label_at_major: bool = True
    label_format: str = ".1f"
    label_size: float | None = None   # font size in px for CSS2D labels
    show_ticks: bool = True

@dataclass
class Grid:
    """Coordinate grid in a plane."""
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    dir_u: tuple[float, float, float] = (1.0, 0.0, 0.0)
    dir_v: tuple[float, float, float] = (0.0, 1.0, 0.0)
    range_u: float = 5.0
    range_v: float = 5.0
    interval_u: float = 1.0
    interval_v: float = 1.0

@dataclass
class Axes3D:
    """Convenience: expands to three Axis objects."""
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    dir_u: tuple[float, float, float] = (1.0, 0.0, 0.0)
    dir_v: tuple[float, float, float] = (0.0, 1.0, 0.0)
    dir_w: tuple[float, float, float] = (0.0, 0.0, 1.0)
    range_u: float = 5.0
    range_v: float = 5.0
    range_w: float = 5.0
    major_interval: float = 1.0
    labels: tuple[str, str, str] | None = None

@dataclass
class Axes2D:
    """Convenience: expands to two Axis objects."""
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0)
    dir_u: tuple[float, float, float] = (1.0, 0.0, 0.0)
    dir_v: tuple[float, float, float] = (0.0, 1.0, 0.0)
    range_u: float = 5.0
    range_v: float = 5.0
    major_interval: float = 1.0
    labels: tuple[str, str] | None = None
```

### 1.3 Extend `py/pytanga/viz/serializer.py`

Add:
- `_serialize_axis(ent, props, ...)` → `{"kind": "Axis", "start": [...], "end": [...], ...}`
- `_serialize_grid(ent, props, ...)` → `{"kind": "Grid", "origin": [...], ...}`

Register both in `serialize_entity()`.

### 1.4 Extend `py/pytanga/viz/_types.py`

Add `Axis`, `Grid`, `Axes3D`, `Axes2D` to `VizInputType` union.

---

## 2. Backend API Changes

### 2.1 `py/pytanga/viz/visualizer.py`

- Remove `space_extent`, `show_grid`, `show_axes` from `__init__` params.
- Remove `SceneConfig` fields.
- In `_add_to_scene()`: expand `Axes3D`/`Axes2D` into individual `Axis` objects.
- Handle `Axis`/`Grid` as scene-layer `SceneObject`s.
- Add `set_camera(camera: CameraConfig)` method.
- Add `_add_default_scene_objects()` called after first browser connects — adds
  default `Axes3D` (or `Axes2D` for `space_dim=2`) and `Grid` if the user hasn't
  added any.

### 2.2 `py/pytanga/viz/_app.py`

Remove `space_extent`, `show_grid`, `show_axes` params from `VisualizerApp.__init__`.

### 2.3 `py/pytanga/viz/_scene_handle.py`

- Remove `_space_extent` property.
- Add `set_camera()` method.
- Remove `space_extent` usage in `display()` height calculation — use sensible
  default instead.

### 2.4 `py/pytanga/viz/_jupyter.py`

Remove `_space_extent` property requirement from the mixin contract.
Replace with a sensible default for iframe height.

### 2.5 `py/pytanga/viz/__init__.py`

Export new types: `View2DConfig`, `ViewPlaneConfig`, `Axis`, `Grid`, `Axes3D`, `Axes2D`.

---

## 3. Frontend Changes

### 3.1 `py/pytanga/viz/templates/viewer.js`

- In `initScene()`: remove `window._gridHelper` and `window._axesHelper` creation.
- In `applySceneConfig()`: remove grid/axes creation block. Handle `view_2d` and 
  `view_plane` camera fields.
- Ensure Axis and Grid entities flow through `upsertObject()` → `createEntityMesh()`.

### 3.2 `py/pytanga/viz/templates/view_mode.js`

- **Rewrite `switchToCamera()`** to handle `view_2d` and `view_plane`:
  - `view_2d`: compute orthographic frustum from `extent_x`/`extent_y`, respecting
    aspect ratio so the larger extent fits. Position at `(center.x, center.y, 20)`.
  - `view_plane`: compute camera distance from `fov` and `max(extent_u, extent_v)`.
    If `span_u` given: orthogonalize against normal → **û**, **v̂** = cross(normal, **û**).
    If not given: auto-compute **û** from reference vector, then **v̂**.
    Camera position = center + **n̂** * distance; up = **v̂**.
- **Remove `createGrid()`** export (no longer used — Grid is a SceneObject now).
- Update `handleResize()` to use custom extents from `view_2d` when available.

### 3.3 New: `renderers/axis.js`

```
export function createAxis(ent) → THREE.Group
```

- Draws a line from `start` to `end`.
- At major intervals: small perpendicular tick mark + optional CSS2D value label.
- At minor intervals: smaller perpendicular tick mark only.
- Works in any direction, 2D or 3D.

### 3.4 New: `renderers/grid.js`

```
export function createGrid(ent) → THREE.Group
```

- Draws a mesh of lines in the UV plane.
- Lines parallel to `dir_u` at each `interval_v` step.
- Lines parallel to `dir_v` at each `interval_u` step.
- Uses `THREE.Line` with `THREE.BufferGeometry`, grouped.

### 3.5 `renderers/factory.js`

Add:
```
case 'Axis':  mesh = createAxis(ent); break;
case 'Grid':  mesh = createGrid(ent); break;
```

---

## 4. HTML Export Changes

### 4.1 `py/pytanga/viz/export/_html.py`

- Remove `show_grid`/`show_axes`/`space_extent` references from `_build_static_fullpage_adapter()`.
- Remove inline grid/axes creation code in the adapter.
- Grid/axes are now part of the entity data (serialized Axis/Grid objects)
  that get rendered by `createEntityMesh()`.

### 4.2 `py/pytanga/viz/export/_animated_figure.py`

- Both `_build_animated_figure_adapter()` and `_build_animated_fullpage_adapter()`:
  - Remove `show_grid`, `show_axes`, `space_extent` params from `js_scene_setup()` calls.
  - Remove grid/axes from `FigureStyle` defaults.

### 4.3 `py/pytanga/viz/export/_bootstrap/_scene.py`

- **`js_scene_setup()`**: remove `show_grid`, `show_axes`, `space_extent` params
  and associated code blocks entirely.
- Also remove 2D orthographic camera creation from `space_extent` — the static
  export now uses entity-based grid/axes and camera config.

### 4.4 `py/pytanga/viz/export/_bootstrap/__init__.py`

Re-exports unchanged — but `js_scene_setup` signature changes so ensure all 
callers are updated (see §4.2, 4.3 above).

### 4.5 `py/pytanga/viz/export/_figure_html.py`

Remove `show_grid`, `show_axes` from `FigureStyle` usage and `js_scene_setup()` calls.

### 4.6 `py/pytanga/viz/_styles/_overlay_styles.py`

Remove `show_grid` and `show_axes` from `FigureStyle`.

### 4.7 `py/pytanga/viz/templates/export_viewer.html`

Should continue to work — just make sure `createEntityMesh` is bundled in the
bootstrap JS (the `_RENDERER_FILES` list in `_bootstrap/_html.py` needs updating).

### 4.8 `py/pytanga/viz/export/_bootstrap/_html.py` — `_RENDERER_FILES`

Add `renderers/axis.js` and `renderers/grid.js` to the renderer files list.

---

## 5. glTF Export Changes

### 5.1 `py/pytanga/viz/export/_gltf.py`

In `_make_primitives()`, add cases for `Axis` and `Grid`:

- **Axis**: Draw a cylinder (the axis line) + small perpendicular cylinders
  at tick intervals. No text labels (glTF has no text primitive).
- **Grid**: Draw line primitives (`lines_from_points()` style) for each grid
  line in the UV plane.

In `_get_position()`, return `(0, 0, 0)` for Axis/Grid (they are world-anchored).

### 5.2 `py/pytanga/viz/export/_gltf_primitives.py`

New helper: `lines_from_segments(segments: list[tuple[vec3, vec3]])` that builds
a `LINES` primitive from start/end point pairs. Useful for both Axis ticks and
Grid lines.

---

## 6. Adapt All Callers

### 6.1 Examples

| File | Change |
|------|--------|
| `py/examples/viz/demo_act_point.py` | No change needed (doesn't use space_extent/show_grid/show_axes) |
| `py/examples/viz/demo_animated_export.py` | Remove `space_extent`/`show_grid`/`show_axes` if used |
| `py/examples/viz/two_spheres_interact.py` | Remove `space_extent` from Visualizer() call |
| `py/examples/viz/demo_camera_config.py` | Remove `space_extent`; demonstrate new `view_2d`/`view_plane` |
| All other examples in `py/examples/viz/` | Remove `space_extent`/`show_grid`/`show_axes` params |

### 6.2 Tests

| File | Change |
|------|--------|
| `py/tests/viz/test_scene_session.py` | Remove assertions on `space_extent`/`show_grid`/`show_axes`; add tests for `View2DConfig`/`ViewPlaneConfig` serialization and `CameraConfig.to_dict()` |
| `py/tests/viz/test_scene_session.py` | Add test: `Axis` serialization produces correct JSON with start/end/intervals/label fields |
| `py/tests/viz/test_scene_session.py` | Add test: `Grid` serialization produces correct JSON with origin/dir_u/dir_v/range/interval fields |
| `py/tests/viz/test_scene_session.py` | Add test: `Axes3D` expands to three `Axis` objects with correct directions and ranges |
| `py/tests/viz/test_scene_session.py` | Add test: `Axes2D` expands to two `Axis` objects |
| `py/tests/viz/test_scene_session.py` | Add test: default axes/grid are added automatically when user hasn't provided any |
| `py/tests/viz/test_scene_session.py` | Add test: default axes/grid are NOT added when user has provided at least one Axis or Grid |
| `py/tests/viz/test_scene_session.py` | Add test: `SceneConfig.to_dict()` does NOT include `space_extent`, `show_grid`, or `show_axes` keys |
| `py/tests/viz/test_scene_session.py` | Add test: `CameraConfig.to_dict()` includes `view_2d` and `view_plane` when set |
| `py/tests/viz/test_scene_session.py` | Add test: `Visualizer()` no longer accepts `space_extent`/`show_grid`/`show_axes` kwargs |

### 6.3 Documentation

| File | Change |
|------|--------|
| `docs/py/viz/index.md` | Update overview: mention new camera modes, Axis/Grid as scene objects, remove references to `space_extent`/`show_grid`/`show_axes` |
| `docs/py/viz/` (new or existing) | Add guide doc: "Camera Configuration" — explain `View2DConfig`, `ViewPlaneConfig`, how to set 2D extents, 3D plane-based camera, and runtime `set_camera()` |
| `docs/py/viz/` (new or existing) | Add guide doc: "Axes and Grid" — explain `Axis`, `Grid`, convenience classes `Axes3D`/`Axes2D`, customizing intervals/labels/ticks, and how defaults work |
| `py/pytanga/viz/scene.py` | Update docstrings for `CameraConfig`, `SceneConfig`, new `View2DConfig`, `ViewPlaneConfig` |
| `py/pytanga/viz/_scene_objects.py` | Write full docstrings with usage examples for `Axis`, `Grid`, `Axes3D`, `Axes2D` |
| `py/pytanga/viz/visualizer.py` | Update class/`__init__` docstring to remove `space_extent`/`show_grid`/`show_axes`, document `set_camera()` |
| `py/examples/viz/` | Add new example: `demo_axes_custom.py` — shows custom axes with intervals, labels, and ticks |
| `py/examples/viz/` | Add new example: `demo_camera_2d.py` — shows `View2DConfig` with custom extent and center |
| `py/examples/viz/` | Add new example: `demo_camera_3d_plane.py` — shows `ViewPlaneConfig` with a tilted plane and custom span_u |
| `py/examples/viz/demo_camera_config.py` | Update to demonstrate `view_2d` and `view_plane` instead of (or in addition to) manual position/target |

---

## 7. Implementation Order

1. ✅ **`py/pytanga/viz/scene.py`** — Add `View2DConfig`, `ViewPlaneConfig`; extend `CameraConfig`; clean `SceneConfig`
2. ✅ **`py/pytanga/viz/_scene_objects.py`** — New file with `Axis`, `Grid`, `Axes3D`, `Axes2D`
3. ✅ **`py/pytanga/viz/serializer.py`** — Add Axis/Grid serializers
4. ✅ **`py/pytanga/viz/_types.py`** — Update `VizInputType`
5. ✅ **`py/pytanga/viz/__init__.py`** — Export new types
6. ✅ **`py/pytanga/viz/visualizer.py`** — Remove old params; handle new objects; add `set_camera()`; default axes/grid
7. ✅ **`py/pytanga/viz/_app.py`** — Remove old params
8. ✅ **`py/pytanga/viz/_scene_handle.py`** — Remove `_space_extent`; add `set_camera()`
9. ✅ **`py/pytanga/viz/_jupyter.py`** — Remove `_space_extent` contract
10. ✅ **Frontend renderers** — `axis.js`, `grid.js`, `factory.js`
11. ✅ **Frontend camera** — `view_mode.js` (rewrite `switchToCamera`), `viewer.js` (remove grid/axes)
12. ✅ **Export: bootstrap scene** — `_bootstrap/_scene.py` (remove grid/axes params)
13. ✅ **Export: HTML** — `_html.py`, `_figure_html.py`, `_animated_figure.py`
14. ✅ **Export: glTF** — `_gltf.py`, `_gltf_primitives.py` (Axis/Grid without text)
15. ✅ **Export: bootstrap HTML** — `_bootstrap/_html.py` (update `_RENDERER_FILES`)
16. ✅ **Styles** — `_styles/_overlay_styles.py` (remove `show_grid`/`show_axes` from `FigureStyle`)
17. ✅ **Examples** — All files in `py/examples/viz/`
18. ✅ **Tests** — `py/tests/viz/test_scene_session.py`
19. ✅ **Docs** — `docs/py/viz/`
