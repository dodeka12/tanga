# Phase 3 — Export resize handler recomputes the 2D ortho frustum

## Goal

Make the export's `js_resize_handler` recompute the ortho frustum for 2D scenes
and store `camera.userData._view2d` in the export's 2D camera paths, so resize
matches the live viewer.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`

## Steps

- [x] **3.1 — `js_resize_handler` gains `space_dim: int = 3`**
  - Add the keyword-only parameter (defaulted so existing callers stay green).
  - In both the conditional and non-conditional branches, define local
    `const rw = …; const rh = …;` and, when `space_dim == 2`, emit
    `if (camera.isOrthographicCamera) { applyOrthoFrustum(camera, rw, rh); }`
    before the `aspect`/`updateProjectionMatrix()`/`setSize` lines.
  - Non-conditional branch uses `rw = {width_expr}`, `rh = {height_expr}`; the
    conditional branch already reads the container.
- [x] **3.2 — `js_apply_camera` stores `_view2d` in the 2D branch**
  - Inside the `typeof cfg.xmin === 'number' && …` guard, after setting
    `left/right/top/bottom`, store
    `camera.userData._view2d = { xmin: cfg.xmin, xmax: cfg.xmax, ymin: cfg.ymin, ymax: cfg.ymax, uniform: cfg.uniform !== false, border_px: cfg.border_px || 0 };`.
- [ ] **3.3 — `js_scene_setup` stores `_view2d` on the default 2D camera**
  - After `{camera_var}.lookAt(0, 0, 0);`, add
    `{camera_var}.userData._view2d = { xmin: _frustumSize * ({width_expr} / {height_expr}) / -2, xmax: _frustumSize * ({width_expr} / {height_expr}) / 2, ymin: -_frustumSize / 2, ymax: _frustumSize / 2, uniform: true, border_px: 0 };`
    (mirroring `switchToCamera`'s default-2D branch).

## Validation

`uv run pytest py/tests/viz/test_camera_fit_unification.py py/tests/viz/test_export_camera.py py/tests/viz/test_export_static.py -q`

## Notes

- `applyOrthoFrustum` is declared by the bundled `camera-fit.js`, which
  `generate_bootstrap_js` concatenates before the adapter JS, so the resize
  handler can call it by name.
