# Camera & Controls

## CameraConfig

All fields are optional. When a field is `None`, the browser computes it
automatically from the scene's entity bounding box.

```python
from pytanga.viz import CameraConfig

CameraConfig(
    position=None,           # (x, y, z) world position
    target=None,             # (x, y, z) look-at point
    fov=None,                # vertical field of view in degrees
    near=None,               # near clipping plane
    far=None,                # far clipping plane
    view_2d=None,            # View2DConfig for orthographic views
    view_plane=None,         # ViewPlaneConfig for plane-based views
)
```

| Field | Type | Description |
|-------|------|-------------|
| `position` | `(float, float, float) \| None` | Camera world position |
| `target` | `(float, float, float) \| None` | Look-at point |
| `fov` | `float \| None` | Vertical field of view in degrees |
| `near` | `float \| None` | Near clipping plane |
| `far` | `float \| None` | Far clipping plane |
| `view_2d` | `View2DConfig \| None` | Orthographic view defined by a rectangle |
| `view_plane` | `ViewPlaneConfig \| None` | Perspective view defined by a virtual plane |

## Camera Modes

### Auto-Fit (Default)

With `camera=None` (the default), the camera position, target, FOV, near, and
far are all auto-computed from the bounding box of all entities in the scene.

```python
viz = Visualizer()  # auto-fit
```

### Full Explicit

All fields are specified — nothing is auto-computed:

```python
viz = Visualizer(camera=CameraConfig(
    position=(10, 6, 12),
    target=(0, 0, 0),
    fov=45,
    near=0.1,
    far=200,
))
```

### Partial Explicit

Specify only some fields — the rest are auto-computed:

```python
# Explicit position and target, auto-computed FOV
viz = Visualizer(camera=CameraConfig(position=(10, 3, 0)))

# Top-down view with narrow FOV
viz = Visualizer(camera=CameraConfig(position=(0, 15, 0), fov=30))
```

## 2D Camera via View2DConfig

`View2DConfig` defines an orthographic view from a rectangle centred at
`center`.  The larger extent is fit to the viewport aspect ratio.

```python
from pytanga.viz import CameraConfig, View2DConfig, Visualizer

viz = Visualizer(
    space_dim=2,
    camera=CameraConfig(
        view_2d=View2DConfig(
            extent_x=4.0,          # full width
            extent_y=3.0,          # full height
            center=(1.0, 2.0),     # viewport centre
        )
    ),
)
```

| Field | Type | Description |
|-------|------|-------------|
| `extent_x` | `float` | Full width of the view rectangle |
| `extent_y` | `float` | Full height of the view rectangle |
| `center` | `(float, float)` | Point appearing at the viewport centre |

## 3D Camera via ViewPlaneConfig

`ViewPlaneConfig` places the perspective camera along a plane normal at a
distance computed from `fov` and the plane extents.  The optical axis is
the normal; `center` maps to the viewport centre.

```python
from pytanga.viz import CameraConfig, ViewPlaneConfig, Visualizer

viz = Visualizer(
    camera=CameraConfig(
        view_plane=ViewPlaneConfig(
            point=(0.0, 0.0, 0.0),    # point on the plane
            normal=(0.4, 0.6, 1.0),   # camera optical axis
            extent_u=6.0,             # full horizontal extent
            extent_v=5.0,             # full vertical extent
            span_u=(1.0, 0.0, -0.4),  # optional horizontal direction
            fov=50.0,
        )
    ),
)
```

| Field | Type | Description |
|-------|------|-------------|
| `point` | `(float, float, float)` | Point on the virtual plane |
| `normal` | `(float, float, float)` | Camera optical axis (plane normal) |
| `extent_u` | `float` | Full horizontal extent |
| `extent_v` | `float` | Full vertical extent |
| `center` | `(float, float, float) \| None` | Point mapped to viewport centre (defaults to `point`) |
| `span_u` | `(float, float, float) \| None` | Optional horizontal direction |
| `fov` | `float` | Vertical field of view in degrees |

When `span_u` is `None`, a horizontal direction is auto-computed.  The
vertical direction is always `cross(normal, span_u)`.

## Runtime Camera Updates

`set_camera()` updates the camera for a scene at runtime without restarting
the viewer:

```python
viz.set_camera(CameraConfig(view_2d=View2DConfig(8.0, 6.0)))
viz.scene("details").set_camera(CameraConfig(fov=30))
```

## Orbit Controls

The Three.js viewer uses camera‑mode‑aware controls:

### 3D Mode (`space_dim=3`, default)

| Action | Input |
|--------|-------|
| Rotate | Left mouse drag |
| Pan | Middle mouse drag / Shift + left drag |
| Zoom | Scroll wheel / Right mouse drag |

### 2D Mode (`space_dim=2`)

| Action | Input |
|--------|-------|
| Pan | Left mouse drag *or* right mouse drag |
| Zoom | Scroll wheel |
| Rotate | Disabled (orbit rotation locked) |

Orbit controls remain active during animation playback — you can pan and
zoom while entities move.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `Cmd+S` | Download a PNG snapshot of the current viewport |
| `r` | Toggle camera auto-rotation (OrbitControls `autoRotate`) |

The `Ctrl+S` shortcut captures the WebGL canvas (3D scene). It does not
capture DOM overlays (labels, title, annotation panel) — for full-viewport
captures including overlays, use `SceneExporter.screenshot()` (see
[Export & Capture](export.md)).

## Scene Configuration

The `Visualizer` constructor accepts scene-wide settings:

```python
Visualizer(
    space_dim=3,                 # 2 or 3
    background_color="#1a1a2e",  # background color
)
```

Grid and axes are no longer toggled via boolean flags — they are explicit
scene objects.  See [Axes & Grid](axes-grid.md).