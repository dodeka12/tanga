# Phase 5 — Active cell + row/column deletion

## Goal

Add a single **active cell** with a border: click a cell to activate it, move it
with the cursor keys, and use it as the indicator for deleting its **row** or
**column**. Replaces the old multi-row "− Selected" model.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- Edit: `dev/src/js-tests/table-keyboard.test.mjs`

## Steps

- [x] **5.1 — Active-cell state + highlight**
  - Track one active cell (its `td`, `data-original-index`, and `data-col`).
  - Clicking a `td.tanga-cell` sets it active: move `.tanga-cell-active` (a border)
    to it and clear any previous active cell.

- [x] **5.2 — Cursor-key movement**
  - When the table has focus and no editor is open, arrow keys move the active cell
    up/down/left/right (clamped to bounds), updating the border; `preventDefault()`
    so the container doesn't scroll. Left/right must skip the row-number column.
  - The active cell becomes the focused/target cell for editing (Tab/Enter start
    editing from it).

- [x] **5.3 — "− Row" button**
  - Gated by `ctrl.allow_delete_rows !== false`. Deletes the active cell's original
    row → `sendControlEvent('control:row_delete', id, { rows: [originalIndex] })`.

- [x] **5.4 — "− Column" button + event mapping**
  - Gated by `ctrl.allow_delete_columns !== false`. Deletes the active cell's
    column → `sendControlEvent('control:column_delete', id, { col })`.
  - Add `'control:column_delete': 'column_delete'` to `_CONTROL_EVENTS`.

- [x] **5.5 — CSS**
  - `.tanga-cell-active { outline/border }` (does not disturb the cell box or the
    proportional fill) and delete-button styling.

- [x] **5.6 — JS tests**
  - Arrow-key movement clamps to bounds and skips the row-number column; delete
    buttons map to the active cell's original row index / column.

## Validation

`uv run python py/examples/viz/ui/controls/table_editing.py && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- A deleted row/column's active cell is invalidated; move it to the nearest
  surviving cell (or clear it) after the backend re-render via `apply`.
- Arrow keys must not move the active cell while an editor input is open.
