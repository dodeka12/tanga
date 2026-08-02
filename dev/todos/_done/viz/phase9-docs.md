# Phase 9: Documentation

**Files:** `docs/py/viz/index.md`, `docs/py/viz/examples.md`, update `docs/py/index.md`

**Goal:** Write user-facing documentation for the visualization submodule: an overview
page with API reference, a usage guide with code examples, and a link from the main
Python documentation index.

**Prerequisites:** Phase 7 (fully integrated package)

---

## 1. `docs/py/viz/index.md` — Overview & API Reference

Focus on practical usage, not implementation details.

```markdown
# Tanga 3D Visualizer

The `pytanga.viz` submodule provides interactive 3D visualization of geometric
entities in a web browser using **Three.js** and WebGL. Users can rotate, pan,
and zoom the camera, and entities can be rendered translucently for better
overlap visualization.

## Quick Start

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer()
viz.add(Point(1, 2, 3), color="#ff4444")
viz.add(Sphere(Point(0, 0, 0), radius=2.5), wireframe=True, opacity=0.4)
viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)), opacity=0.3)
viz.run()  # Opens browser, blocks until Ctrl+C
```

## How It Works

1. A lightweight HTTP + WebSocket server starts on `localhost:8765`.
2. The browser opens and loads a Three.js scene (CDN, no install needed).
3. Entity data is serialized to JSON and pushed over WebSocket.
4. The browser creates Three.js meshes and renders them with orbit controls.

## API Reference

### `Visualizer`

```python
class Visualizer(
    port: int = 8765,
    host: str = "localhost",
    open_browser: bool = True,
    title: str = "Tanga 3D Viewer",
    background_color: str = "#1a1a2e",
)
```

**Methods:**

| Method | Description |
|--------|-------------|
| `add(obj, *, opns=True, **properties) → str \| list[str]` | Add a geometry entity or MV to the scene. |
| `update(entity_id, **properties)` | Update rendering properties of an existing entity. |
| `update_entity(entity_id, obj, *, opns=True)` | Replace the geometry of an existing entity (for animation). |
| `remove(entity_id)` | Remove an entity from the scene. |
| `clear()` | Remove all entities. |
| `animate_to(entity_id, *, position, rotation, opacity, scale, duration, easing)` | Smoothly animate an entity to a target state (browser-tweened). |
| `timeline() → Timeline` | Create a sequenced animation timeline. |
| `start()` | Start the server in a background thread (non-blocking). |
| `flush()` | Push current scene state to the browser. |
| `run()` | Start server, open browser, block until Ctrl+C. |
| `stop()` | Stop the server and clean up. |

### Default Rendering Properties

The `Visualizer` exposes property setters to configure default colors, line thickness,
plane extents, and other rendering attributes. These defaults apply to all subsequently
added entities unless overridden per-entity via `**properties` on `add()`.

```python
viz = Visualizer()

# Change default colors
viz.set_default_color("point", "#00ff00")
viz.set_default_color("plane", "#ff00ff")
viz.set_default_color("line", "#00ffff")

# Change default extents for infinite objects
viz.set_default_extent(
    line_length=30.0,       # rendered line length (default 20)
    line_thickness=0.05,    # line cylinder radius (default 0.03)
    plane_extent=15.0,      # plane quad half-extent (default 10)
)

# All subsequently added entities use the new defaults
viz.add(Line(origin=Point(0,0,0), direction=Direction(1,0,0)))  # cyan, length 30
viz.add(Plane(point=Point(0,0,3), normal=Direction(0,0,1)))     # magenta, extent 15

# Per-entity properties still override defaults
viz.add(Point(1, 2, 3), color="#ff0000")  # red, ignores the green default

# Bulk-set multiple defaults at once
viz.set_defaults(
    color_sphere="#ffaa00",
    line_length=25.0,
    plane_extent=12.0,
)
```

| Method | Description |
|--------|-------------|
| `defaults` (property) → `dict` | Returns a copy of the current defaults dict. |
| `set_defaults(**kwargs)` | Bulk-set multiple defaults. Raises `KeyError` for unknown keys. |
| `set_default_color(kind, color)` | Set the default color for one entity kind. |
| `set_default_extent(*, line_length, line_thickness, plane_extent, space_extent)` | Set default extent values for infinite entities. |

