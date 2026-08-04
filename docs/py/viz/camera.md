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
)
```

| Field | Type | Description |
|-------|------|-------------|
| `position` | `(float, float, float) \| None` | Camera world position |
| `target` | `(float, float, float) \| None` | Look-at point |
| `fov` | `float \| None` | Vertical field of view in degrees |
| `near` | `float \| None` | Near clipping plane |
| `far` | `float \| None` | Far clipping plane |

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

## 2D Camera (Orthographic)

When `space_dim=2`, the viewer uses an **orthographic camera** with a
top-down view.  This is set automatically — no explicit `CameraConfig`
is needed.

```python
from pytanga.viz import Visualizer

viz = Visualizer(space_dim=2)  # orthographic top-down camera
```

**Default configuration:**

| Property | Value |
|----------|-------|
| Camera type | Orthographic |
| Position | `(0, 0, 20)` — looking straight down |
| Target | `(0, 0, 0)` |
| `fov` (from `CameraConfig`) | Ignored for orthographic cameras |

**Auto-fit** uses the 2D bounding box (x‑y extent only), so entities are
sized appropriately for the viewport.

**Explicit `CameraConfig`** still works, but `fov` is ignored for
orthographic cameras:

```python
from pytanga.viz import Visualizer, CameraConfig

viz = Visualizer(
    space_dim=2,
    camera=CameraConfig(
        position=(0, 0, 30),   # higher up
        target=(5, 5, 0),      # centered on a different point
    ),
)
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

The `Ctrl+S` shortcut captures the WebGL canvas (3D scene, grid, axes). It
does not capture DOM overlays (labels, title, annotation panel) — for
full-viewport captures including overlays, use `SceneExporter.screenshot()`
(see [Export & Capture](export.md)).

## Scene Configuration

The `Visualizer` constructor also accepts scene-wide settings:

```python
Visualizer(
    space_extent=20.0,       # larger grid and rendering extent
    show_grid=False,         # hide grid
    show_axes=False,         # hide axes
    background_color="#000000",  # black background
)
```

`space_extent` controls the size of the grid and the default rendering extent
for infinite entities (lines, planes, space box). Doubling it doubles the
grid size.