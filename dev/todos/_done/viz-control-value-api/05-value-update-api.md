# Phase 5 — Value-update API (Python)

## Goal

Add the public "set a control's value after creation" API, normalized across
all control kinds, for both panel controls and layout views.

## Steps

- [x] **5.1 — `_controls.py` helpers**
  - `get_control_value(ctrl)` / `set_control_value(ctrl, value)` mapping the
    uniform `value` to the per-kind field with type coercion
    (float/str/bool); `Button` raises `TypeError`.

- [x] **5.2 — `views.py` helper**
  - `set_control_view_value(view, value)` for `ControlView` subclasses
    (same mapping).

- [x] **5.3 — `Visualizer.set_control_value(cid, value, *, scene_name="")`**
  - Look up `scene._controls[cid]`, call `set_control_value`, then push the
    `control_update` message (a `_push_control_update` helper, added in Phase 6).

- [x] **5.4 — `Visualizer.set_control_view_value(view, value)`**
  - Mirrors `set_view_camera`: validate `ControlView`, set its value, push
    `control_update` keyed by `view.id`.

- [x] **5.5 — `VizSceneHandle.set_control_value` + `update_control(value=…)`**
  - Scene-handle wrapper; `update_control` routes a `value=` keyword through
    `set_control_value`.

- [x] **5.6 — Tests + Validate**
  - `py/tests/viz/test_entry_points.py` (or a new `test_control_value_api.py`):
    mutation + message emission for slider/dropdown/checkbox/layout view;
    `Button` raises.
  - `uv run pytest py/tests/viz/test_entry_points.py py/tests/viz/test_views.py -q`.

## Validation

`uv run pytest py/tests/viz/test_entry_points.py py/tests/viz/test_views.py -q`

## Notes

- This is where the original "update value from backend" feature lands; the
  rename (Phases 1–4) is the breaking-change foundation.
