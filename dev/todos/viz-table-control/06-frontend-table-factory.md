# Phase 6 — Frontend table factory + view

## Goal

Render the `table` control with Tabulator in `controls-panel.js`, and add the
layout `TableView` + `build.js` wiring.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- New: `py/pytanga/viz/templates/views/table-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`

## Steps

- [ ] **6.1 — `createTable(ctrl)` (`controls-panel.js`)**
  - Build a wrapper `div.tanga-control.tanga-table` with a `label` (as other
    factories) and a container `div` for Tabulator.
  - Guard with `typeof Tabulator !== 'undefined'`; on failure render a
    "Tabulator unavailable" notice in the container and skip wiring.
  - Map `columns` → `{title, field: 'c'+i, editor: 'input'}` and `rows` →
    `[{c0, c1, …}, …]`; instantiate
    `new Tabulator(container, { height: '220px', layout: 'fitColumns', data, columns })`.
  - `table.on('cellEdited', cell => …)` → send
    `sendControlEvent('control:cell_change', id, {row, col, value})` using
    `cell.getRow().getPosition()` and the field→column-index mapping.
  - "+ Row" / "+ Column" buttons (hidden when `allow_add_rows` /
    `allow_add_columns` are false): call `table.addRow({})` /
    `table.addColumn({title, field, editor:'input'})`, then send
    `control:row_add` / `control:column_add` with the new row/column contents.
  - Register `_controlRegistry[ctrl.id] = { kind:'table', apply: value =>
    table.setColumns(...)+table.setData(...) }` (no-op `apply` when Tabulator
    is unavailable).
  - `wrapper.addEventListener('pointerdown', e => e.stopPropagation())` (as the
    other factories).

- [ ] **6.2 — Dispatch (`_createControlElement`)**
  - Add `case 'table': return createTable(ctrl);`.

- [ ] **6.3 — `views/table-view.js` (new)**
  - `export class TableView extends ControlView` with `render()` returning
    `createTable({ id: this.controlId, label: this.label, tooltip: this.tooltip,
    columns: this.columns, rows: this.rows, allow_add_rows, allow_add_columns })`.

- [ ] **6.4 — `views/build.js`**
  - Import `TableView` and add an `else if (node.type === 'table_view')` branch
    constructing it from `node.id/label/tooltip/columns/rows/allow_add_rows/allow_add_columns`.

## Validation

Manual viewer smoke: a `table` control (and a `TableView` in a layout) renders,
cells are editable, cell/row/column events reach the Python handlers.
`uv run pytest py/tests/viz -q` for Python regression.

## Notes

- All events flow through `sendControlEvent`, so the Python dispatch (Phase 4)
  is the only backend change needed.
- `cellEdited` fires on cell commit; keep the field→index map in the factory
  closure. Prefer `cell.getRow().getPosition()` for the row index (Tabulator
  row positions are zero-based for unfiltered/unsorted data).
