# Phase 2 — Frontend `orthoFrustum` modes

## Goal

Implement the four `stretch` modes in the shared camera-fit module and thread
the string through `view_mode.js` and `fit_camera.js`, with a Node-based math
test.

## Files

- Edit: `py/pytanga/viz/templates/camera-fit.js`
- Edit: `py/pytanga/viz/templates/view_mode.js`
- Edit: `py/pytanga/viz/templates/fit_camera.js`
- Edit: `py/tests/viz/test_camera_fit_unification.py`
- New: `py/tests/viz/test_camera_fit_math.py`

## Steps

- [x] **2.1 — `orthoFrustum` dispatch**
  - Rename the 5th parameter `uniform` → `stretch` and dispatch on the string:
    `"fill"` (existing stretch), `"fill_x"`/`"fill_y"` (new uniform cover
    modes), default `"fit"` (existing letterbox). Guard `fill_x`/`fill_y` with
    `cw > 0 && ch > 0` (fall back to `fit` otherwise).

- [x] **2.2 — `applyOrthoFrustum` resize**
  - Read `v2d.stretch || 'fit'` instead of `v2d.uniform !== false` when
    recomputing the frustum from `_view2d`.

- [x] **2.3 — `view_mode.js` + `fit_camera.js`**
  - `view_mode.js`: in `switchToCamera` use `cc.stretch || 'fit'`, pass it to
    `orthoFrustum`, and store `_view2d.stretch`; the default-2D branch stores
    `stretch: 'fit'`.
  - `fit_camera.js`: call `orthoFrustum(..., 'fit', 0, ...)` and store
    `_view2d = {..., stretch: 'fit', border_px: 0}`.

- [x] **2.4 — Tests**
  - Update `test_camera_fit_unification.py`'s `orthoFrustum(..., true, 0`
    assertion to the `'fit'` form.
  - Add `test_camera_fit_math.py` that runs `node --input-type=module -e` on
    `camera-fit.js` and checks `orthoFrustum` numeric output for `fit`, `fill`,
    `fill_x`, `fill_y` (letterbox vs cover), skipping if `node` is unavailable.

## Validation

`node --check py/pytanga/viz/templates/camera-fit.js && node --check py/pytanga/viz/templates/view_mode.js && node --check py/pytanga/viz/templates/fit_camera.js && uv run pytest py/tests/viz/test_camera_fit_unification.py py/tests/viz/test_camera_fit_math.py -q`

## Notes

- `camera-fit.js` is pure (no `three`/DOM imports), so it can be executed by
  Node as an ES module for the math test.
