# Phase 8 — Finish de-inlining appearance

## Goal

Move the remaining inline appearance (outside the control factories) into theme
CSS files so *all* appearance lives in CSS. Computed geometry stays inline.

## Files

- Edit: `py/pytanga/viz/templates/viewer.html`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/pytanga/viz/templates/views/banner-view.js`
- Edit: `py/pytanga/viz/templates/views/overlay-view.js` (if inline)
- Edit: `py/pytanga/viz/templates/themes/base.css` (+ `views/*.css`)

## Steps

- [ ] **8.1 — `viewer.html` shell**
  - Move the status-dot + loading-overlay + reset (`* { margin:0 … }`) rules into
    `base.css`; keep the `<style>` only if truly structural (or remove entirely).
  - Keep the status dot's class hooks (`.connected` / `.disconnected`) and move
    colors to tokens.

- [ ] **8.2 — `three-view.js`**
  - Replace the SDF/WebGL warning banner inline styles with a
    `.tanga-warning-banner` class + CSS (keep `position:fixed`/z-index as
    structural CSS, colors via tokens). Leave `_applyOverlayAnchor` math inline.

- [ ] **8.3 — `banner-view.js` / `dialog-view.js` / `menu-view.js`**
  - Move panel appearance (background/border/radius/shadow/font/color) to
    `views/banner-view.css` etc.; keep the computed `transform: translate(-x%,-y%)`
    and align anchors inline.

- [ ] **8.4 — Smoke + audit**
  - Grep `templates/**/*.js` for remaining `background:` / `color:` /
    `border:` inline styles and reduce to computed-geometry-only. Extend the
    smoke page to cover banner + warning-banner.

## Validation

`node --check py/pytanga/viz/templates/views/three-view.js && node --check py/pytanga/viz/templates/views/banner-view.js && uv run pytest py/tests/viz/test_themes.py -q`
