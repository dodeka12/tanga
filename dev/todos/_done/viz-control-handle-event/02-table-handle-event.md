# Phase 2 — `Table.handle_event` + `on_change` field

## Goal

Implement `Table.handle_event` for the six table events and add the `on_change`
field it will fire.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/tests/viz/test_controls.py`

## Steps

- [x] **2.1 — `on_change` field**
  - Add `on_change: Handler | None = None` to `Table` (after `on_row_delete`),
    documented as: fired once with the full `{columns, rows}` on wholesale
    changes (undo/redo).

- [x] **2.2 — `Table.handle_event` override**
  - Implement `handle_event(self, event, payload)` per the README table: resolve
    `nested = payload.get("value")` with a top-level fallback, call the matching
    mutation method, and return the matching `Dispatch`.
  - `cell_change`/`row_add`/`column_add`/`row_delete` return
    `Dispatch("<event>", <payload dataclass>)` (no push — the browser grid is
    already updated).
  - `undo`/`redo`: call `undo()`/`redo()`; on success return
    `Dispatch("change", table_value, push=table_value)`, else `Dispatch()`,
    where `table_value = {"columns": list(self.columns), "rows": [list(r) for r in self.rows]}`.

- [x] **2.3 — Unit tests**
  - Each mutation event returns the right `Dispatch` and mutates the model.
  - `handle_event("undo")` after `set_cell` returns `("change", <restored>,
    push=<restored>)` and restores the grid; `handle_event("undo")` with empty
    history returns `Dispatch()`.

## Validation

`uv run pytest py/tests/viz/test_controls.py -q`

## Notes

- Model-only: this phase does not touch `Visualizer`.
- The mutation methods already bounds-check and no-op (return `False` without
  recording history); `handle_event` mirrors that by returning `Dispatch()` when
  a mutation returns `False`.
