# Phase 3 — Larger, directly-clickable sort icons

## Goal

Make the sort arrow larger and the sole sort affordance (clicking it toggles
sort), without growing the header row height, so the header title is free for
double-click rename (phase 2).

## Files

- Edit: `py/pytanga/viz/templates/themes/controls/table.css`
- Edit: `py/pytanga/viz/templates/controls/table.js`

## Steps

- [x] **3.1 — CSS: larger arrow, no row growth**
  - Bump `.tanga-sort-arrow` `font-size` from `10px` to `14px`; keep
    `position: absolute; top: 50%; transform: translateY(-50%)` so the header
    row height (`height: var(--tanga-table-row-height)`) is unchanged.
  - Change `pointer-events: none` → `auto` and add `cursor: pointer`; add a
    hover/active color token if the theme has one, else keep the existing
    `--tanga-table-sort-arrow`.

- [x] **3.2 — Frontend: arrow is the sort target**
  - In `renderHeader`, remove the `<th>`-level `click` → `toggleSort` listener.
  - Attach the `toggleSort(i)` listener to the `.tanga-sort-arrow` span instead,
    with `e.stopPropagation()` so it does not collide with the title editor
    (phase 2) or the resize handle.
  - Keep the `tanga-sortable` / `tanga-sort-asc` / `tanga-sort-desc` classes for
    cursor and arrow glyph rendering.
  - Done in phase 2 (2.4) — required there because the sort handler's header
    rebuild would otherwise break the title editor's double-click.

- [x] **3.3 — Browser smoke**
  - Verify clicking the arrow toggles sort (↕ → ▲/▼) and clicking the title no
    longer sorts.

## Validation

```
node --check py/pytanga/viz/templates/controls/table.js
uv run pytest py/tests/viz/ -q
```

## Notes

- The arrow stays absolutely positioned, so a larger glyph cannot change the
  row height; the resize handle remains at the far right edge.
