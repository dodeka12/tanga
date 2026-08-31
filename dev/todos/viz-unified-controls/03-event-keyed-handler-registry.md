# Phase 3 — Event-keyed handler registry

## Goal

Replace the bare-id `ControlHandlerRegistry` (with `__row_add__`/`__press__`/
`__group__` magic keys) with a `(target_id, event_name)` key, and dispatch by
event name.

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/tests/viz/test_controls.py` (+ any registry tests)

## Steps

- [ ] **3.1 — Extend registry to `(id, event)`**
  - Add `register(id, event, handler)`, `unregister(id, event=None)`,
    `get(id, event)`, `clear`.
  - Keep a `register(id, handler)` convenience mapping to `(id, "change")` for
    the common single-handler case.

- [ ] **3.2 — Migrate registration sites**
  - `_register_control_handlers` (layout) and each `add_*` (panel): register
    `(id, "change"/"click"/"cell_change"/"row_add"/"column_add"/"press"/"release"/"toggle")`
    instead of building `__row_add__{id}` strings.

- [ ] **3.3 — Dispatch by event**
  - Rewrite `_dispatch_control_event` to derive `event_name` from `msg_type` and
    look up `(cid, event_name)`; drop the magic-key string building.

- [ ] **3.4 — Tests**
  - Update `test_controls.py` registry tests; add coverage that
    `register(id, "row_add", …)` / `get(id, "row_add")` round-trip, and that
    layout + panel handlers coexist under the same id with different events.

## Validation

`uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_file_chooser.py py/tests/viz/test_table.py -q`
