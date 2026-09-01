# Phase 5 — export bootstraps use the shared module

## Goal

Delete the export's hand-maintained `_orthoFrustum2d`/`_finiteAspectExport` and
make `js_apply_camera`/`js_autofit_camera` call the bundled `camera-fit.js`
helpers with a width/height expression.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`
- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/_figure_html.py`
- Edit: `py/pytanga/viz/export/_animated_figure.py`

## Steps

- [x] **5.1 — `js_apply_camera` drops the duplicated helpers**
  - Remove `_finiteAspectExport` and `_orthoFrustum2d` from the emitted string.
  - In `applyCameraConfig`'s 2D branch, call
    `orthoFrustum(cfg.xmin, cfg.xmax, cfg.ymin, cfg.ymax, cfg.uniform !== false, cfg.border_px || 0, width, height)`
    (replacing the `_orthoFrustum2d(...)` call; `orthoFrustum` is declared by
    the now-bundled `camera-fit.js`).
  - Update the function's docstring.

- [x] **5.2 — `js_autofit_camera` emits the 6-arg call**
  - Add required `width_expr: str` and `height_expr: str` params.
  - Emit
    `fitCamera({registry_var}, {camera_var}, {controls_var}, {space_dim}, {width_expr}, {height_expr});`.

- [x] **5.3 — `_html.py` (snapshot/full-page)**
  - Pass `width_expr="window.innerWidth"`, `height_expr="window.innerHeight"`.

- [x] **5.4 — `_figure_html.py` (figure)**
  - Pass `width_expr=dim_w`, `height_expr=dim_h`.

- [x] **5.5 — `_animated_figure.py` figure adapter**
  - Move the `dim_w`/`dim_h` computation above the `js_autofit_camera(...)`
    call, then pass `width_expr=dim_w`, `height_expr=dim_h`.

- [x] **5.6 — `_animated_figure.py` full-page adapter**
  - Pass `width_expr="window.innerWidth"`, `height_expr="window.innerHeight"`.

## Validation

`uv run pytest py/tests/viz/test_export_camera.py py/tests/viz/test_export_static.py py/tests/viz/test_export_renderers.py -q`

## Notes

- `applyCameraConfig`'s callers already pass `(camera, controls, cfg, w, h)`, so
  no signature change is needed there.
- Responsive figures already use
  `(figContainer.clientWidth || window.innerWidth)` for `dim_w`/`dim_h`, so the
  fit becomes pane-size-aware in embedded/iframe figures.
