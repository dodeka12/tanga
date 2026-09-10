# Phase 6 — Frontend sorting by column

## Goal

Click a data-column header to sort the rendered rows ascending/descending (a third
state clears the sort). Display-only: the backend `rows` order and all `control:*`
row indexes stay original.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js` (or `table-grid.js`)
- Edit: `py/pytanga/viz/templates/themes/controls/table.css` (sort arrow indicator)

## Steps

- [x] **6.1 — Sort state + header toggle**
  - Gate header-click sorting on `ctrl.sortable !== false` (no sorting when disabled).
  - Track `{ colIndex, dir: 'asc'|'desc'|null }` on the grid.
  - Click a `th` cycles asc → desc → unsorted; add `.tanga-sort-asc`/`.tanga-sort-desc`
    and a small arrow to the header.

- [x] **6.2 — Reorder display rows**
  - Use `sortRows(rows, colIndex, dir)` (Phase 3) to reorder `tbody` rows by
    `data-original-index`, keeping `data-original-index` attached so edits/deletes
    still report original indexes.
  - The row-number column shows the 1-based display position after reorder.

- [x] **6.3 — Reset on data change**
  - `apply(value)` (backend refresh) clears the sort and re-renders in original
    order.

## Validation

`uv run python py/examples/viz/ui/controls/table_editing.py`

## Notes

- Stable sort; numeric-aware compare (parse numbers, fall back to locale string).
- Sorting must not disturb the active cell's original index mapping.
