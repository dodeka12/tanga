# 2D standalone HTML export — recompute the ortho camera on resize — Overview

**Created:** 2026-09-01 | **Status:** Done | **Branch:** `fix/tabular`

## Goal

The standalone HTML exports (snapshot, figure, animated figure/full-page) of 2D
scenes render a distorted/stretched view, and resizing the browser window does
not correct it. Fix the export resize path so a 2D `OrthographicCamera`
recomputes its `left/right/top/bottom` frustum from the viewport size exactly
like the live viewer does — without changing live-viewer behavior.

## Root cause

For a 2D scene the export creates a `THREE.OrthographicCamera`. Its projection
matrix is derived from `left/right/top/bottom`, **not** `aspect`. The export's
`js_resize_handler()` (in `py/pytanga/viz/export/_bootstrap/_scene.py`) only
does:

```js
camera.aspect = w / h;
camera.updateProjectionMatrix();   // no-op for an ortho camera
renderer.setSize(w, h);
```

so on resize the canvas grows/shrinks but the world-rectangle stays frozen →
stretch/distortion that never self-corrects. The live viewer already handles
this correctly in `view_mode.js`'s `handleResize()` via its private
`_applyOrthoFrustum()`, which recomputes the frustum from the stored
`camera.userData._view2d` rect.

## Architecture (short)

- Extract the live viewer's private `_applyOrthoFrustum` into the shared, pure
  `templates/camera-fit.js` as `applyOrthoFrustum(camera, width, height)` (no
  `three`/DOM, Node-testable, already bundled into every export).
- Point `view_mode.js`'s `handleResize()` at the shared helper (a verbatim port
  → behavior identical).
- Make the export's `js_resize_handler()` recompute the ortho frustum for 2D by
  calling the bundled `applyOrthoFrustum`, and store `camera.userData._view2d`
  in the export's 2D camera paths so resize has a rect to recompute from.

## Fixed contract

```js
// templates/camera-fit.js  (no `three`/DOM; Node-testable)
finiteAspect(width, height);                                    // number | NaN
orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, width, height);
                                                                // {left,right,top,bottom}
applyOrthoFrustum(camera, width, height);                       // mutates left/right/top/bottom
```

`applyOrthoFrustum(camera, width, height)`:
1. if `camera.userData._view2d` is finite → `orthoFrustum(v2d.xmin, v2d.xmax,
   v2d.ymin, v2d.ymax, v2d.uniform !== false, v2d.border_px || 0, width, height)`;
2. else preserve the current full height, letterboxed to `finiteAspect(width,
   height)`;
3. else (corrupt/non-finite frustum) reset to a 10-unit-high default box.

```js
// templates/view_mode.js
handleResize(camera, renderer, labelRenderer, spaceDim, width, height); // unchanged
//   if (spaceDim === 2 && camera.isOrthographicCamera)
//       applyOrthoFrustum(camera, width, height);
```

```python
# export/_bootstrap/_scene.py
js_resize_handler(*, renderer_var, label_renderer_var, camera_var,
                  width_expr, height_expr, conditional=False, container_expr="",
                  space_dim=3)
# emits, for 2D ortho, `applyOrthoFrustum(camera, rw, rh)` before the
# aspect/updateProjectionMatrix/setSize lines
```

`js_apply_camera`'s 2D branch and `js_scene_setup`'s default 2D camera store
`camera.userData._view2d = {xmin, xmax, ymin, ymax, uniform, border_px}`.

## Decisions (confirmed)

- One source of truth: `applyOrthoFrustum` lives in `camera-fit.js` and is used
  by both the live viewer and the export resize handler.
- `_applyOrthoFrustum` is ported **verbatim** → no live-viewer behavior change.
- `js_resize_handler` gains `space_dim: int = 3` (defaulted) so each phase stays
  independently green; callers then thread the real `space_dim`.
- Store `_view2d` in the export's 2D paths for resize parity with
  `switchToCamera` (rather than relying only on the preserve-height fallback).
- No public Python API changes.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-shared-ortho-frustum-helper.md](./01-shared-ortho-frustum-helper.md) | Add `applyOrthoFrustum` to `camera-fit.js` + Node unit tests. |
| 2 | [02-live-viewer-consolidation.md](./02-live-viewer-consolidation.md) | `view_mode.js` uses the shared helper (verbatim port). |
| 3 | [03-export-resize-2d.md](./03-export-resize-2d.md) | `js_resize_handler` recomputes 2D ortho frustum; store `_view2d`. |
| 4 | [04-export-callers-space-dim.md](./04-export-callers-space-dim.md) | Thread `space_dim` into the four export adapters. |
| 5 | [05-regression-tests.md](./05-regression-tests.md) | Python regression tests pin the 2D resize emit. |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Branch changelog. |

## Testing as you go

- JS unit: `node --test dev/src/js-tests/camera-fit.test.mjs`
- JS syntax: `node --check py/pytanga/viz/templates/<file>.js`
- Python: `uv run pytest py/tests/viz/`
- Lint: `uv run ruff check py/pytanga/viz/export/ py/pytanga/viz/templates/`

## Non-goals

- No change to the 3D perspective resize/fit path or `CameraConfig3d`.
- No collapse of the `space_dim` vs `camera.type` taxonomy.
- No headless-browser harness; the runtime "no more stretch" check stays a
  manual browser smoke.
