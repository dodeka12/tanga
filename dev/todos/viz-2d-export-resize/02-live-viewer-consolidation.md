# Phase 2 — Live viewer uses the shared helper

## Goal

Delete `view_mode.js`'s private `_applyOrthoFrustum` and have `handleResize`
call the shared `applyOrthoFrustum` — a behavior-identical refactor.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`

## Steps

- [x] **2.1 — Import the shared helper**
  - Change `import { finiteAspect, orthoFrustum } from './camera-fit.js';` to
    also import `applyOrthoFrustum`.
- [x] **2.2 — Delete the private `_applyOrthoFrustum`**
  - Remove the function and its doc comment (currently lines 33–80).
- [x] **2.3 — Update `handleResize`**
  - Replace `_applyOrthoFrustum(camera, width, height);` with
    `applyOrthoFrustum(camera, width, height);`, keeping the
    `spaceDim === 2 && camera.isOrthographicCamera` guard.

## Validation

`node --check py/pytanga/viz/templates/view_mode.js`

## Notes

- `handleResize`'s public signature and behavior are unchanged; its three
  callers (`viewer.js`, `views/three-view.js`, `sdf/sdf_viewer.js`) are
  untouched.
