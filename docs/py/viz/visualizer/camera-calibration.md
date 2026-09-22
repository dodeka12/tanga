# Camera Calibration

`CameraCalibration` bundles a pinhole camera's **intrinsics** and **extrinsics**
with a coordinate-frame convention and a unit scale, and turns them into a
`PinholeCamera` placed in the standard right-handed world.

```python
from pytanga.geometry import Matrix, OpenCVFrame
from pytanga.viz import CameraCalibration

calib = CameraCalibration(
    K=Matrix([[1075.65, 0.0, 224.07],
              [0.0, 1073.90, 167.72],
              [0.0, 0.0, 1.0]]),
    R=Matrix.identity(3),  # world → camera
    t=(0.0, 0.0, 0.0),     # world → camera
    image_size=(400, 400),
    frame=OpenCVFrame(),   # the data's axis convention
    units=0.001,           # millimetres → metres
)

cam = calib.to_pinhole_camera()
```

| Field | Type | Description |
|-------|------|-------------|
| `K` | `Matrix` (3×3) | intrinsic matrix (`fx`, `fy`, `cx`, `cy`) in pixels |
| `R` | `Matrix` (3×3) | world→camera rotation, expressed in `frame` |
| `t` | 3-vector | world→camera translation, expressed in `frame` |
| `image_size` | `(width, height)` | image resolution in pixels |
| `frame` | `CoordinateFrame` | axis convention the data uses (default `OpenCVFrame()`) |
| `units` | `float` | scale applied to `t` (e.g. `0.001` for mm → m) |

## Methods

- `to_pinhole_camera(*, near=None, far=None, fit="fit")` → `PinholeCamera` —
  converts `R`/`t` from `frame` into the standard right-handed frame, applies
  `units` to `t`, and builds the camera.
- `world_to_camera()` → `Matrix` — the 4×4 world→camera matrix `[R t; 0 1]`
  (standard frame, metres).
- `camera_to_world()` → `Matrix` — the inverse: the 4×4 camera→world matrix.
- `camera_center()` → `(x, y, z)` — the camera's world position (the
  translation of `camera_to_world()`).

## Typical use case: OpenCV calibration + image / 3D overlay

A very common pipeline reads a real camera's calibration (intrinsics `K` and
world→camera `R`/`t`, e.g. from OpenCV or a dataset such as BOP) and overlays
3D geometry pixel-accurately onto the camera image:

1. Bundle the calibration into a `CameraCalibration` — pick the matching
   `frame` (e.g. `OpenCVFrame()`) and a `units` scale.
2. `calib.to_pinhole_camera()` → the `PinholeCamera`.
3. Map the object's model→camera pose into the same right-handed world by
   composing `calib.camera_to_world()` with the pose as a
   `Matrix.from_R_t(R, t)` — see below.
4. Show the image as the camera's `background_image` in a `CameraView`, and add
   the object (and a `Frustum`) to the scene.

```python
import numpy as np

from pytanga.geometry import Frustum, Matrix, OpenCVFrame
from pytanga.viz import CameraCalibration, CameraView, ImageData, SceneView, Visualizer

calib = CameraCalibration(K, R, t, image_size=(w, h), frame=OpenCVFrame(), units=1e-3)
cam = calib.to_pinhole_camera()

# Object pose (model→camera, OpenCV/mm) → model→world (standard, m).
T = calib.world_to_camera().inverse() @ Matrix.from_R_t(
    R_m2c, np.asarray(t_m2c, dtype=float) * calib.units
)
# corners_model is a 4×N matrix of model-space points [x, y, z, 1]ᵀ.
corners = (T @ corners_model)[:3]  # 3×N, Cartesian metres

viz = Visualizer()
scene = viz.scene("world")
scene.new(Frustum.from_camera(cam, near=0.05, far=0.7), color="#ffcc44")
# … add the object at corners …

left = SceneView(
    "world",
    camera_view=CameraView(
        cam,
        navigation="2d",
        background_image=ImageData("cam", data=image_rgb),
    ),
)
viz.show(layout=left)
```

A complete, runnable version — bundling one real T-LESS image with its BOP
calibration and ground-truth pose — is
[`pinhole_calibrated.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/camera/pinhole_calibrated.py)
(also in the [Examples → Visualization](../../examples/viz/camera/pinhole_calibrated.md)
gallery).
