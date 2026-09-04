# Phase 3 — `_dispatch_control_event` delegates through `handle_event`

## Goal

Replace the per-kind control ladder in `_dispatch_control_event` with a single
resolve → `handle_event` → push → fire tail. The non-control special cases stay.

## Files

- Edit: `py/pytanga/viz/_controls.py` (`parse_table_event` + refactor `Table.handle_event`)
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_table.py`

## Steps

- [x] **3.1 — Collapse the control ladder**
  - Keep the existing early returns for `close`/`accept`/`file_browser_navigate`/
    `file_browser_select`, the banner/editor `close`/`accept` handling, and
    `group_toggle` (route to `"toggle"` exactly as today).
  - For the remaining `control:*` messages: derive
    `event = msg_type[len("control:"):]`, resolve `ref = self._resolve_control(cid)`,
    call `d = ref.control.handle_event(event, payload)` (guard `ref`/`control`),
    then push/fire per the README contract (reusing the existing try/except +
    logging).
  - Delete the now-dead `control:cell_change` / `row_add` / `column_add` /
    `row_delete` / `undo` / `redo` branches and the generic tail.

- [x] **3.2 — Behavior-preserving verification**
  - The existing `test_table.py` dispatch round-trips (cell_change mutates model
    + fires handler, etc.) and `test_controls.py` must pass unchanged.

- [x] **3.3 — Bulk-fire test**
  - Register an `on_change` handler, call `_dispatch_control_event("control:undo",
    ...)`, assert the handler fired once with the restored `{columns, rows}` and
    a `control_update` was pushed.

## Validation

`uv run pytest py/tests/viz/test_table.py py/tests/viz/test_controls.py -q`

## Notes

- `msg_type` values are `control:change` / `control:click` / `control:press` /
  `control:release` plus the table + undo/redo ones — all covered by
  `handle_event` after this phase.
- Do not touch `close`/`accept`/`file_browser`/`group_toggle` code paths.
- Table payload parsing is shared with `Table.handle_event` via a module-level
  `parse_table_event` helper, and `_dispatch_control_event` keeps a
  `ref is None` fallback (banner controls / stale handler ids) that fires the
  handler without a control — preserving `test_dispatch_without_control_still_calls_handler`.
