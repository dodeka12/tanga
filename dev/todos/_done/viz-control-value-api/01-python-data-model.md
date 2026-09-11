# Phase 1 — Python data model: rename `default` → `value`

## Goal

Unify the value field on the `Control` dataclasses and their serialization.
`Slider`, `Dropdown`, `ColorPicker`, `Checkbox` switch from `default` to
`value`; `_serialize_one_control` emits `"value"` for every value-bearing
control.

## Steps

- [x] **1.1 — `_controls.py` dataclass fields**
  - `Slider.default: float = 0.5` → `value: float = 0.5`.
  - `Dropdown.default: str = ""` → `value: str = ""`.
  - `ColorPicker.default: str = "#ffffff"` → `value: str = "#ffffff"`.
  - `Checkbox.default: bool = False` → `value: bool = False`.

- [x] **1.2 — `_serialize_one_control`**
  - `Slider`: `"default": ctrl.default` → `"value": ctrl.value`.
  - `Dropdown`: `"default": ctrl.default` → `"value": ctrl.value`.
  - `ColorPicker` / `Checkbox`: `{"default": ctrl.default}` →
    `{"value": ctrl.value}`.

- [x] **1.3 — Tests**
  - `py/tests/viz/test_controls.py`: `default=` → `value=`, expected dict keys
    `"default"` → `"value"`.
  - `py/tests/viz/test_banner.py`: `default=` → `value=`, `["default"]` →
    `["value"]`.

- [x] **1.4 — Validate**
  - `uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_banner.py -q`.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_banner.py -q`

## Notes

- `TextField` / `TextArea` / `FileChooser` already use `value` — no change.
- No `default` alias is kept (breaking).
