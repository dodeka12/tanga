# Phase 2 — Python view model: rename `default` → `value`

## Goal

Apply the same rename to the layout-API control views so the Python view
model and the dataclass model stay consistent.

## Steps

- [x] **2.1 — `views.py` control views**
  - `SliderView`: `default: float | None = None` → `value`; `self.default` →
    `self.value`; `_serialize` `"default"` → `"value"`.
  - `DropdownView`, `ColorPickerView`, `CheckboxView`: same rename.

- [x] **2.2 — Tests `py/tests/viz/test_views.py`**
  - `default=` → `value=`, `node["default"]` → `node["value"]`, `.default` →
    `.value`.
  - Rename `test_slider_default_defaults_to_min` →
    `test_slider_value_defaults_to_min`.

- [x] **2.3 — Validate**
  - `uv run pytest py/tests/viz/test_views.py -q`.

## Validation

`uv run pytest py/tests/viz/test_views.py -q`

## Notes

- `SliderView` keeps the "unset `value` → `min`" fallback.
