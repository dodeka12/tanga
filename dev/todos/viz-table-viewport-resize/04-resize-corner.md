# Phase 4 — Resize corner handle

## Goal

Add a bottom-right drag corner that resizes the whole table by setting the
view's preferred size (so the enclosing flow container re-lays-out).

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/views/table-view.js`
- Edit: `py/pytanga/viz/templates/themes/controls/table.css`

## Steps

- [x] **4.1 — `onResize` callback**
  - `table-view.js::render()` passes
    `onResize: (w, h) => { this.preferredWidth = { value: w, unit: 'px' }; this.preferredHeight = { value: h, unit: 'px' }; }`.
- [x] **4.2 — Corner handle**
  - `createTable` adds a `.tanga-table-resize` corner (bottom-right); on
    `pointerdown` capture the wrapper's rect and on move call
    `onResize(clamp(w), clamp(h))` (min ~200×120).
- [x] **4.3 — CSS**
  - Style `.tanga-table-resize` with the `::after` grip (mirror
    `.tanga-dialog-resize`).

## Validation

`node --check py/pytanga/viz/templates/controls-panel.js py/pytanga/viz/templates/views/table-view.js && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- In a `SplitView` the splitter owns the size, so `preferredchange` is a no-op
  there (corner is inert) — expected per the confirmed decision.
