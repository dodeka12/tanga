# Phase 4 — Frontend `OverlayView` + `BannerView`

## Goal

Implement the two view modules that render a banner, both extending the `View`
base class.

## Steps

- [x] **4.1 — `templates/views/overlay-view.js`**
  - `OverlayView extends View`: full-screen container
    (`position: fixed; inset: 0; pointer-events: none; z-index: 500`).
  - `addChild(view)` / `removeChild(view)` mounting into `this.el` (children set
    `pointer-events: auto` themselves).

- [x] **4.2 — `templates/views/banner-view.js`**
  - `BannerView extends View`; constructor
    `{ id, title, text, align_x, align_y, auto_hide, dismissable, controls, backdropMode }`
    (`backdropMode` = `"fixed"` global | `"absolute"` per-scene).
  - Card chrome (reuse the `.tanga-control-panel` look), `pointer-events: auto`.
  - Title span; text element rendered with `marked.parse` + `renderMathInElement`
    (same delimiters as `ThreeJsView._renderAnnotation`), graceful fallback when
    `marked`/KaTeX are absent.
  - Control row: build each control via `controls-panel.js`
    `createSlider` / `createButton` / `createDropdown` (they self-wire to
    `sendControlEvent`). Buttons laid out horizontally; sliders/dropdowns
    stacked.
  - Alignment anchor: `left/top: (align*100)%` + `transform:
    translate(-(align_x*100)%, -(align_y*100)%)`.

- [x] **4.3 — Modal backdrop (`dismissable=false`)**
  - Render a full-container dimmed backdrop
    (`position: backdropMode; inset: 0; background: rgba(0,0,0,0.5);
    pointer-events: auto`) behind the card; no ✕, no click-away.

- [x] **4.4 — Dismissal / auto-hide**
  - `dismissable=true`: ✕ button + click-away on the backdrop/outside →
    `this._dismiss(notify=true)` (emits a `banner_closed` message via a provided
    `onClose` callback / module `_ws`).
  - `auto_hide=true`: capture-phase `click` / `change` listeners on the control
    row → `this._dismiss(notify=false)` (no backend notification).

- [x] **4.5 — Smoke**
  - `node --check` on the two new modules, plus the live viewer example
    `py/examples/viz/banners/banner_types.py` (every banner kind renders;
    auto-hide, ✕, and the modal backdrop behave correctly).

## Validation

`node --check` on the two new modules + open the smoke page in a browser.
