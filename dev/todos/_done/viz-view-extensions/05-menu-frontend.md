# Phase 5 — Menu frontend (`menu-view.js`, build, viewer routing)

## Goal

Render `MenuView` in the browser: a borderless hamburger dropdown
(`click`-to-toggle), a permanent horizontal strip (`mode="bar"`), and nested
sub-menus; plus mount global-overlay menus into `getOverlay()`.

## Files

- New: `py/pytanga/viz/templates/views/menu-view.js`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Edit: `py/pytanga/viz/templates/controls-panel.js` (CSS `.tanga-menu-item`)

## Steps

- [x] **5.1 — `menu-view.js` (`MenuView extends StackView`)**
  - Import `createIconElement` from `../controls-panel.js`; build a borderless
    trigger (`background:none; border:none`) using `trigger` (default hamburger).
  - `mode="dropdown"`: click toggles a hidden options panel (a vertical
    `StackView`); outside-click / `Escape` closes it.
  - `mode="bar"`: render options always-visible in a horizontal strip.
  - **Sub-menus:** when a child is another `MenuView`, render it as an option
    row and open its panel beside the parent on click (absolute-positioned next
    to the parent panel), closing siblings on open.

- [x] **5.2 — `build.js`**
  - Add a `menu` branch: `new MenuView({ trigger, label, mode, direction,
    position, children })`, recursing over `node.children`.

- [x] **5.3 — `viewer.js` global overlay mount**
  - In `_buildLayout`, after building `msg.root`, build each `msg.overlay` view
    via `buildViewTree` and mount it into `getOverlay()` (import from
    `./overlay.js`), anchoring by its `position`.

- [x] **5.4 — `.tanga-menu-item` CSS (`controls-panel.js`)**
  - Add flat menu-row styling: no border/background, left-aligned full-width
    text, hover highlight; `createButton`/`createCheckbox`/`createSlider` add the
    class when `ctrl.variant === "menu"` (threaded through `build.js`).

- [x] **5.5 — Smoke**
  - New `dev/src/js-tests/menu-view-smoke.html`: assert the hamburger toggles the
    panel, `mode="bar"` renders inline, and a nested `MenuView` opens beside its
    parent.

## Validation

`node --check py/pytanga/viz/templates/views/menu-view.js && node --check py/pytanga/viz/templates/views/build.js && node --check py/pytanga/viz/templates/viewer.js`
