# Phase 5 — Zoom icons, fit-to-content & view-state reporting

## Goal

Replace the glyph zoom controls with icon buttons, add fit-to-content column
sizing, and report view-state changes back to the backend.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/table-grid.js`
- Edit: `dev/src/js-tests/table-keyboard.test.mjs`

## Steps

- [x] **5.1 — icon zoom buttons (`controls/table.js`)**
  - Replace `addZoomGroup` with icon-only buttons via `createIconElement`:
    `material:arrow_left` / `material:arrow_right` (narrower/wider columns),
    `material:arrow_drop_up` / `material:arrow_drop_down` (shorter/taller rows),
    `material:fit_screen` (fit to content). Keep the existing
    `tanga-zoom-btn`/`tanga-icon-button` styling.

- [x] **5.2 — fit-to-content (`controls/table.js`, `table-grid.js`)**
  - `fitToContent()`: measure header + cell text widths (canvas `measureText`
    with the cell's computed font); bool/select cells contribute a fixed width;
    clamp each column to `[TABLE_MIN_COLUMN, TABLE_FIT_MAX]` + padding; set
    `colWidths` and `fit()`.
  - Add pure `fitContentColumnWidths(measured, {min, max, padding})` to
    `table-grid.js`; unit-test it.

- [x] **5.3 — report view state (`controls/table.js`)**
  - Send `sendControlEvent('control:table_view_change', id, {…})` with the changed
    keys: `sort` on header click, `row_height` on row zoom, `column_widths`
    (relative, `colWidths / sum`) on column zoom / resize drag-end / fit-to-content.
  - Debounce continuous sources (resize drag reports on pointerup; zoom buttons
    report immediately).

- [x] **5.4 — tests**
  - `node --test` for `fitContentColumnWidths` (min/max clamp, padding, empty).
  - Browser smoke: icons render, zoom/fit/sort update the grid and emit
    `table_view_change`.

## Validation

`node --test 'dev/src/js-tests/*.test.mjs'` + browser smoke.

## Notes

- `column_widths` are sent as relative proportions (sum ≈ 1), not absolute px, so
  the persisted layout re-fits any container width (see README contract).
