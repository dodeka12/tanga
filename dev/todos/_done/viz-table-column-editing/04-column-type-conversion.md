# Phase 4 — Column type change via context menu

## Goal

Right-click a header to *propose* a different column type; the backend runs the
base conversion (rejecting impossible switches) and pushes the full grid on
success, with an optional `on_column_type_change` handler that can use the base
handler's `bool` return (e.g. to show a warning banner).

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/controls/table.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- Edit: `py/tests/viz/test_controls.py`, `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **4.1 — Base conversion algorithm (`Table.convert_column`)**
  - Add `TableColumnTypeChange(col, target, ok, column_type)` in `_controls.py`.
  - Implement `Table.convert_column(col, target) -> bool` exactly per the README
    rules: idempotent on same kind; `string` always; `number` (bool→1/0, str →
    parse, else fail); `bool` (number 0/1 only, else fail; str `"true"`/`"1"`/
    `"false"`/`"0"`); `enum` (distinct non-empty values, only when
    `0 < len < 20`). On success: record undo, rewrite the column cells, set the
    resolved type, `_save()`, return `True`; otherwise leave the model untouched
    and return `False`.

- [x] **4.2 — Event dispatch + custom handler**
  - Add `Table.on_column_type_change: Handler | None`; add a `column_type_change`
    branch to `parse_table_event` (payload `{col, type}`) and to
    `Table.handle_event`, which calls `convert_column`, builds
    `TableColumnTypeChange(col, target, ok, column_type)`, and returns
    `Dispatch("column_type_change", payload, push=(get_value() if ok else None))`
    so a successful conversion pushes the full grid and the handler always fires.

- [x] **4.3 — View/API + routing + exports**
  - `TableView.convert_column(col, target) -> bool` (delegate + `_push_value()`
    on success); forward `on_column_type_change` in `TableView.__init__` and
    `control_to_view`.
  - Add `"column_type_change": "control:column_type_change"` to
    `server.py::_EVENT_MSG_MAP` and `'control:column_type_change':
    'column_type_change'` to `controls-panel.js::_CONTROL_EVENTS`.
  - Export `TableColumnTypeChange` from `py/pytanga/viz/__init__.py`.

- [x] **4.4 — Frontend context menu**
  - Add a `contextmenu` listener on each sortable `<th>` (preventDefault +
    stopPropagation) that shows a small theme-styled menu of the *other* three
    types; selecting one sends `control:column_type_change` with `{col, type}`.
  - Position the menu at the pointer, close on outside click / Escape / select;
    style it in `table.css` with `--tanga-*` tokens.

- [x] **4.5 — Tests**
  - bool→number maps `true/false`→`1/0`; number→bool succeeds only for 0/1
    (rejects e.g. `2`); enum succeeds for <20 distinct values and rejects ≥20;
    string always succeeds; a rejected conversion leaves the model unchanged.
  - `handle_event("column_type_change", …)` returns `ok=True` + `push` on
    success and `ok=False` + no push on rejection.
  - A registered `on_column_type_change` handler receives the payload (so it can
    show a warning banner on `ok=False`).

## Validation

```
uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py -q
uv run ruff check py/pytanga/viz/
node --check py/pytanga/viz/templates/controls/table.js py/pytanga/viz/templates/controls-panel.js
```

## Notes

- The custom handler is the `on_column_type_change` seam: it receives
  `TableColumnTypeChange.ok` (the base `convert_column` return), so a handler can
  call `table.convert_column(...)` itself and act on the returned bool.
- A rejected proposal leaves the DOM unchanged (no push), so the warning banner
  is the only user feedback.
