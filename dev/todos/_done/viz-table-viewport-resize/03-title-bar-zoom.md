# Phase 3 — Title-bar zoom controls

## Goal

Add right-aligned `+`/`−` controls in the table title bar to scale column
widths (preserving relative proportions) and step row height.

## Files

- Edit: `py/pytanga/viz/templates/table-grid.js`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`

## Steps

- [x] **3.1 — Pure `clamp` helper**
  - Add `export function clamp(value, min, max)` to `table-grid.js`.
- [x] **3.2 — Title bar**
  - Replace the plain `<label>` with a flex title bar: label left, a controls
    container right.
- [x] **3.3 — Column-width zoom**
  - Add `let colScale = 1;` and use
    `contentWidth = (container.clientWidth − rowNumberW) × colScale` in `fit()`.
    `+`/`−` buttons do `colScale = clamp(colScale ×/÷ 1.25, 0.25, 8); fit();`.
- [x] **3.4 — Row-height zoom**
  - `+`/`−` buttons do `rowHeight = clamp(rowHeight ± 4, 16, 60);` then re-apply
    the `--tanga-table-row-height` token.
- [x] **3.5 — Preserve state on `apply`**
  - `apply` keeps `weights` (col count unchanged), `colScale`, `rowHeight`;
    still resets `sortState`/`activeTd`/`editorCell`.
- [x] **3.6 — CSS**
  - Style `.tanga-table-title-bar` and the zoom buttons (reuse button styling).

## Validation

`node --check py/pytanga/viz/templates/controls-panel.js && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- `fitColumnWidths` (already tested) covers the proportional width math; the
  zoom is just the `colScale` multiplier.
