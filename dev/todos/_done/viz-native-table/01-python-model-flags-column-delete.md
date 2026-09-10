# Phase 1 — Python model: flags (titles/row-numbers/delete/sortable) + column delete

## Goal

Add the display/sort/delete flags (`show_column_titles`, `show_row_numbers`,
`allow_delete_columns`, `sortable`) and a full `column_delete` capability to the
backend: payload dataclass, mutation, event dispatch, and handler — mirroring the
existing `row_delete`. These are the only Python model changes in the plan.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/server.py` (`_EVENT_MSG_MAP` entry)
- Edit: `py/tests/viz/test_controls.py`, `py/tests/viz/test_table.py`

## Steps

- [x] **1.1 — Flags on `Table` (`_controls.py`)**
  - Add `show_column_titles: bool = True`, `show_row_numbers: bool = False`,
    `allow_delete_columns: bool = True`, `sortable: bool = True` to the `Table`
    dataclass.
  - Add all four to `Table._fields()`.

- [x] **1.2 — `TableColumnDelete` payload + handler**
  - Add `@dataclass TableColumnDelete` (field `col: int`) next to `TableRowsDelete`.
  - Add `on_column_delete: Handler | None = None` to `Table`.

- [x] **1.3 — `Table.delete_column(col) -> bool`**
  - Bounds-check `col` to `[0, len(columns))`; `_push_undo()`; remove the header and
    each row's cell at `col`; return success. (Undo/redo already snapshots
    `{columns, rows}`, so it covers this with no extra work.)

- [x] **1.4 — `handle_event` + `parse_table_event` branch**
  - `parse_table_event`: add a `column_delete` case returning
    `Dispatch("column_delete", TableColumnDelete(col))`.
  - `Table.handle_event`: add `elif event == "column_delete": self.delete_column(change.col)`.

- [x] **1.5 — Thread through `TableView.__init__`**
  - Add `show_column_titles`, `show_row_numbers`, `allow_delete_columns`,
    `sortable`, `on_column_delete` params, forwarded to `Table(...)`.

- [x] **1.6 — Event-map entry**
  - Add `"column_delete": "control:column_delete"` to `server.py::_EVENT_MSG_MAP`
    (next to `row_delete`). No other routing change — `dispatch_control_event`
    (`_layout.py`) and `Table.handle_event` are generic.

- [x] **1.7 — Tests**
  - Flags serialize with correct defaults; `TableView` pass-through.
  - `delete_column` mutates model, records history (undo restores), bounds-checks.
  - Dispatch round-trip: `column_delete` mutates the model and fires
    `on_column_delete`.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py py/tests/viz/test_table.py -q`

## Notes

- `delete_column` must `_push_undo()` so the existing snapshot undo/redo restores
  the deleted column.
- Keep the frontend out of scope here (it still ignores the new flags until later
  phases).