Valid `kind` values for `set_default_color`: `"point"`, `"direction"`, `"homogeneous_point"`,
`"point_pair"`, `"line"`, `"plane"`, `"circle"`, `"sphere"`, `"space"`.

Defaults dict keys (for `set_defaults()`): `color_point`, `color_direction`,
`color_homogeneous_point`, `color_point_pair`, `color_line`, `color_plane`,
`color_circle`, `color_sphere`, `color_space`, `line_length`, `line_thickness`,
`plane_extent`, `space_extent_render`.

### `Timeline`

```python
timeline = viz.timeline()
timeline.wait(0.5)                        # Pause 0.5 seconds
timeline.animate_to(id, position=(3,0,0), duration=1.0)  # Move entity
timeline.wait(0.2)                        # Pause 0.2 seconds
timeline.animate_to(id2, opacity=0.3, duration=0.5)     # Fade entity
timeline.animate_to(id3, rotation=(0, math.pi, 0), duration=2.0, parallel=True)  # Concurrent
timeline.play()                           # Send to browser
```

### Entity Rendering Properties

Properties passed as `**kwargs` to `add()` or `update()`:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `color` | `str \| (float, float, float) \| (float, float, float, float)` | varies by kind | Hex string or RGB/RGBA float tuple. Normalized to hex for the browser. |
| `opacity` | `float` | varies | 0.0 (fully transparent) to 1.0 (opaque) |
| `size` | `float` | `0.08` | Point radius |
| `length` | `float` | `20.0` | Rendered length of lines/directions |
| `thickness` | `float` | `0.03` | Thickness of line cylinders |
| `extent` | `float` | `10.0` | Half-extent of plane quads and space box |
| `wireframe` | `bool` | `True` (spheres) | Show wireframe overlay |
| `tubeRadius` | `float` | `0.03` | Thickness of circle torus tube |
| `label` | `str \| None` | `None` | Text annotation displayed next to the entity via CSS2DRenderer |
| `labelOffsetY` | `float` | `0.3` | Vertical offset of the label above the entity center |
| `labelFontSize` | `float` | `14` | CSS font-size in pixels |
| `labelColor` | `str` | `"#ffffff"` | Text color (CSS color, e.g. `"#ff0"` or `"white"`) |
| `labelBackground` | `str` | `"rgba(0,0,0,0.6)"` | Background CSS value |

Default colors by entity kind:

| Entity | Default Color |
|--------|---------------|
| Point | `#ff4444` (red) |
| Direction | `#ffffff` (white) |
| HPoint | `#ff8844` (orange) |
| PointPair | `#44ff44` (green) |
| Line | `#44ff44` (green) |
| Plane | `#4488ff` (blue) |
| Circle | `#ff44ff` (magenta) |
| Sphere | `#ffaa00` (amber) |
| Space | `#888888` (grey) |

### Camera Controls

The Three.js viewer uses standard orbit controls:

| Action | Input |
|--------|-------|
| Rotate | Left mouse drag |
| Pan | Middle mouse drag / Shift + left drag |
| Zoom | Scroll wheel / Right mouse drag |
| Reset view | (Press 'R' — Phase 7+) |
```

---

## 2. `docs/py/viz/examples.md` — Usage Examples

```markdown
# Visualization Examples

## Example 1: Static Scene with All Entity Types

```python
from pytanga.viz import Visualizer
from pytanga.geometry import (
    Point, Direction, Line, Plane, Circle, Sphere, Space, PointPair
)

viz = Visualizer()

# Points
viz.add(Point(2, 0, 0), color="#ff4444")
viz.add(Point(0, 2, 0), color="#44ff44", size=0.12)
viz.add(Point(0, 0, 2), color="#4444ff", size=0.15)

# Direction arrow from origin
viz.add(Direction(1, 1, 0), color="#ffffff", length=3.0)

# Line through origin along X axis
viz.add(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
        color="#44ff44", thickness=0.04)

# Translucent plane at z=3
viz.add(Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
        color="#4488ff", opacity=0.25)

# Circle in XY plane
viz.add(Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=3),
        color="#ff44ff")

# Sphere at origin
viz.add(Sphere(Point(0, 0, 0), radius=2.5),
        color="#ffaa00", wireframe=True, opacity=0.3)

# Point pair
viz.add(PointPair(point_a=Point(-1, 1, 0), point_b=Point(1, 1, 0)),
        color="#44ff44")

# Space bounding box
viz.add(Space(), opacity=0.08)

viz.run()
```

