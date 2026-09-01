# Phase 14 — Frontend single build path (`viewer.js`)

## Goal

Remove the single-scene bootstrap so the frontend always renders through the
layout tree. A single-scene URL builds identically to a layout URL.

## Files

- Edit: `py/pytanga/viz/templates/viewer.js`

## Steps

- [x] **14.1 — Always build from `view_layout`**
  - Delete the single-scene `new ThreeJsView(_myScene)` branch in `init()`; the tree
    is now built only by `_buildLayout` (which always arrives after Phase 13).

- [x] **14.2 — `_buildLayout` teardown**
  - Before building, unmount/destroy the previous `_layoutRoot` and clear
    `_sceneRoutes` / `_viewById` (also fixes a reconnect leak).

- [x] **14.3 — Unified routing**
  - Replace the `if (_layoutName !== null)` routing gate with `if (_layoutRoot !== null)`
    so every scene-scoped message routes via `_sceneRoutes`/`_routeToScene`.

- [x] **14.4 — Single-scene-only code**
  - Resolve the active `ThreeJsView` from `_sceneRoutes.get(_myScene).sceneViews[0]`
    for the Ctrl+S screenshot and the `titlechange` listener (which read the removed
    `view`).

- [x] **14.5 — Smoke**
  - Confirm a single-scene URL still renders via the layout path (manual browser
    check); update `dev/src/js-tests/` pages if any referenced the old bootstrap.

## Validation

`node --check py/pytanga/viz/templates/viewer.js`
