# Phase 4 — Server routing + undo/redo dispatch

## Goal

Route the new frontend `undo` / `redo` events to the backend and dispatch them:
resolve the control, `undo()`/`redo()`, and push `control_update`.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_table.py` (dispatch) and any server routing test

## Steps

- [x] **4.1 — `_EVENT_MSG_MAP` (`server.py`)**
  - Add `"undo": "control:undo"` and `"redo": "control:redo"` to the map
    (line ~35). The unified `event` envelope path already forwards these to the
    control callback; the legacy `control:*` top-level tuple is **not** used by
    `sendControlEvent`, so leave it unless a routing test requires otherwise.

- [x] **4.2 — `_dispatch_control_event` branches (`visualizer.py`)**
  - `control:undo`: resolve control; if a `Table`, call `undo()`; push
    `control_update` on success.
  - `control:redo`: same with `redo()`.
  - No-op (return) when no control / empty stack; do not raise.

- [x] **4.3 — Tests**
  - `_dispatch_control_event("control:undo", {"control_id": "tbl"})` restores the
    pre-edit grid and pushes `control_update` (monkeypatch the push).
  - `control:redo` re-applies after an undo.
  - Unknown id is a no-op.

## Validation

`uv run pytest py/tests/viz/test_table.py py/tests/viz/test_server_layout.py py/tests/viz/test_server_lifecycle.py -q`

## Notes

- Keep `control:undo`/`control:redo` symmetric with the existing table-event
  branches (resolve → mutate → push), but with no user handler to call.
- If a `server.py` routing test exists for `_EVENT_MSG_MAP`, extend it to assert
  `undo`/`redo` map to `control:undo`/`control:redo`.
