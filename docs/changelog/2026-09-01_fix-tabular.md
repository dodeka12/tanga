# Changes since version 1.14.1

## New Features
- **Spreadsheet-style table editing** — `add_table` and `TableView` grids now
  enable Tabulator's keyboard navigation (Tab / Shift+Tab between cells, Enter
  to the next row, Tab past the last cell appends a row).

## Bug Fixes
- **Table cell edits keep their coordinates** — the table event payload, which
  the unified envelope nests under `value`, is now unwrapped in
  `_dispatch_control_event`, so `TableCellChange`, `TableRowAdd`, and
  `TableColumnAdd` receive the real `row` / `col` / `value` instead of a
  stringified dict.
