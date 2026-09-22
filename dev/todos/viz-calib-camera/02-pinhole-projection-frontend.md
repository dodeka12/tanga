# Phase 2 — Frontend: off-center pinhole projection

## Goal

When `CameraConfig3d` carries `intrinsics`, render with an off-center
perspective projection so a calibrated principal point `(cx, cy)` is honored.
Ship the frustum math as a pure JS module with a Node test, wire it into
`switchToCamera`, and guard the resize path so `updateProjectionMatrix()` never
overwrites it. Without `intrinsics` the existing symmetric `fov` path is
unchanged.

## Files

- New: `py/pytanga/viz/templates/pinhole-projection.js`
- New: `py/tests/viz/test_pinhole_math.py` (Node harness, mirror `test_camera_fit_math.py`)
- Edit: `py/pytanga/viz/templates/view_mode.js`

## Steps

- [x] **2.1 — `pinhole-projection.js`**
  - Export `pinholeFrustum(fx, fy, cx, cy, width, height, near, far)` →
    `{ left, right, top, bottom, near, far }` with
    `left=-cx*near/fx`, `right=(width-cx)*near/fx`,
    `top=cy*near/fy`, `bottom=-(height-cy)*near/fy`.
  - Keep it pure (no `three`/DOM) so Node can import it.

- [x] **2.2 — Node math test**
  - `test_pinhole_math.py`: run the same Node harness used by
    `test_camera_fit_math.py`. Project a known camera-space point at `Z=near`
    through a `Matrix4.makePerspective(left,right,top,bottom,near,far)` (in the
    harness) and assert its NDC maps back to the expected pixel `(u, v)` via
    `u = fx*X/Z + cx`, `v = fy*Y/Z + cy`. This pins the sign convention.

- [x] **2.3 — apply projection in `switchToCamera` (3D branch)**
  - When `cc.intrinsics` is present, after setting `position/target/up`, compute
    the frustum via `pinholeFrustum(...)` and set `camera.projectionMatrix` with
    `new THREE.Matrix4().makePerspective(l, r, t, b, near, far)` plus
    `camera.projectionMatrixInverse = camera.projectionMatrix.clone().invert()`.
  - Store `camera.userData._pinhole = {fx,fy,cx,cy,width,height,near,far}`.
  - When absent, keep the current `cam.fov = fov; cam.aspect = aspect; cam.updateProjectionMatrix()` path.

- [x] **2.4 — resize guard**
  - In `handleResize`, if `camera.userData._pinhole`, recompute the off-center
    projection from `_pinhole` (re-using `pinholeFrustum`) instead of calling
    `camera.updateProjectionMatrix()`; still set `camera.aspect`.

- [x] **2.5 — bundle**
  - `uv run python tools/build-viewer-js.py --check`.  `pinhole-projection.js`
    and `view_mode.js` are live-viewer-only (export keeps the symmetric `fov`
    path per the non-goal), so the committed bundle is unchanged and stays in
    sync.

## Validation

`uv run pytest py/tests/viz/test_pinhole_math.py -q && node --check py/pytanga/viz/templates/pinhole-projection.js && uv run python tools/build-viewer-js.py --check`

## Notes

- `OrbitControls` only mutates the view matrix, never the projection, so an
  off-center projection still orbits/pan/zooms freely (use case 1).
- `interaction.js` already reads `camera.projectionMatrix` /
  `projectionMatrixInverse`, so picking works with the off-center projection
  without changes.
- Static single-scene export reads the camera config but uses the symmetric
  `fov` branch in `export/_bootstrap/_scene.py`; confirm it simply ignores
  `intrinsics` (serialization stays JSON-compatible). No export feature work here.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
