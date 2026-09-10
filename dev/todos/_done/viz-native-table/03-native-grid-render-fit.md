# Phase 3 — Native grid render + proportional fill + scrollbars

## Goal

Rewrite `createTable` to build a plain-DOM `<table>` grid (sticky header,
scrollable container, optional row-number column) with proportional column
widths that fill the container naturally, plus vertical and horizontal
scrollbars. Thread the new flags through `build.js`/`table-view.js`. Add the
grid CSS. Remove the Tabulator instantiation.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/views/table-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- New: `py/pytanga/viz/templates/table-grid.js` (pure `fitColumnWidths` + `sortRows` helpers)
- Edit: `dev/src/js-tests/table-keyboard.test.mjs`

## Steps

- [x] **3.1 — Pure helpers (`table-grid.js`)**
  - Export `fitColumnWidths(available, weights, { min = 24 } = {}) -> number[]`
    distributing `available` proportionally to `weights` (clamped at `min`);
    `available` is the full container width (no gap).
  - Export `sortRows(rows, colIndex, direction)` returning a display order
    (stable, numeric-aware fallback to string) — pure, no DOM; used in Phase 6.

- [x] **3.2 — Rewrite `createTable` skeleton**
  - Keep `wrapper`/`label`/`container`/`buttonRow` and the `_controlRegistry` +
    `sendControlEvent` wiring. Replace `new Tabulator(...)`, `buildDefs`,
    `buildData`, and the `typeof Tabulator` guard with a native grid builder.
  - DOM: `container(.tanga-table-container.tanga-table-grid.tanga-scroll,
    overflow:auto) > table(.tanga-table) > thead(.tanga-table-head) +
    tbody(.tanga-table-body)`. `table-layout: fixed`; widths via a
    `<colgroup><col>`; `thead` is `position: sticky; top: 0`.
  - The `table` gets `min-width` = Σ column minimums so a narrow container scrolls
    horizontally instead of squeezing columns below their minimum.

- [x] **3.3 — Render columns + rows**
  - Header row from `ctrl.columns` when `ctrl.show_column_titles !== false`;
    omit `thead` when hidden.
  - Leading row-number column when `ctrl.show_row_numbers` (fixed width, e.g. 40px,
    class `tanga-row-number`), showing 1-based display position.
  - Each data cell: `td.tanga-cell[data-col][data-original-index]` (the original
    row index is the row's index in `ctrl.rows`).

- [x] **3.4 — Column fit + resize + scrollbars**
  - Track `weights[]` (initial equal). A `ResizeObserver` on the container calls
    `fitColumnWidths(container.clientWidth - rowNumberW, weights)` and writes each
    `<col>.style.width`.
  - Draggable 4px handles on header right edges update the dragged column's weight
    (then re-fit the rest), so resizes persist across re-fits.
  - Vertical scroll: rows scroll in the container with the sticky header visible.
    Horizontal scroll: the table's `min-width` (Σ `MIN`) overflows the container
    when columns don't fit.

- [x] **3.5 — Thread flags + CSS**
  - `build.js` `table_view` branch: pass `node.show_column_titles` /
    `node.show_row_numbers` / `node.allow_delete_columns` / `node.sortable` into
    `new TableView(...)`.
  - `table-view.js`: add the fields and pass them to `createTable`.
  - `table.css`: add `.tanga-table-grid`, header/cell borders, row striping,
    `.tanga-row-number`, hover/active state, and resize handle — all via
    `var(--tanga-*)` tokens (no hardcoded colors).

- [x] **3.6 — JS unit tests**
  - `fitColumnWidths` fills the available width, keeps proportions, clamps at `min`.

- [x] **3.7 — Theme tokens**
  - Define the table tokens (see README `Theme contract`) in `base.css` (dark
    defaults), `light/tokens.css`, and `pastel/tokens.css`.
  - Confirm `controls/table.css` only uses `var(--tanga-*)` tokens and stays in
    `registry.json` `components` (no registry change expected).

- [x] **3.8 — View base + sizing + single event channel**
  - `table-view.js` `TableView` stays `extends ControlView` (→ base `View`) so it
    slots into any `SplitView`/`StackView`/`GroupView`/overlay.
  - In the `TableView` constructor, set default sizes via the base `View` setters
    (mirror `file-chooser-view.js`): `minWidth`/`minHeight` (e.g. 240×160) and a
    natural `preferredWidth`/`preferredHeight`; `maxWidth`/`maxHeight` stay `null`
    unless the Python model sets them. `build.js` still overrides with serialized
    values.
  - All events use the single `sendEvent(id, "<event>", data)` envelope
    (`events.js`) via `sendControlEvent`; no new channel. `_controlRegistry[id]`
    keeps the `{ owner, kind: 'table', apply }` entry.

## Validation

`node --test dev/src/js-tests/table-keyboard.test.mjs && uv run pytest py/tests/viz/test_themes.py -q && uv run python py/examples/viz/ui/controls/table_split.py` (switch dark/light/pastel and confirm the grid restyles; shrink the pane and confirm vertical + horizontal scrollbars appear)

## Notes

- The grid must fill the container height (`height: 100%` from the layout view) via
  the existing `.tanga-table-container { flex: 1; min-height: 0 }` rule; the `thead`
  is `position: sticky; top: 0` inside the scroll container.
