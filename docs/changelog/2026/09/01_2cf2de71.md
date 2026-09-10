# Changes since version 1.14.1

## New Features
- **Spreadsheet-style table editing** — `add_table` and `TableView` grids now
  enable Tabulator's keyboard navigation (Tab / Shift+Tab between cells, Enter
  to the next row, Tab past the last cell appends a row).
- **Row deletion by range selection** — table grids gain drag-to-select cell
  ranges and a "− Selected" button that deletes every row with at least one
  selected cell, reporting a `TableRowsDelete` payload via `on_row_delete`.
- **Table undo/redo** — `add_table` and `TableView` grids keep a backend-side
  undo history (one snapshot per committed edit, `max_history=100` default).
  Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y in the browser, or `undo_table` /
  `redo_table` / `clear_table_history` / `can_undo_table` / `can_redo_table`
  from Python, undo/redo edits and re-sync the grid.

## Bug Fixes
- **Table cells are editable again** — enabling drag-to-select cell ranges made a
  single click both start a range selection and open the cell editor (Tabulator's
  default `focus` edit trigger), so the editor immediately lost focus and cells
  could not be changed; cells now open for editing on **double-click**, leaving
  single click/drag for range selection.
- **Table cell edits keep their coordinates** — the table event payload, which
  the unified envelope nests under `value`, is now unwrapped in
  `_dispatch_control_event`, so `TableCellChange`, `TableRowAdd`, and
  `TableColumnAdd` receive the real `row` / `col` / `value` instead of a
  stringified dict.
- **Standalone HTML export of 2D views now recomputes the orthographic camera on
  window resize** — the export resize handler only updated the camera `aspect`
  (a no-op for orthographic cameras), so 2D snapshots and figures stretched and
  never self-corrected; it now recomputes `left`/`right`/`top`/`bottom` via the
  shared `applyOrthoFrustum`, matching the live viewer.
