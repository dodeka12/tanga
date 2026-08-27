# Phase 2 — Python control + group model

## Goal

Add the four new control dataclasses, icon/icon_only on `Button`, tooltip on
`Control`, and icon/tooltip on `ControlGroup`, and extend serialization to match
the fixed wire contract.

## Steps

- [x] **2.1 — `Control.tooltip`**
  - Add `tooltip: str = ""` to `Control` (inherited by every control).
  - Update the `Handler` docstring value-type list (bool for checkbox, str for
    text/color/textarea).

- [x] **2.2 — New control dataclasses (in `_controls.py`)**
  - `TextField(kind="text", value="", placeholder="", on_change=None)`.
  - `TextArea(kind="textarea", value="", placeholder="", rows=4, on_change=None)`.
  - `ColorPicker(kind="color", default="#ffffff", on_change=None)`.
  - `Checkbox(kind="checkbox", default=False, on_change=None)`.

- [x] **2.3 — `Button` icon/icon_only**
  - Add `icon: Icon | None = None` and `icon_only: bool = False` (import
    `Icon` from `._icons`).

- [x] **2.4 — `ControlGroup` icon/tooltip**
  - Add `icon: Icon | None = None` and `tooltip: str = ""`.

- [x] **2.5 — `_serialize_one_control`**
  - Emit `tooltip` when non-empty (base dict).
  - Add `text`, `textarea`, `color`, `checkbox` branches.
  - `button` branch: emit `icon` (when set) and `icon_only`.

- [x] **2.6 — `serialize_controls` group dict**
  - Add `icon` (when set) and `tooltip` (when non-empty) to each group entry.

- [x] **2.7 — Unit tests (`test_controls.py`)**
  - Serialization of each new control (exact dicts).
  - Button with icon/icon_only; button without icon (no `icon` key).
  - `Control.tooltip` present when set, absent when empty.
  - Group serialization with `icon` + `tooltip`.

- [x] **2.8 — Validate**
  - `uv run pytest py/tests/viz/test_controls.py -q` (green).

## Validation

`uv run pytest py/tests/viz/test_controls.py -q`

## Notes

- Keep `kind` strings lowercase and snake-case to match existing kinds.
- No behavior change for existing `slider`/`dropdown`/`file_chooser` shapes
  (except the optional `tooltip`).
