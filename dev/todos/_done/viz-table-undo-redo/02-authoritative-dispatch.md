# Phase 2 — Authoritative dispatch

## Goal

Make `_dispatch_control_event` mutate the resolved `Table` (recording history)
for the four existing table events, **before** invoking the user handler. After
this phase the Python `Table.rows`/`columns` reflect the live grid, so undo/redo
has real state to operate on.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_table.py`

## Steps

- [x] **2.1 — Resolve and mutate on `control:cell_change`**
  - In the existing `control:cell_change` branch, resolve
    `ref = self._resolve_control(cid)`; when `ref.control` is a `Table`, call
    `ref.control.set_cell(row, col, value)` (already unwrapped from the nested
    payload). Then look up and call the handler exactly as today.

- [x] **2.2 — `control:row_add`**
  - Resolve control; call `insert_row(row, values)` when it is a `Table`; then
    call the handler.

- [x] **2.3 — `control:column_add`**
  - Resolve control; call `insert_column(col, header, values)` when a `Table`;
    then call the handler.

- [x] **2.4 — `control:row_delete`**
  - Resolve control; call `delete_rows(rows)` when a `Table`; then call the
    handler.

- [x] **2.5 — Keep handler behavior identical**
  - Handler lookup/`try`/`except`/logging stays unchanged; mutation happens
    before the handler call, and `None` control (e.g. handler without a stored
    control) still dispatches the handler as before.

- [x] **2.6 — Tests (`test_table.py`)**
  - After `control:cell_change`, `viz.get_control("tbl")` returns the new value
    at the edited cell (both panel `add_table` and layout `TableView`).
  - After `row_add` / `column_add` / `row_delete`, `viz.get_control("tbl")`
    reflects the insert/delete.
  - Undo via the model (`_resolve_control("tbl").control.undo()`) restores the
    pre-dispatch grid.

## Validation

`uv run pytest py/tests/viz/test_table.py -q`

## Notes

- Reuse the `nested = payload.get("value")` unwrapping already present in each
  branch (the current code handles both flat and nested payloads).
- `_resolve_control` returns `ControlRef(placement, control, scene)`; guard with
  `isinstance(ref.control, Table)` before mutating.
