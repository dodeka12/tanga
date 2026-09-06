# Phase 5 — `undo_table`/`redo_table` fire `on_change`

## Goal

Make the programmatic undo/redo API go through `handle_event` so it fires the
bulk `on_change` handler (and pushes) exactly like the frontend Ctrl+Z path.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **5.1 — Scheduled-fire helper**
  - Add a small private helper that schedules `_dispatch_event(cid, event, value,
    browser_id=None)` onto `self._loop` via `asyncio.run_coroutine_threadsafe`
    (mirroring the push-from-sync-method pattern in `set_control_view_value`).

- [x] **5.2 — Route `undo_table`/`redo_table` through `handle_event`**
  - `undo_table(cid)`: resolve + `isinstance(Table)` guard (raise `KeyError` as
    today); `d = ref.control.handle_event("undo", {})`; if `d.push is not None`
    push `control_update` and schedule-fire the `d.event` handler; return
    `d.push is not None`.
  - `redo_table(cid)`: same with `"redo"`.
  - Leave `clear_table_history`/`can_undo_table`/`can_redo_table` delegating to
    `Table` (already thin).

- [x] **5.3 — Tests**
  - `undo_table` restores the grid, pushes, and fires `on_change` once with the
    restored value (recorded async handler).
  - Empty-history `undo_table` returns `False` and fires nothing.

## Validation

`uv run pytest py/tests/viz/test_control_value_api.py py/tests/viz/test_table.py -q`

## Notes

- Keep the signatures synchronous (backward compatible). The async handler is
  fire-and-forget on the loop, with the existing `_dispatch_event` logging.
- The frontend Ctrl+Z path fires inline (phase 3) and the programmatic path
  schedules (this phase) — distinct call sites, no dedupe needed.
