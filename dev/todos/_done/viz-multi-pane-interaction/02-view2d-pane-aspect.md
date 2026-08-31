# Phase 2 — Pane-aspect 2D camera

## Goal

Compute the 2D orthographic frustum from the pane's measured aspect ratio
rather than `window.innerWidth / window.innerHeight`, so 2D `CoordinateSystem`
panes in a `SplitView` render at the correct scale without relying on a
follow-up resize.

## Files

- Edit: `py/pytanga/viz/templates/view_mode.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **2.1 — Accept a pane aspect in `switchToCamera`**
  - Change the signature to
    `switchToCamera(camera, controls, spaceDim, cameraConfig, viewAspect = null)`.
  - At the top compute
    `const aspect = (Number.isFinite(viewAspect) && viewAspect > 0) ? viewAspect : window.innerWidth / window.innerHeight;`
    and use `aspect` in place of the current `window.innerWidth / window.innerHeight`
    in the 2D branch (and as the 3D `cam.aspect` default).
- [x] **2.2 — Pass the measured pane aspect from `ThreeJsView`**
  - In `_applyCamera` (`views/three-view.js:300`), compute
    `const viewAspect = (this.width > 0 && this.height > 0) ? this.width / this.height : null;`
    and pass it as the last argument to `switchToCamera(...)`.
  - Leave `resize()`/`handleResize` as-is (it already recomputes the frustum from
    the measured extent via `_applyOrthoFrustum`).

## Validation

`node --check py/pytanga/viz/templates/view_mode.js && node --check py/pytanga/viz/templates/views/three-view.js && uv run pytest py/tests/viz -q`

## Notes

- The `userData._view2d` rectangle and the `uniform` letterbox policy are
  unchanged; only the aspect used to derive `left/right/top/bottom` changes.
- When the pane is not yet measured (`viewAspect === null`), behaviour falls
  back to the window aspect exactly as today — no regression for the
  full-window / single-scene case.
