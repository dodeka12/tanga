# Phase 2 — Backend control API on `TableView` / `Table`

## Goal

Expose full programmatic control over a table from Python: read/write single
cells, read/write the whole grid, clear history, and enable/disable sorting —
all backed by the `Table` model and synced to the browser through the existing
`control_update` push.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_control_value_api.py`, `py/tests/viz/test_controls.py`

## Steps

- [x] **2.1 — `Table.get_cell(row, col) -> str`**
  - Return `self.rows[row][col]` with the same bounds guard as `set_cell`
    (raise `IndexError` on out-of-range, documented).

- [x] **2.2 — `TableView` control methods**
  - `get_value() -> {columns, rows}` (explicit, delegating to `control`).
  - `get_cell(row, col) -> str` (delegating).
  - `set_cell(row, col, value) -> bool`: call `control.set_cell(...)` then
    `_push_value()` so the browser re-renders (reuses `control_update`; no new
    wire message).
  - `clear_history() -> None`: delegate to `control.clear_history()`.

- [x] **2.3 — Confirm undo/redo surface**
  - `undo()` / `redo()` / `can_undo` / `can_redo` already exist on `TableView`
    (and `Table`); document them in the API — no code change unless missing.

- [x] **2.4 — `sortable` flag**
  - Add `sortable: bool = True` to `Table` + `_fields()` and to
    `TableView.__init__` (see Phase 1). The frontend gates header-click sorting
    on it (Phase 6).

- [x] **2.5 — Tests**
  - `get_cell` / `set_cell` round-trip; `set_cell` pushes `control_update` with
    the updated grid and records undo history.
  - `clear_history` empties both stacks.
  - `sortable` serializes with default `True`.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py -q`

## Notes

- Cell/whole-grid reads and writes go through the `Table` model so undo/redo stays
  correct (backend stays authoritative).
- `set_cell` pushes the full `{columns, rows}` snapshot (same as undo/redo), so the
  frontend `apply` (Phase 4) already handles it with no new wire format.