## Example 2: Labeled Entities

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Sphere, Plane, Direction

viz = Visualizer()

# Labels attach to entities automatically
viz.add(Point(1, 2, 3), color="#ff4444", label="P₁", size=0.15)
viz.add(Point(5, 0, 2), color="#44ff44", label="P₂", size=0.15)
viz.add(
    Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1)),
    opacity=0.3, label="π (z=3)"
)
viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    wireframe=True, opacity=0.4, label="S₁"
)

# Customize label appearance
viz.add(
    Point(0, 0, 0), color="#ffff00", size=0.2,
    label="Origin",
    labelOffsetY=0.5,
    labelFontSize=18,
    labelColor="#ffff00",
    labelBackground="rgba(0,0,0,0.8)",
)

viz.run()
```

Labels are rendered via Three.js CSS2DRenderer — crisp HTML text that follows
the entity in 3D space but always faces the camera. Set `label=None` to hide
a label, or use `viz.update(entity_id, label="new text")` to change it.

## Example 3: Visualizing Multivectors from PGA3

```python
from pytanga.algebra import Algebra
from pytanga.viz import Visualizer
from pytanga.geometry import Direction, Point

pga = Algebra.from_name("PGA3")
viz = Visualizer()

# add() accepts both Entity objects and MV (multivector) objects.
# MVs are analyzed internally via pytanga.geometry.analyze().
# The 'opns' flag controls OPNS (True) vs IPNS (False) interpretation.

# Plane at z=3, normal pointing up (OPNS)
viz.add(pga.plane(0, 0, 1, 3), opacity=0.3)

# Point at (5, 0, 0) in OPNS form (grade-3 trivector in PGA3)
viz.add(pga.point(5, 0, 0), color="#ff4444", size=0.12, opns=True)

# Same point in IPNS form (grade-1 vector)
mv_ipns = pga.point(5, 0, 0)
viz.add(mv_ipns, color="#44ff44", size=0.12, opns=False)

# Line through origin along X axis (OPNS)
viz.add(pga.line_from_direction(Direction(1, 0, 0), Point(0, 0, 0)),
        color="#44ff44")

viz.run()
```

## Example 4: Animated Rotating Point

```python
import time, math
from pytanga.viz import Visualizer
from pytanga.geometry import Point

viz = Visualizer()
viz.start()  # Non-blocking: server runs in background

point_id = viz.add(Point(3, 0, 0), color="#ff4444", size=0.12)
viz.flush()

# Animate: orbit the point around the Z-axis
for frame in range(600):
    angle = frame * 0.05
    x = 3 * math.cos(angle)
    y = 3 * math.sin(angle)
    viz.update_entity(point_id, Point(x, y, 0))
    viz.flush()
    time.sleep(1/60)

viz.stop()
```

## Example 5: Keyframe Animation with Timeline

```python
viz = Visualizer()

# Change default colors — accepts hex strings or RGB/RGBA tuples
viz.set_default_color("point", (0.0, 1.0, 0.0))   # RGB tuple → green
viz.set_default_color("plane", "#ff00ff")          # hex string → magenta
viz.set_default_color("line", (0.0, 1.0, 1.0))    # RGB tuple → cyan

# Change default extents for infinite objects
viz.set_default_extent(
    line_length=30.0,       # rendered line length (default 20)
    line_thickness=0.05,    # line cylinder radius (default 0.03)
    plane_extent=15.0,      # plane quad half-extent (default 10)
)

