# Phase 1 — `Table` history + mutation methods

## Goal

Add snapshot-based undo/redo state and the four mutation methods to the `Table`
control dataclass in `_controls.py`, with a configurable depth cap, plus unit
tests. No dispatch or API changes yet — this is pure model logic.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_controls.py`

## Steps

- [x] **1.1 — History fields on `Table`**
  - Add `max_history: int = 100` and private `_undo: list[dict] = field(...)`,
    `_redo: list[dict] = field(...)` to `Table` with
    `field(default_factory=list, repr=False, compare=False)` (so serialization,
    `repr`, and equality ignore them).

- [x] **1.2 — Snapshot + stack helpers**
  - `_snapshot() -> dict` returning `{"columns": list(self.columns),
    "rows": [list(r) for r in self.rows]}`.
  - `_push_undo()`: append the current snapshot to `_undo`, clear `_redo`, then
    trim `_undo` to `max_history` (drop oldest) when `max_history` is not `None`.
  - `_restore(snap)`: copy `columns`/`rows` back from a snapshot.

- [x] **1.3 — Mutation methods**
  - `set_cell(row, col, value) -> bool`: bounds-check; on valid range
    `_push_undo()` then `self.rows[row][col] = str(value)`; return success.
  - `insert_row(row, values) -> bool`: bounds-check `row` to `[0, len(rows)]`;
    `_push_undo()` then insert a string-coerced row at that index.
  - `insert_column(col, header, values) -> bool`: bounds-check `col` to
    `[0, len(columns)]`; `_push_undo()` then insert the header and per-row
    value (pad `values` with `""` to the current row count).
  - `delete_rows(rows) -> bool`: keep valid ascending indexes, `_push_undo()`
    then remove in **descending** order; return `False` when nothing deleted.

- [x] **1.4 — `undo()` / `redo()` / `clear_history()` / `can_undo` / `can_redo`**
  - `undo()`: if `_undo` non-empty, push current snapshot to `_redo`, pop from
    `_undo`, `_restore` it, return `True`; else `False`.
  - `redo()`: symmetric (push current to `_undo`, pop `_redo`, restore).
  - `clear_history()`: clear both stacks.
  - Read-only `can_undo` / `can_redo` properties.

- [x] **1.5 — `set_control_value` Table branch clears history**
  - After replacing `ctrl.columns` / `ctrl.rows`, call `ctrl.clear_history()`
    (full programmatic replace = new baseline).

- [x] **1.6 — Unit tests (`test_controls.py`)**
  - Snapshot/undo/redo round-trip: edit a cell, `undo()` restores old value,
    `redo()` re-applies it.
  - Row insert / multi-row delete restore the prior grid on `undo()`.
  - Column insert restores prior columns on `undo()`.
  - A new mutation after `undo()` clears the redo stack.
  - Depth cap: with `max_history=2`, the oldest snapshot is dropped.
  - Out-of-range `set_cell` / `insert_row` / `insert_column` return `False` and
    don't record history.
  - `set_control_value(table, {...})` empties both stacks.

## Validation

`uv run pytest py/tests/viz/test_controls.py -q`

## Notes

- Follow the `FileChooser`/`ValueEdit` precedent: `kind` is a class-level
  default, `on_*` handlers are plain attributes (not serialized); the new
  history fields must not appear in `_serialize_one_control` output.
- `max_history=None` means unlimited (no trimming); the public default stays 100.
