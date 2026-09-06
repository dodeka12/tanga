# Phase 2 — Standard row height + bounded scroll

## Goal

Give every row (including empty new rows) a standard height, and confirm the
grid scrolls internally now that it has a bounded size.

## Files

- Edit: `py/pytanga/viz/templates/themes/base.css`
- Edit: `py/pytanga/viz/templates/themes/light/tokens.css`
- Edit: `py/pytanga/viz/templates/themes/pastel/tokens.css`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- Edit: `py/pytanga/viz/templates/controls-panel.js`

## Steps

- [x] **2.1 — Row-height token**
  - Add `--tanga-table-row-height: 24px;` to `base.css` (dark defaults) and the
    light/pastel `tokens.css` overrides.
- [x] **2.2 — Apply the height to cells**
  - `table.css`: `.tanga-cell`, `.tanga-table-head-cell`, `.tanga-row-number`
    get `height: var(--tanga-table-row-height)`.
- [x] **2.3 — JS `rowHeight` state**
  - In `createTable`, add `let rowHeight = 24;` and write
    `table.style.setProperty('--tanga-table-row-height', rowHeight + 'px')` in
    `render()` so later zoom steps reuse it.
- [x] **2.4 — Confirm scroll**
  - With Phase 1's default size, `overflow: auto` now scrolls both axes (smoke
    via the examples).

## Validation

`uv run pytest py/tests/viz/test_themes.py -q && node --check py/pytanga/viz/templates/controls-panel.js`

## Notes

- New rows render with the same classes → standard height automatically.
