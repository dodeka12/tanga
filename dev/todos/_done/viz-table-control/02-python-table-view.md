# Phase 2 — Python table view

## Goal

A layout counterpart `TableView` so the table can be embedded in a declarative
split/stack layout (`view_layout`), plus its value coercion, with unit tests.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/tests/viz/test_views.py`

## Steps

- [x] **2.1 — `TableView(ControlView)`**
  - `_node_type = "table_view"`; `__init__(cid, *, label="", columns=(),
    rows=(), allow_add_rows=True, allow_add_columns=True, tooltip="",
    on_cell_change=None, on_row_add=None, on_column_add=None, **kwargs)`.
  - `_serialize` emits `columns`, `rows`, `allow_add_rows`,
    `allow_add_columns` on top of the base control fields.

- [x] **2.2 — `set_control_view_value`**
  - Add a `TableView` branch accepting a `{"columns", "rows"}` dict and copying
    it in place (mirrors the `Table` branch in `_controls.py`).

- [x] **2.3 — Exports**
  - Add `TableView` to the module `__all__`.

- [x] **2.4 — Unit tests (`test_views.py`)**
  - `TableView("tbl", columns=..., rows=...)._serialize(...)` → type
    `"table_view"` + fields.
  - `set_control_view_value(view, {"columns": [...], "rows": [...]})` updates
    the view.

## Validation

`uv run pytest py/tests/viz/test_views.py -q`

## Notes

- Match the `TextAreaView` / `FileChooserView` shape: keyword-only args, `**kwargs`
  forwarded to `ControlView`.
- `iter_control_views` already yields any `ControlView` subclass, so no change
  there — layout handler registration in Phase 3 picks `TableView` up for free.
