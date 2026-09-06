# Phase 1 — `EControlVariant` + `variant` on button/checkbox/slider

## Goal

Introduce the extensible control-variant enum and thread it through the
button/checkbox/slider model, serialization, and view wrappers. No frontend
styling yet (that lands with the menu work in Phase 5).

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/tests/viz/test_controls.py` (extend) / `py/tests/viz/test_views.py` (extend)

## Steps

- [x] **1.1 — `EControlVariant` StrEnum (`_controls.py`)**
  - Add `class EControlVariant(StrEnum): DEFAULT = "default"; MENU = "menu"`.
  - Import `StrEnum` from `enum`.

- [x] **1.2 — `variant` field + serialization**
  - Add `variant: EControlVariant = EControlVariant.DEFAULT` to `Button`,
    `Checkbox`, `Slider` (after their existing `kind` field).
  - In `_serialize_one_control`, emit `base["variant"] = str(ctrl.variant)` for
    the `Button`, `Checkbox`, `Slider` branches.

- [x] **1.3 — View wrappers accept `variant` (`views.py`)**
  - Add `variant: EControlVariant = EControlVariant.DEFAULT` to `ButtonView`,
    `CheckboxView`, `SliderView` constructors and pass it into the wrapped
    `Button` / `Checkbox` / `Slider`.

- [x] **1.4 — Export**
  - Import and export `EControlVariant` from `py/pytanga/viz/__init__.py`
    (add to `__all__`).

- [x] **1.5 — Tests**
  - `test_controls.py`: `_serialize_one_control` for button/checkbox/slider
    includes `"variant": "default"`; a menu-variant button serializes
    `"variant": "menu"`.
  - `test_views.py`: `ButtonView(..., variant=EControlVariant.MENU)` serializes
    `"variant": "menu"` in the layout node.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_views.py -q`
