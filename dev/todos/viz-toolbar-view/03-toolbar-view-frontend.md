# Phase 3 — Frontend `ToolbarView` rendering

## Goal

Render the serialized `toolbar` node in the browser: a horizontal flex row with
a thin border, inner margin (padding), and the gap/align/justify policy — sized
correctly by enclosing `SplitView`s.

## Files

- New: `py/pytanga/viz/templates/views/toolbar-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- New: `py/pytanga/viz/templates/themes/views/toolbar-view.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json`

## Steps

- [x] **3.1 — `toolbar-view.js`**
  - `export class ToolbarView extends StackView`, constructor
    `{ direction = 'horizontal', margin = null, border = true, gap = null,
    align = 'center', justify = 'start', children = [] }`.
  - Call `super({ direction, gap, align, justify, children: [] })`; store
    `this.margin`, `this.border`.
  - Add class `tanga-toolbar` (and `tanga-toolbar-borderless` when
    `border === false`); apply `margin` as inline `padding` on `this.el`
    (px, or `%` when the unit is `%`).

- [x] **3.2 — Chrome-aware sizing**
  - Override `minSizePx`/`preferredPx` (mirroring `GroupView`) so the toolbar's
    measured padding + border is added to the content size along both axes.
  - Use a `_chrome()` helper reading `getComputedStyle(this.el)` padding/border,
    with a static fallback constant for the fake-DOM Node tests (as
    `GroupView` does for its chrome).

- [x] **3.3 — `build.js` registration**
  - Import `ToolbarView` and add a `node.type === 'toolbar'` branch that
    constructs it from `node.margin` / `node.border` / `node.gap` /
    `node.align` / `node.justify`, calls `applySizeSpecs`, then adds children
    (same shape as the existing `stack` branch).

- [x] **3.4 — Theme CSS**
  - `toolbar-view.css`: `.tanga-toolbar { border: 1px solid
    var(--tanga-border-subtle); border-radius: 4px; }` and
    `.tanga-toolbar.tanga-toolbar-borderless { border: none; }`.
  - Add `"views/toolbar-view.css"` to `registry.json` `components` (alphabetical
    position in the views block).

## Validation

```
node --check py/pytanga/viz/templates/views/toolbar-view.js py/pytanga/viz/templates/views/build.js
node --test 'dev/src/js-tests/*.test.mjs'
uv run pytest py/tests/viz/ -q
```

## Notes

- The serialized values are the same strings the `Literal` form emitted, so the
  existing `stack-view.js` flex logic needs no change — only the new node type
  is added.
- Keep `direction` fixed to `'horizontal'` in the toolbar constructor.
