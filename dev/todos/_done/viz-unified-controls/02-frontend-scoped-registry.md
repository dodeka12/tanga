# Phase 2 — Frontend: owner-scoped control registry

## Goal

Stop `controls_define`/`controls_clear` from wiping layout/banner control
registry entries (the `registry-reset` bug). Tag each registry entry with its
owner and scope the teardown.

## Files

- Edit: `py/pytanga/viz/templates/controls-panel.js`
- Edit: `py/pytanga/viz/templates/views/*-view.js` (render call sites)
- New/Edit: `dev/src/js-tests/*` (new registry unit test)

## Steps

- [x] **2.1 — Tag registry entries**
  - `_controlRegistry[id] = { owner, scene, kind, apply }` where
    `owner ∈ {"panel", "attached", "layout", "banner"}`.
  - `createX` factories take an optional `{ owner, scene }` (default `"panel"`);
    layout view `render()` and banner rendering pass `"layout"` / `"banner"`.

- [x] **2.2 — Scope `_destroyAll` / `handleControlsClear`**
  - `_destroyAll({ owner = "panel", scene = null })` removes only matching
    entries; `handleControlsDefine`/`handleControlsClear` call it with the panel
    scope so layout/banner entries survive.

- [x] **2.3 — `applyControlValue` resolves by id**
  - Keep the single id lookup; add a missing-entry guard + debug log. No owner
    discrimination needed for application.

- [x] **2.4 — Tests**
  - Add a `node:test` unit (stub DOM) asserting `_destroyAll` for panel scope
    leaves a layout-scope entry intact, and `applyControlValue` still applies it.
  - Re-check `control-view-smoke.html` / `control-group-view-smoke.html`.

## Validation

`node --test dev/src/js-tests/*.test.mjs`

## Notes

- Follow-up within this phase (if scope allows): make `handleControlsDefine`
  *diff* by id (upsert/remove) instead of `_destroyAll`+rebuild, to preserve
  collapse/drag/focus state. If too large, split into its own step and keep
  scope-delete as the minimal fix.
