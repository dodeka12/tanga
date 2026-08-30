# Phase 4 — Server dispatch

## Goal

Route the three new inbound messages from the WebSocket handler to the correct
registered handler, building the event dataclasses, with focused tests.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/visualizer.py`
- New: `py/tests/viz/test_table.py`

## Steps

- [ ] **4.1 — Inbound routing (`server.py`)**
  - Add `"control:cell_change"`, `"control:row_add"`,
    `"control:column_add"` to the control-message tuple in `_ws_handler`
    (next to `control:change` / `control:click`).
  - Add a `_ws_msg_brief` case for the three types (concise `row/col` summary).

- [ ] **4.2 — Event dispatch (`visualizer.py::_dispatch_control_event`)**
  - Add three branches before the generic `handler(...)` call:
    - `control:cell_change` → `TableCellChange(row, col, value)` to
      `self._handler_registry.get(cid)`.
    - `control:row_add` → `TableRowAdd(row, values)` to
      `self._handler_registry.get(f"__row_add__{cid}")`.
    - `control:column_add` → `TableColumnAdd(col, header, values)` to
      `self._handler_registry.get(f"__column_add__{cid}")`.
  - Coerce `row`/`col` to `int`, `value`/`header` to `str`, and `values` to a
    `list[str]` defensively.

- [ ] **4.3 — Tests (`test_table.py`)**
  - `@pytest.mark.anyio` dispatch tests using `viz._dispatch_control_event` for
    each message type, asserting the handler received the correct dataclass
    instance (fields populated) and that unknown ids are no-ops.

## Validation

`uv run pytest py/tests/viz/test_table.py -q`

## Notes

- Follow the `test_file_chooser.py` pattern: a `_viz()` helper
  (`Visualizer(add_default_axes=False, add_default_grid=False)`) and inline
  `async def` handlers capturing into a list.
- Keep the branches as early `return`s (like `file_browser_*`) so the generic
  `control:click`/`value` path is untouched.
