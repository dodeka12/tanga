# Phase 3 — `fit_camera.js` contain-fit via the shared module

## Goal

Make the shared `fitCamera` accept `(width, height)`, compute a true contain-fit
of the content bounding box via `orthoFrustum`, and store the **raw** rect so
resize stays correct for any aspect.

## Files

- Edit: `py/pytanga/viz/templates/fit_camera.js`

## Steps

- [x] **3.1 — Import the shared helper, drop the local one**
  - Add `import { orthoFrustum } from './camera-fit.js';`.
  - Delete the private `_finiteAspect` function.

- [x] **3.2 — Parameterize `fitCamera`**
  - Change the signature to
    `fitCamera(sceneObjects, camera, controls, spaceDim, width, height)` and
    update the JSDoc `@param` lines.

- [x] **3.3 — Rewrite the 2D branch as a contain-fit**
  - Keep the existing bounding-box computation (`box`, empty-check, `center`,
    `size`).
  - Compute `margin = Math.max(size.x, size.y, 1) * 0.1;` and the raw fitted
    rect `{xmin, xmax, ymin, ymax}` = box expanded by `margin` on each side.
  - `const f = orthoFrustum(xmin, xmax, ymin, ymax, true, 0, width ?? window.innerWidth, height ?? window.innerHeight);`
    then set `camera.left/right/top/bottom` from `f`.
  - Keep `position`/`lookAt`/`updateProjectionMatrix`/`controls.target`/
    `controls.update` as today.
  - Store `camera.userData._view2d = { xmin, xmax, ymin, ymax, uniform: true, border_px: 0 };`.
  - Leave the 3D branch untouched.

## Validation

`node --check py/pytanga/viz/templates/fit_camera.js`

## Notes

- This is the deliberate framing change from the README: the stored rect is now
  aspect-independent, so `handleResize` recomputes the frustum correctly for any
  pane aspect, and wide content is no longer clipped in a narrow pane.
- The `width ?? window.innerWidth` fallback only triggers for callers that omit
  the size (the live wrapper and export pass it explicitly).