# All subsequently added entities use the new defaults
viz.add(Line(origin=Point(0,0,0), direction=Direction(1,0,0)))  # cyan, length 30
viz.add(Plane(point=Point(0,0,3), normal=Direction(0,0,1)))     # magenta, extent 15

# Per-entity properties still override defaults
viz.add(Point(1, 2, 3), color=(1.0, 0.0, 0.0))  # RGB tuple → red, ignores the green default

# Bulk-set multiple defaults at once
viz.set_defaults(
    color_sphere="#ffaa00",
    line_length=25.0,
    plane_extent=12.0,
)
```

## Example 6: Fade-in Geometric Construction

```python
from pytanga.viz import Visualizer
from pytanga.geometry import Point, Line, Plane, Sphere, Direction

viz = Visualizer()

# Add all entities fully transparent
plane_id = viz.add(
    Plane(point=Point(0, 0, 2), normal=Direction(0, 0, 1)),
    opacity=0.0, color="#4488ff"
)
line_id = viz.add(
    Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)),
    opacity=0.0, color="#44ff44"
)
sphere_id = viz.add(
    Sphere(Point(0, 0, 0), radius=2.5),
    opacity=0.0, wireframe=True, color="#ffaa00"
)
point_id = viz.add(
    Point(1, 0, 0),
    opacity=0.0, color="#ff4444", size=0.15
)

viz.run()  # Blocks — user sees entities fade in one by one
```

(For the fade-in example to work, the animation calls must happen before `run()`,
or use `start()` + timeline.)

## Dependencies

The visualizer requires `aiohttp` on the Python side:

```bash
uv add aiohttp
```

The browser requires no installation — Three.js loads from a CDN automatically.
```

---

## 3. Update `docs/py/index.md`

Add a link to the viz documentation in the Python docs index.

Locate the section listing submodule documentation pages and add:

```markdown
- [3D Visualizer](viz/index.md) — Interactive Three.js visualization of geometric entities
```

---

### 4.1 Documentation Files

- [ ] **D1:** Create `docs/py/viz/` directory
- [ ] **D2:** Create `docs/py/viz/index.md` — API reference: `Visualizer`, `CameraConfig`, `SceneConfig`, `Timeline`, `ObjVizProps`, rendering properties
- [ ] **D3:** Include default color table for all entity and operator kinds
- [ ] **D4:** Include camera controls reference (orbit, pan, zoom)
- [ ] **D5:** Document `Visualizer._defaults` and `set_default_*()` methods
- [ ] **D6:** Document MV input pipeline with `opns` flag
- [ ] **D7:** Document Jupyter notebook workflow (`start()` / `flush()` / `stop()`)

### 4.2 Example Documentation

- [ ] **D8:** Create `docs/py/viz/examples.md`
- [ ] **D9:** Example 1: Static scene with all entity types (Point, Line, Plane, Circle, Sphere, etc.)
- [ ] **D10:** Example 2: Labeled entities with custom styling
- [ ] **D11:** Example 3: Visualizing multivectors from PGA3/N3
- [ ] **D12:** Example 4: Animated rotating point (frame streaming)
- [ ] **D13:** Example 5: Keyframe animation with Timeline
- [ ] **D14:** Example 6: Fade-in geometric construction
- [ ] **D15:** All code examples are syntactically correct and runnable

### 4.3 Integration with Main Docs

- [ ] **D16:** Update `docs/py/index.md` — add link to `viz/index.md`
- [ ] **D17:** Verify documentation format matches existing docs style (`docs/py/geometry/`, `docs/py/algebra/`)
- [ ] **D18:** Verify all inline code snippets use correct API (matching current implementation)

## 5. Verification Checklist

- [ ] `docs/py/viz/index.md` covers all public API (Visualizer, Timeline, properties).
- [ ] `docs/py/viz/index.md` includes default color table.
- [ ] `docs/py/viz/index.md` includes camera controls reference.
- [ ] `docs/py/viz/examples.md` has at least 5 distinct examples.
- [ ] All code examples are syntactically correct Python.
- [ ] `docs/py/index.md` links to `viz/index.md`.
- [ ] Documentation uses the same style and formatting as existing docs (`docs/py/geometry/`).