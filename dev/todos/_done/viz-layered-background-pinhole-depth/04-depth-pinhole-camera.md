# Phase 4 — `DepthImage` pinhole camera mode

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("New entity kind", "Frustum",
> `CameraCalibration`/`PinholeCamera` notes) and `docs/py/viz/visualizer/camera-calibration.md`.
> This phase extends the `depth_image` mesh payload + shader.

## Goal

Add a pinhole mode to `DepthImage` so a calibrated depth map is rendered as
camera-frame vertices (`X = (u−cx)/fx·z`, `Y = (v−cy)/fy·z`, `Z = z`), placed in
the world via the entity transform or an auto-applied `CameraCalibration` pose.
The camera is specified the **same way** as the calibrated background image:
`CameraCalibration` (canonical) or `PinholeCamera`.

## Files

- Edit: `py/pytanga/viz/_styles/_entity_styles.py` (`DepthImageStyle`)
- Edit: `py/pytanga/viz/_styles/__init__.py` (defaults)
- Edit: `py/pytanga/viz/depth_image.py` (intrinsics resolution + `compute_pinhole_positions`)
- Edit: `py/pytanga/viz/templates/renderers/depth-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/depth-image.js`
- Edit: `js/tanga-viewer.js` (regenerated)
- Edit: `py/tests/viz/test_depth_image.py` (+ `test_depth_image_pinhole.py`)

## Steps

- [x] **4.1 — `DepthImageStyle` fields**
  - Add `camera: Any | None = None` (accepts `CameraCalibration | PinholeCamera`),
    `depth_kind: str | None = None` (validate `"z"|"range"`), and
    `apply_pose: bool | None = None` to `DepthImageStyle`; serialize each in
    `to_dict()` (resolve `camera` via a duck-typed helper that reads `K` or
    `fx/fy/cx/cy`, so `_styles` stays free of a `camera.py` import).
  - Register defaults in `_styles/__init__.py` `"DepthImage"`:
    `camera=None`, `depth_kind="z"`, `apply_pose=True`.

- [x] **4.2 — Intrinsics + payload in `depth_image.py`**
  - Add a helper resolving `(fx, fy, cx, cy)` from a `CameraCalibration` (`K`) or
    `PinholeCamera` (fields), plus a `camera_to_world` 16-float list when
    `apply_pose` and the camera is a `CameraCalibration` (from
    `calib.camera_to_world()`).
  - In `_serialize_mesh` (or `_build`), when `style["camera"]` is set, emit
    `mesh.camera = {fx, fy, cx, cy, depth_kind}` and, when applicable,
    `mesh.camera_to_world` (list of 16 floats).  `world_scale` stays in the
    payload but is ignored by the pinhole path.

- [x] **4.3 — CPU reference `compute_pinhole_positions`**
  - Add a pure function in `depth_image.py`:
    `compute_pinhole_positions(depth, fx, fy, cx, cy, *, depth_kind="z",
    depth_scale=1.0, depth_offset=0.0, mesh_scale=1.0, max_mesh_size=None)` →
    `(positions: np.ndarray, u: np.ndarray, v: np.ndarray)` in camera frame,
    implementing the exact vertex math (and documenting it).  This is the
    reference used by the unit test and mirrors the frontend.

- [x] **4.4 — Frontend vertex shader (`depth-shader.js`)**
  - Extend `buildDepthVertex` with a pinhole branch gated by `u_depth_kind`
    (0 = orthographic as today, 1 = "z", 2 = "range"): compute `z` from the
    depth texture as today, then `X/Y` from `u_fx/u_fy/u_cx/u_cy` and the
    full-resolution pixel `(u, v) = uv * frame_size`.
  - Compute the surface normal by finite differences of the position function
    (analytic partials: `dP/du`, `dP/dv` from `z` and the intrinsics; fall back
    to the existing `uWorldStep`-based normal in orthographic mode).
  - Apply an optional `u_camera_to_world` mat4 (from `mesh.camera_to_world`)
    before `modelMatrix` so `apply_pose` is baked for the supplied calibration.

- [x] **4.5 — Frontend renderer (`depth-image.js`)**
  - In `buildDepthUniforms`, add `u_depth_kind`, `u_fx/u_fy/u_cx/u_cy`,
    `u_frame_size`, and `u_camera_to_world` (mat4, identity when absent),
    sourced from `ent.mesh.camera` / `ent.frame`.
  - Keep `applyDepthImageUniforms` / segmentation selection / lighting untouched
    (they only touch uniforms).

- [x] **4.6 — Tests**
  - Serialization: with `DepthImageStyle(camera=..., depth_kind="z")`, the mesh
    payload carries `fx/fy/cx/cy` and `depth_kind`; with a `CameraCalibration`,
    it also carries `camera_to_world` (16 floats) when `apply_pose=True`.
  - CPU reference: for a synthetic constant-depth plane `Z = 2`, the positions
    equal `((u−cx)/fx·2, (v−cy)/fy·2, 2)`.
  - `depth_kind` validation (`"z"`/`"range"` only); `range` → `z` conversion.

## Validation

```
uv run pytest py/tests/viz/test_depth_image.py py/tests/viz/test_depth_image_pinhole.py -q
uv run ruff check py/pytanga/viz/depth_image.py py/pytanga/viz/_styles/_entity_styles.py
node --test js/dev/tests/depth-shader.test.mjs
uv run python tools/build-viewer-js.py
```

## Notes

- Distortion is out of scope (images are rectified).
- The `depth_kind`/intrinsics math in `compute_pinhole_positions` is the
  canonical reference; the GLSL must match it, and the unit test pins the
  `Z = 2` plane case.
- Reuse `CameraCalibration`/`PinholeCamera` exactly as the calibrated background
  does (`calib.to_pinhole_camera()` → `CameraView.camera`); do **not** add a new
  `PinholeIntrinsics` type.
