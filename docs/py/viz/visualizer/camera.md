# Camera & Controls

## Camera Config Types

Camera configuration is split into a small typed hierarchy:

- `CameraConfig` — the base type carrying a `type` discriminator plus the
  fields shared by both camera families (`position`, `target`, `up`, `near`,
  `far`).
- `CameraConfig3d` — a perspective camera (adds `fov`).
- `CameraConfig2d` — an orthographic top-down camera (adds the visible world
  rectangle and a scaling policy).

You normally construct the concrete subclass directly, or use one of the
builder functions below.

```python
from pytanga.viz import CameraConfig3d

# Perspective camera with explicit placement
CameraConfig3d(
    position=(10, 6, 12),   # (x, y, z) world position
    target=(0, 0, 0),       # look-at point
    up=(0, 1, 0),           # camera up vector (also the orbit rotation axis)
    fov=50.0,               # vertical field of view in degrees
    near=None,              # near clipping plane
    far=None,               # far clipping plane
)
```

## Camera Modes

### Auto-Fit (Default)

With `camera=None` (the default), the camera position, target, FOV, near, and
far are all auto-computed from the bounding box of all entities in the scene.

```python
viz = Visualizer()  # auto-fit
```

### Explicit 3D Perspective

```python
from pytanga.viz import CameraConfig3d, Visualizer

viz = Visualizer(camera=CameraConfig3d(
    position=(10, 6, 12),
    target=(0, 0, 0),
    fov=45,
    near=0.1,
    far=200,
))
```

Partial cameras are also supported — any field left `None` is auto-computed:

```python
CameraConfig3d(position=(10, 3, 0))
CameraConfig3d(position=(0, 15, 0), fov=30)
```

## 2D Camera via View2DConfig

`View2DConfig` is a pure **input** spec for an orthographic view. It defines
the visible world rectangle with min/max bounds, optional borders, and a
scaling policy. Pass it directly to `Visualizer(camera=...)` — the viewer
deduces `space_dim=2` from it automatically. (You can also convert it
explicitly with `get_camera_view2d()` or the dispatching `get_camera()`.)

```python
from pytanga.viz import View2DConfig, Visualizer

viz = Visualizer(
    camera=View2DConfig(
        xmin=-4.0,              # minimum visible world X
        xmax=4.0,               # maximum visible world X
        ymin=-3.0,              # minimum visible world Y
        ymax=3.0,               # maximum visible world Y
    ),
)
```

| Field | Type | Description |
|-------|------|-------------|
| `xmin` / `xmax` | `float` | Visible world X range |
| `ymin` / `ymax` | `float` | Visible world Y range |
| `border_world` | `float` | World-unit margin added on all four sides (applied in Python) |
| `border_px` | `float` | Pixel margin added on all four sides (applied by the frontend) |
| `uniform` | `bool` | `True` = letterbox (uniform scale), `False` = stretch-to-fill |

### Scaling Policy (`uniform`)

`uniform=True` (default) preserves the aspect ratio via letterboxing: a single
world-units-per-pixel scale is used so geometry is never distorted, and the
requested rectangle is fully contained. The frontend computes the final
frustum from the live browser viewport so the result is independent of the
window size.

`uniform=False` stretches the rectangle's width and height to fill the
viewport, scaling X and Y independently. A long, thin plot therefore fills the
whole window (axes intentionally non-uniform). This is the right choice for
graph-style plots where the data bounds may be very wide or tall.

`border_world` and `border_px` provide margins for clean graph rendering:
`border_world` is applied deterministically in Python; `border_px` is applied
by the frontend because converting pixels to world units requires the live
viewport size. Both apply in **both** scaling modes: letterboxing shrinks the
effective content area before the fit, and stretch-to-fill maps the rectangle
onto the inset content area (viewport minus the border).

## 3D Camera via View3dConfig

`View3dConfig` is a pure **input** spec that describes a projective 3D camera
using a virtual plane.  The plane defines the camera's **initial framing**:

- the optical axis is the plane normal `n̂`;
- the camera is placed at `center + n̂ · distance`, where `distance` is derived
  from `fov` and the plane extents so the plane is fully framed;
- the `up` vector (default `(0, 1, 0)`) is the camera's up direction and is
  also used as the orbit rotation axis by the interactive viewer, independent
  of the plane orientation.

Convert it with `get_camera_view3d()` (or the dispatching `get_camera()`). The
result is a plain projective `CameraConfig3d` (with `position` / `target` /
`up` / `fov` populated), so it is **not** a locked 2D-on-plane view — the
frontend renders it as a free 3D camera with standard orbit controls.

```python
from pytanga.viz import View3dConfig, Visualizer, get_camera_view3d

viz = Visualizer(
    camera=get_camera_view3d(View3dConfig(
        point=(0.0, 0.0, 0.0),    # point on the virtual plane
        normal=(0.4, 0.6, 1.0),   # camera optical axis
        extent_u=6.0,             # full horizontal extent
        extent_v=5.0,             # full vertical extent
        up=(0.0, 1.0, 0.0),       # camera up / orbit rotation axis
        fov=50.0,
    )),
)
```

| Field | Type | Description |
|-------|------|-------------|
| `point` | `(float, float, float)` | Point on the virtual plane |
| `normal` | `(float, float, float)` | Camera optical axis (plane normal) |
| `extent_u` | `float` | Full horizontal extent |
| `extent_v` | `float` | Full vertical extent |
| `center` | `(float, float, float) \| None` | Point mapped to viewport centre (defaults to `point`) |
| `up` | `(float, float, float)` | Camera up vector / orbit rotation axis (defaults to `(0, 1, 0)`) |
| `fov` | `float` | Vertical field of view in degrees |

The `up` vector controls the camera roll and, in the interactive viewer, the
orbit rotation axis. It defaults to `(0, 1, 0)` so orbit behaviour matches the
no-camera case regardless of the plane orientation.

The produced `CameraConfig3d` is a fully explicit projective camera; once it is
in place, the user can freely rotate (left-drag), pan (right/middle-drag), and
zoom (scroll wheel) about the framed plane.

## Builder Functions

| Function | Input | Returns |
|----------|-------|---------|
| `get_camera_view2d(config)` | `View2DConfig` | `CameraConfig2d` |
| `get_camera_view3d(config)` | `View3dConfig` | `CameraConfig3d` |
| `get_camera(view_config)` | `View2DConfig \| View3dConfig` | `CameraConfig` (dispatches) |

`get_camera()` is a convenience dispatcher over the two specific builders.

## Runtime Camera Updates

`set_camera()` updates the camera for a scene at runtime without restarting
the viewer:

```python
viz.set_camera(get_camera_view2d(View2DConfig(xmin=0, xmax=8, ymin=0, ymax=6)))
viz.scene("details").set_camera(CameraConfig3d(fov=30))
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
[Video & Image Export](../export/video-image.md)).

## Scene Configuration

The `Visualizer` constructor accepts scene-wide settings:

```python
Visualizer(
    space_dim=3,                 # 2 or 3
    background_color="#1a1a2e",  # background color
)
```

Grid and axes are explicit scene objects (see [Axes & Grid](../scene-objects/axes-grid.md)).
Whether a default axes/grid is inserted automatically is controlled by the
`add_default_axes` / `add_default_grid` constructor flags (both `True` by
default).
