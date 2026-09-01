# Phase 2 — Extract base + control CSS; de-inline control appearance

## Goal

Move the injected `<style>` blocks out of `controls-panel.js`,
`controls-attached.js`, and `stack-view.js` into `base.css` +
`controls/*.css` + `views/stack-view.css`, using CSS custom properties, and
replace inline appearance on the control factories with stable class names.

## Files

- New: `py/pytanga/viz/templates/themes/base.css`
- New: `py/pytanga/viz/templates/themes/controls/*.css` (button, slider,
  checkbox, dropdown, text-field, text-area, color-picker, value-edit,
  file-chooser, table)
- New: `py/pytanga/viz/templates/themes/views/stack-view.css`
- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/controls-attached.js`
- Edit: `py/pytanga/viz/templates/views/stack-view.js`

## Steps

- [ ] **2.1 — `base.css` tokens + global rules**
  - `:root { --tanga-bg: #1a1a2e; --tanga-fg: #ccc; --tanga-accent: #4488ff;
    --tanga-border: rgba(255,255,255,0.12); … }` (carry over today's palette).
  - Add global look & feel: font stack, scrollbar (from `_injectScrollStyles`),
    and the **borderless icon rule**
    (`.tanga-icon-button, .tanga-group-toggle { border: none; background: none; }`).

- [ ] **2.2 — `controls/*.css`**
  - Port each control's rules from `controls-panel.js::_injectStyles` into its
    own file, replacing hardcoded colors with `var(--tanga-…)`. Keep the same
    class selectors (`.tanga-action-button`, `.tanga-range-input`, …).

- [ ] **2.3 — `views/stack-view.css`**
  - Move `_injectScrollStyles` CSS into this file.

- [ ] **2.4 — Remove injected CSS from JS**
  - Delete `_injectStyles()` (and its `_injectStyles()` call) from
    `controls-panel.js` and `controls-attached.js`; delete `_injectScrollStyles()`
    from `stack-view.js`. Keep the classes the factories already add.

- [ ] **2.5 — De-inline control appearance**
  - In `controls-panel.js` factories, move `Object.assign(…style…)` appearance
    (background/border/color/padding) to the corresponding `.css` via classes;
    keep computed geometry (e.g. flex sizing of the file-chooser row) inline.

- [ ] **2.6 — Smoke**
  - New `dev/src/js-tests/control-theming-smoke.html` that links `base.css` +
    the component CSS directly and renders a button/slider/checkbox, asserting
    the button icon is borderless and colors come from `var()`.

## Validation

`node --check py/pytanga/viz/templates/controls-panel.js && node --check py/pytanga/viz/templates/controls-attached.js && node --check py/pytanga/viz/templates/views/stack-view.js && uv run pytest py/tests/viz/test_themes.py -q`
