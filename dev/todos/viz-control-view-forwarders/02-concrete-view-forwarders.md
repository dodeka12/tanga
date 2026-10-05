# Phase 2 — Concrete view forwarders

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add explicit typed `@property` forwarders (read-only) to every concrete control
view so no attribute read relies on the removed `__getattr__`.

## Files

- Edit: `py/pytanga/viz/views/control_views.py`

## Steps

Add read-only `@property` forwarders (returning `self.control.<field>`) as
listed; mutations stay on the existing setters / methods.

- [ ] **2.1 — `SliderView` (`Slider`)**
  - `variant -> EControlVariant`, `min -> float`, `max -> float`,
    `step -> float`, `value -> float`, `on_change -> ControlHandler | None`,
    `on_press -> ControlHandler | None`, `on_release -> ControlHandler | None`.

- [ ] **2.2 — `ButtonView` (`Button`)**
  - `variant -> EControlVariant`, `icon -> Icon | None`,
    `icon_only -> bool`, `on_click -> ControlHandler | None`.

- [ ] **2.3 — `DropdownView` (`Dropdown`)**
  - `variant -> EControlVariant`, `options -> list[str]`, `value -> str`,
    `on_change -> ControlHandler | None`.

- [ ] **2.4 — `FileChooserView` (`FileChooser`)**
  - `value -> str`, `placeholder -> str`, `root -> str | None`,
    `file_filter -> str`, `folders_only -> bool`, `existing_only -> bool`,
    `on_change -> ControlHandler | None`.

- [ ] **2.5 — `TextFieldView` (`TextField`)**
  - `value -> str`, `placeholder -> str`, `on_change -> ControlHandler | None`.

- [ ] **2.6 — `TextAreaView` (`TextArea`)**
  - `value -> str`, `placeholder -> str`, `rows -> int`,
    `on_change -> ControlHandler | None`.

- [ ] **2.7 — `ColorPickerView` (`ColorPicker`)**
  - `value -> str`, `on_change -> ControlHandler | None`.

- [ ] **2.8 — `CheckboxView` (`Checkbox`)**
  - `variant -> EControlVariant`, `value -> bool`,
    `on_change -> ControlHandler | None`.

- [ ] **2.9 — `ValueEditView` (`ValueEdit`)**
  - `min -> float`, `max -> float`, `step -> float`, `digits -> int`,
    `value -> float`, `editable -> bool`, `on_change -> ControlHandler | None`.

- [ ] **2.10 — `LabelView` (`Label`)**
  - `value -> str`, `font_size -> float`.

- [ ] **2.11 — `MarkdownView` (`Markdown`)**
  - `value -> str`.

- [ ] **2.12 — `ProgressBarView` (`ProgressBar`)**
  - Reads: `title -> str`, `value -> float`, `total -> int`,
    `indeterminate -> bool`, `text -> str`; add `get_value -> dict[str, Any]`
    delegating to `self.control.get_value()`.

- [ ] **2.13 — `TableView` (`Table`)**
  - Add the remaining reads not already explicit:
    `columns -> list[str]`, `rows -> list[list[Any]]`,
    `column_types -> list[Any] | None`, and the `on_*` handler fields
    (`on_cell_change`, `on_row_add`, `on_column_add`, `on_row_delete`,
    `on_column_delete`, `on_column_title_change`, `on_column_type_change`,
    `on_cell_select`, `on_change`, `on_enum_options`).
  - `undo` / `redo` / `get_value` / `can_undo` / `can_redo` / `active_cell` are
    already explicit.

## Validation

```bash
uv run ty check && uv run ruff check . && uv run pytest py/tests/viz -q
```

## Notes

- Forwarded reads are read-only `@property` (no setter), matching today's
  `__getattr__`, which never forwarded writes — a stray `view.value = x` today
  set an unrelated instance attribute; after this change it raises
  `AttributeError`, which is the intended, clearer behavior.
