# Phase 3 — Frontend `"pinhole"` branch + `applyPinhole` + delete clobber

## Goal

Wire the `PinholeCamera` config into the viewer with a single
`applyPinhole(camera, aspect)` used by both `switchToCamera` and resize, and
remove the legacy re-application block that clobbers the off-center projection.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **3.1 — import + `applyPinhole`**
  - Import `pinholeFraming` in `view_mode.js`.
  - Add `applyPinhole(camera, p, aspect)` that sets `projectionMatrix` from
    `pinholeFraming(...)` and keeps `projectionMatrixInverse` in sync.

- [x] **3.2 — `switchToCamera` `"pinhole"` branch**
  - When `cc.type === "pinhole"`, store `camera.userData._pinhole = cc` (the
    intrinsics/pose/fit) and call `applyPinhole(camera, cc, aspect)` after
    setting position/target/up/near/far. Remove the now-dead `intrinsics` branch
    in the `"3d"` case.

- [x] **3.3 — resize**
  - In `handleResize`, when `camera.userData._pinhole`, call
    `applyPinhole(camera, camera.userData._pinhole, aspect)` instead of
    `updateProjectionMatrix()`.

- [x] **3.4 — delete the `_applyCamera` clobber**
  - In `three-view.js`, remove the redundant `cc.position/target/fov/near/far`
    re-application (it duplicates `switchToCamera` and its `updateProjectionMatrix`
    call rewrote the off-center matrix).

## Validation

`node --check py/pytanga/viz/templates/view_mode.js py/pytanga/viz/templates/views/three-view.js && uv run pytest py/tests/viz/test_pinhole_math.py -q`

## Notes

- `interaction.js` already reads `projectionMatrix`, so picking keeps working.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
