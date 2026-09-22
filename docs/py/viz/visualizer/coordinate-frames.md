# Matrices & Coordinate Frames

`pytanga.geometry` provides two small, algebra-free primitives for expressing
numeric transforms and axis conventions: `Matrix` and `CoordinateFrame`.  They
back the camera-calibration helpers and can be passed straight to the scene
graph's `set_transform()` / `apply_transform()`.

## `Matrix`

`Matrix` is a thin, typed wrapper around a square `numpy` array (3×3 or 4×4),
using the column-vector convention (`v' = M @ v`).

```python
import math

from pytanga.geometry import Direction, Matrix, Point

# Rotation about +x by 90° (Rodrigues).
r = Matrix.rotation((1.0, 0.0, 0.0), math.pi / 2)

# Composition, transpose, inverse, determinant.
r @ r.T == Matrix.identity(3)
r.inverse() @ r == Matrix.identity(3)
r.det()           # ≈ 1.0
r.is_rotation()   # True

# Apply to points/directions (homogeneous for a 4×4 matrix).
r @ Point(0.0, 1.0, 0.0)      # → Point(0.0, 0.0, 1.0)
r @ Direction(0.0, 1.0, 0.0)  # → Direction(0.0, 0.0, 1.0)

# Constructors.
Matrix.translation(1.0, 2.0, 3.0)  # 4×4 homogeneous
Matrix.scale(0.5)                  # 3×3 uniform
Matrix.from_axes(x, y, z)          # 3×3 change-of-basis (columns = axes)
Matrix.from_R_t(R, t)              # 4×4 rigid transform [R t; 0 1]
```

| Member | Description |
|--------|-------------|
| `to_matrix()` / `to_numpy()` | the raw `numpy` array |
| `T`, `inverse()`, `det()` | linear algebra |
| `is_rotation()` | orthonormal with determinant ≈ +1 |
| `@` | compose matrices, or transform a `Point`/`Direction` |
| `identity(n)` / `translation(…)` / `rotation(axis, angle)` / `scale(…)` / `from_axes(x, y, z)` / `from_R_t(R, t)` | constructors |

### `MatrixProvider`

Anything with a `to_matrix() -> np.ndarray` method satisfies the
`MatrixProvider` protocol.  `Matrix`, `CoordinateFrame`, and `Transform` all do,
so any of them can be used wherever a 4×4 matrix is expected — including
`set_transform()` / `apply_transform()`:

```python
from pytanga.geometry import MatrixProvider, OpenCVFrame
from pytanga.viz import Visualizer

assert isinstance(OpenCVFrame(), MatrixProvider)

group = viz.add_group("data")
group.set_transform(OpenCVFrame())  # remap OpenCV-frame children into the world
```

## `CoordinateFrame`

`CoordinateFrame(x, y, z)` names where a child frame's `+x`/`+y`/`+z` axes point
in the parent (right-handed) frame.  `to_matrix()` returns the 4×4
change-of-basis matrix (a proper rotation), and `handedness()` reports `+1`
(right-handed) or `-1` (left-handed).

```python
from pytanga.geometry import CoordinateFrame, Direction

# The standard frame (identity).
CoordinateFrame(
    x=Direction(1.0, 0.0, 0.0),
    y=Direction(0.0, 1.0, 0.0),
    z=Direction(0.0, 0.0, 1.0),
)
```

### `OpenCVFrame`

`OpenCVFrame()` is a ready-made frame for the OpenCV camera convention
(x right, y down, z forward).  It is a 180° rotation about `+x` relative to the
standard x-right / y-up / z-toward-viewer frame — a **proper** rotation
(determinant +1), so it keeps the world right-handed and composes with other
rotations.

```python
from pytanga.geometry import OpenCVFrame

frame = OpenCVFrame()
frame.handedness()  # 1
frame.to_matrix()   # diag([1, -1, -1, 1])
```

Use it to remap OpenCV-frame data into the right-handed world — either by
passing it to `set_transform()`, or through `CameraCalibration` (see
[Camera Calibration](camera-calibration.md)).
