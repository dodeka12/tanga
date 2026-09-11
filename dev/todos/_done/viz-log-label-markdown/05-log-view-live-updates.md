# Phase 5 — `LogView` live updates

## Goal

Wire backend `log()`/`clear()`/`load_file()` to the browser: `Visualizer`
injects a push callback into every `LogView` at layout time and emits
`log_update`; `viewer.js` dispatches it to the registry added in Phase 4.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/tests/viz/test_log_view.py` (or `test_control_value_api.py`)

## Steps

- [x] **5.1 — `Visualizer` registration + push**
  - Add `_register_log_views(root)` (walk `iter_log_views(root)`, set
    `view._push = self._push_log_update`); call it from `set_layout` right after
    `self._register_control_handlers(root)`.
  - Add `_push_log_update(view_id, action, lines=None)` building
    `{"type": "log_update", "id": view_id, "action": action}` (+ `"lines"` when
    given) and pushing via `run_coroutine_threadsafe(server.push_raw(...))`,
    mirroring `_push_control_update`.

- [x] **5.2 — `viewer.js` dispatch**
  - Import `applyLogUpdate` from `./views/log-view.js`; add
    `if (msg.type === 'log_update') { applyLogUpdate(msg); return; }` next to
    the `control_update` branch.

- [x] **5.3 — Tests**
  - `test_log_view.py`: a `Visualizer` with `set_layout(LogView(...))` followed
    by `log_view.log("x")` pushes a `log_update` (fake server), and `clear()`
    pushes a `clear` action.
  - Reuse the fake-server pattern from `test_control_value_api.py`
    (`test_set_control_value_*`).

## Validation

```
uv run pytest py/tests/viz/test_log_view.py py/tests/viz/test_control_value_api.py -q
node --check py/pytanga/viz/templates/viewer.js
node --test 'dev/src/js-tests/*.test.mjs'
```

## Notes

- `log_update` is global-by-id (no `scene` routing), exactly like
  `control_update`'s frontend dispatch.
- `_push_log_update` no-ops when no server/loop is running (mirrors
  `_push_control_update`).
