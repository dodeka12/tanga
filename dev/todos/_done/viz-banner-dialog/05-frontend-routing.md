# Phase 5 — Banner manager, routing, per-scene handling

## Goal

Wire banner messages through the viewer: a global overlay manager plus
per-scene rendering inside `ThreeJsView`.

## Steps

- [x] **5.1 — `templates/banner.js` (new)**
  - Module state: singleton `OverlayView` mounted on `document.body`; a map of
    `bannerId -> BannerView`; `_ws` set via `setWebSocket(ws)`.
  - `handleBannerDefine(msg)`, `handleBannerRemove(msg)`, `handleBannerClear()`
    (build/remove `BannerView` with `backdropMode: "fixed"`).
  - `notifyClosed(id)` → `_ws.send({ type: "banner_closed", id })`.

- [x] **5.2 — `viewer.js` routing**
  - In the message handler, before scene routing:
    `banner_define` / `banner_remove` / `banner_clear` with `msg.scene === null`
    → `banner.js` handlers, return.
  - Otherwise let them fall through to the existing `_routeToScene` (layout) /
    `_forMyScene` filter + `view.handleMessage` (single-scene).

- [x] **5.3 — `ThreeJsView` per-scene banners**
  - `this._banners: Map<id, BannerView>`; add `banner_define` /
    `banner_remove` / `banner_clear` branches in `handleMessage` (mount
    `BannerView` with `backdropMode: "absolute"` into `this.el`; share a
    `BannerView` factory with the global path).
  - `clearAll()` also clears per-scene banners.

- [x] **5.4 — `viewer.html`**
  - Add `<script type="module" src="banner.js"></script>` (and wire
    `setWebSocket` like `controls-panel.js`).

- [ ] **5.5 — Manual check**
  - Global banner over a split layout; per-scene banner appears in every pane
    of that scene; modal banner blocks the pane/scene; `banner_remove` /
    `banner_clear` hide them.

## Validation

`node --check` on touched modules + manual browser check (single-scene and
layout modes).
