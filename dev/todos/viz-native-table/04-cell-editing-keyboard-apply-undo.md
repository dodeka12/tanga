# Phase 4 — Editing, keyboard, +Row/+Column, registry apply, undo/redo

## Goal

Make the native grid interactive: double-click cell editing, keyboard navigation,
the +Row/+Column buttons, backend-driven `apply`, and the Ctrl+Z / Ctrl+Shift+Z /
Ctrl+Y undo/redo keydown. (Active-cell + deletion is Phase 5.)

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `dev/src/js-tests/table-keyboard.test.mjs`

## Steps

- [x] **4.1 — Double-click editing**
  - `dblclick` on `td.tanga-cell` swaps text for an `<input>` (value = current
    text), focuses + selects.
  - Commit on blur/Enter → `sendControlEvent('control:cell_change', id,
    { row: originalIndex, col: dataCol, value })`; Escape restores text, no event.

- [x] **4.2 — Keyboard navigation**
  - Tab/Shift+Tab move to the next/prev cell (opening its editor); Enter → next row.
  - Tab from the last cell (when `ctrl.allow_add_rows !== false`) appends a blank
    row and sends `control:row_add` with `{row: totalRows, values: ['', ...]}`.

- [x] **4.3 — + Row / + Column buttons**
  - "+ Row" appends a row (blank cells) and sends `control:row_add`.
  - "+ Column" appends a header + per-row blank and sends `control:column_add`.
  - Keep `allow_add_rows`/`allow_add_columns` gating.

- [x] **4.4 — Registry `apply` (backend refresh / reset / undo push)**
  - `_controlRegistry[ctrl.id].apply = (value) => rerender(value.columns, value.rows)`
    (preserve width weights when the column count is unchanged; clear sort + active
    cell).

- [x] **4.5 — Undo/redo keydown**
  - Keep `resolveUndoRedoAction` + `control:undo`/`control:redo`; change the editor
    guard from `.tabulator-editor` to the new input (skip while editing).

- [x] **4.6 — JS tests**
  - Edit-commit maps `(row, col, value)` correctly using `data-original-index`.

## Validation

`uv run python py/examples/viz/ui/controls/table_editing.py && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `row` in `control:cell_change` must be the **original** index (not the sorted
  position) — read it from `data-original-index`.
