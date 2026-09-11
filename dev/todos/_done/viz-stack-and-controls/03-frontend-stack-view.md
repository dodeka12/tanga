# Phase 3 — Frontend `StackView`

## Goal

A flow/flex container (`View`) that stacks children vertically, horizontally, or
wraps, with content-based natural sizing so it works as a `SplitView` pane.

## Steps

- [x] **3.1 — `templates/views/stack-view.js`**
  - `StackView extends View`; constructor `{ direction = 'vertical', children = [] }`.
  - Validate `direction` ∈ `vertical` | `horizontal` | `wrap`.
  - `this.children = []` + `addChild`/`removeChild` (mount children into `this.el`,
    re-measure on child `constraintschange`/`preferredchange`, mirroring
    `SplitView.addChild`).
  - `el` gets `display: flex` with
    `flex-direction: column` (vertical) / `row` (horizontal) / `row` + `flex-wrap:
    wrap` (wrap); `align-items: stretch`; `gap` for spacing.

- [x] **3.2 — Content-based natural sizing**
  - Override `minSizePx`/`preferredPx` to derive from children:
    - vertical → height = Σ children heights + gaps, width = max child width;
    - horizontal → width = Σ children widths + gaps, height = max child height;
    - wrap → measure rendered content (or sum + wrap heuristic); keep it
      best-effort, document that `wrap` uses measured `scrollWidth/scrollHeight`.
  - A pure helper (`stack-size.js`) keeps the arithmetic Node-testable.

- [x] **3.3 — Re-layout on extent change**
  - `_relayout()` emits `preferredchange` when children change (content size), so
    an enclosing `SplitView` re-resolves. Children flow via CSS flex (no absolute
    positioning).

- [x] **3.4 — Node test + smoke**
  - `dev/src/js-tests/stack-size.test.mjs` for the pure helper.
  - `dev/src/js-tests/stack-view-smoke.html`: mount a `StackView` with a few
    dummy `View`s, verify stacking/wrapping.

## Validation

`node --test 'dev/src/js-tests/stack-size.test.mjs'` + `node --input-type=module
--check` on `stack-view.js` (+ browser smoke page).
