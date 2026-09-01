# Phase 4 — Thread `space_dim` into the export adapters

## Goal

Pass each scene's real `space_dim` to `js_resize_handler` so the 2D branch is
actually taken.

## Files

- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/_figure_html.py`
- Edit: `py/pytanga/viz/export/_animated_figure.py`

## Steps

- [x] **4.1 — `_html.py` (snapshot)**
  - Add `space_dim=space_dim` to the `js_resize_handler(...)` call.
- [x] **4.2 — `_figure_html.py` (figure)**
  - Add `space_dim=space_dim` to the `js_resize_handler(...)` call.
- [x] **4.3 — `_animated_figure.py` figure adapter**
  - Add `space_dim=space_dim` to the `js_resize_handler(...)` call.
- [x] **4.4 — `_animated_figure.py` full-page adapter**
  - Add `space_dim=space_dim` to the `js_resize_handler(...)` call.

## Validation

`uv run pytest py/tests/viz/test_export_camera.py py/tests/viz/test_export_static.py -q`

## Notes

- All four adapters already compute a local `space_dim =
  scene_config.get("space_dim", 3)`, so this is a pass-through.
