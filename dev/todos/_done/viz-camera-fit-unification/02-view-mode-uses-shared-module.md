# Phase 2 — `view_mode.js` uses the shared module

## Goal

Delete the private `_finiteAspect`/`_orthoFrustum` from `view_mode.js` and thread
`(width, height)` through `_applyOrthoFrustum`, `handleResize`, and
`switchToCamera`.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`

## Steps

- [x] **2.1 — Import the shared helpers**
  - Add `import { finiteAspect, orthoFrustum } from './camera-fit.js';`.
  - Delete the private `_finiteAspect` and `_orthoFrustum` functions.

- [x] **2.2 — `_applyOrthoFrustum` takes `(width, height)`**
  - Change `_applyOrthoFrustum(camera, aspect)` →
    `_applyOrthoFrustum(camera, width, height)`.
  - Compute `const aspect = finiteAspect(width, height);` at the top and pass
    `width, height` to `orthoFrustum` in the finite-rect branch.
  - Keep the two fallback branches using `aspect` unchanged.

- [x] **2.3 — `handleResize` passes width/height**
  - Replace `_applyOrthoFrustum(camera, aspect)` with
    `_applyOrthoFrustum(camera, width, height)`.

- [x] **2.4 — `switchToCamera` threads `viewWidth`/`viewHeight`**
  - Change the signature to
    `switchToCamera(camera, controls, spaceDim, cameraConfig, viewWidth = null, viewHeight = null)`
    (replacing the old `viewAspect` 5th param).
  - Compute
    `const w = (Number.isFinite(viewWidth) && viewWidth > 0) ? viewWidth : window.innerWidth;`
    (and the `h` equivalent), then `const aspect = finiteAspect(w, h);` and
    `const safeAspect = Number.isFinite(aspect) ? aspect : 1.0;`.
  - In the `type === "2d"` branch pass `w, h` to `orthoFrustum` (replacing the
    old `_orthoFrustum(..., aspect)`).
  - Use `safeAspect`/`aspect` in the 3D (`cam.aspect`) and default-2D branches
    as before.

## Validation

`node --check py/pytanga/viz/templates/view_mode.js`

## Notes

- `sdf_viewer.js` calls `switchToCamera` with 4 args; the new `viewWidth`/
  `viewHeight` defaults keep it working.
- `three-view.js`'s `_applyCamera` currently passes `viewAspect` as the 5th
  positional arg; it is updated in Phase 4 to pass `viewWidth`/`viewHeight`.
