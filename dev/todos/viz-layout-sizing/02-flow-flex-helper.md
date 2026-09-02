# Phase 2 — Flow flex helper (pure JS)

## Goal

Add a pure, DOM-free JS helper that maps a child's `preferred` size to CSS
flex, and parametrize the stack content-size math by `gap`. This is the unit
under the frontend wiring in phase 3.

## Files

- New: `py/pytanga/viz/templates/views/flow-size.js`
- Edit: `py/pytanga/viz/templates/views/stack-size.js`
- New: `dev/src/js-tests/flow-size.test.mjs`
- Edit: `dev/src/js-tests/stack-size.test.mjs`

## Steps

- [x] **2.1 — `flow-size.js`: `flowFlex(sizeSpec)` and `flexCss(flex)`.**
  - `flowFlex(sizeSpec)` takes a `Size`-shaped object (`{ value, unit }`) or
    `null`/`undefined` and returns `{ grow, shrink, basis }`:
    - `null`/`undefined` or `unit === 'auto'` → `{ grow: 0, shrink: 1, basis: 'auto' }`
    - `unit === 'fr'` → `{ grow: value, shrink: 1, basis: '0' }`
    - `unit === 'px'` → `{ grow: 0, shrink: 0, basis: value + 'px' }`
    - `unit === '%'` → `{ grow: 0, shrink: 0, basis: value + '%' }`
  - `flexCss({ grow, shrink, basis })` → the string `"<grow> <shrink> <basis>"`.
  - No imports beyond reading the plain `{ value, unit }` shape; keep it
    dependency-free and testable under `node --test`.

- [x] **2.2 — Parametrize `gap` in `stack-size.js`.**
  - Change `stackMinSize(axis, direction, children, available, gap = GAP)` and
    `stackPreferredSize(axis, direction, children, available, gap = GAP)` to use
    the `gap` argument instead of the module constant in the sum terms.
  - Keep `export const GAP = 4` as the default value (the default parameter).

- [x] **2.3 — Update `stack-size.test.mjs`.**
  - Add a case where `gap = 0` makes a vertical stack's min height equal the
    bare sum of child minima (no gap term), and a non-default `gap = 10` adds
    `(n - 1) * 10`.

- [x] **2.4 — New `flow-size.test.mjs`.**
  - `flowFlex(null)` and `flowFlex({value:0,unit:'auto'})` → `0 1 auto`.
  - `flowFlex({value:2,unit:'fr'})` → `2 1 0`.
  - `flowFlex({value:200,unit:'px'})` → `0 0 200px`.
  - `flowFlex({value:50,unit:'%'})` → `0 0 50%`.
  - `flexCss` string assembly for each.

## Validation

```powershell
node --test dev/src/js-tests/flow-size.test.mjs dev/src/js-tests/stack-size.test.mjs
```

## Notes

- The `Size` object already exposes `.value`/`.unit` (see `size.js`); the helper
  reads that shape directly so it works with both parsed `Size` instances and
  the serialized JSON shape.
