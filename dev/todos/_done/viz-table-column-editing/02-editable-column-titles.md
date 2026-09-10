# Phase 2 — Editable column titles

## Goal

Double-click a header cell to rename the column, gated by a backend flag
(`editable_titles`, default `True`).

## Files

- Edit: `py/pytanga/viz/_controls.py`
- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/controls/table.js`
- Edit: `py/pytanga/viz/templates/views/table-view.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- Edit: `py/tests/viz/test_controls.py`, `py/tests/viz/test_control_value_api.py`

## Steps

- [x] **2.1 — Backend model + event payload**
  - Add `TableColumnTitleChange(col: int, title: str)` in `_controls.py`.
  - Add `Table.rename_column(col, title) -> bool`: bounds-check, record undo,
    set `self.columns[col] = title`, `_save()`, return `True`.
  - Add `Table.on_column_title_change: Handler | None` field and handle
    `column_title_change` in `Table.handle_event` via `parse_table_event` (new
    branch) + `rename_column`, returning
    `Dispatch("column_title_change", TableColumnTitleChange(...))` (no push —
    the frontend already applied it).

- [x] **2.2 — View/API layer**
  - `TableView.__init__` gains `editable_titles: bool = True` and
    `on_column_title_change: Handler | None`, forwarded to `Table`; add a
    `TableView.rename_column(col, title) -> bool` delegating + no push (matches
    `cell_change`).
  - `control_to_view` forwards `on_column_title_change`; `_fields()`/serialize
    include `editable_titles`.

- [x] **2.3 — Event routing**
  - Add `"column_title_change": "control:column_title_change"` to
    `server.py::_EVENT_MSG_MAP` and `'control:column_title_change':
    'column_title_change'` to `controls-panel.js::_CONTROL_EVENTS`.
  - Export `TableColumnTitleChange` from `py/pytanga/viz/__init__.py`.

- [x] **2.4 — Frontend header editor**
  - In `renderHeader`, when `ctrl.editable_titles !== false`, add a `dblclick`
    listener on the `<th>` (only on the title, not the sort arrow / resize
    handle) that swaps in an `<input class="tanga-table-title-editor">`.
  - On Enter/Tab/blur commit: set `columns[i] = value` locally, re-render the
    header + `fit()`, and `sendControlEvent('control:column_title_change',
    ctrl.id, { col: i, title: value })`. Escape cancels (restore, no event).
  - Style the editor so it sits inside the header row without changing its
    height.

- [x] **2.5 — Tests**
  - `Table.handle_event("column_title_change", ...)` mutates `columns[col]` and
    returns the payload with `push is None`.
  - `rename_column` bounds-check + history.
  - `TableView` serializes `editable_titles` (default `True`) and forwards the
    handler.

## Validation

```
uv run pytest py/tests/viz/test_controls.py py/tests/viz/test_control_value_api.py -q
uv run ruff check py/pytanga/viz/
node --check py/pytanga/viz/templates/controls/table.js py/pytanga/viz/templates/controls-panel.js
```

## Notes

- Title edits follow the `cell_change` pattern (frontend applies locally +
  backend mutates, no full-grid push) so the inline editor is not torn down.
- The `<th>`-level sort click was moved to the `.tanga-sort-arrow` span here
  (with `pointer-events: auto`), because the sort handler rebuilds the header on
  every click — which would otherwise destroy the `<th>` mid-double-click and
  break the title editor. This satisfies phase 3's step 3.2 early; phase 3 then
  only adjusts the arrow sizing.
