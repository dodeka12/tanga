# Phase 6 — Python control views parity

## Goal

Add view counterparts for the new controls and thread tooltip/button-icon
through the `views.py` hierarchy so layouts/panels can host them.

## Steps

- [x] **6.1 — `ControlView.tooltip`**
  - Add `tooltip: str = ""` to `ControlView.__init__` and emit it in
    `ControlView._serialize`.

- [x] **6.2 — `ButtonView` icon/icon_only**
  - Add `icon: Icon | None = None`, `icon_only: bool = False`; serialize
    `icon` (when set) + `icon_only`.

- [x] **6.3 — New views**
  - `TextFieldView` (`_node_type="text_field_view"`),
    `TextAreaView` (`_node_type="text_area_view"`),
    `ColorPickerView` (`_node_type="color_picker_view"`),
    `CheckboxView` (`_node_type="checkbox_view"`), each mirroring the
    corresponding `Control` fields and `_serialize`.

- [x] **6.4 — Unit tests (`test_views.py`)**
  - `serialize_layout` of each new view (type/id/label + fields).
  - `ButtonView` with icon/icon_only; `ControlView` tooltip present/absent.

- [x] **6.5 — Validate**
  - `uv run pytest py/tests/viz/test_views.py -q` (green).

## Validation

`uv run pytest py/tests/viz/test_views.py -q`

## Notes

- Concrete views already forward `**kwargs` to `ControlView`, so `tooltip`
  flows once added there; still list `tooltip` explicitly on `ControlView`.
