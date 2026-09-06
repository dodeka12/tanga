# Phase 1 — Shared `applyOrthoFrustum` helper

## Goal

Add `applyOrthoFrustum(camera, width, height)` to the pure, shared
`templates/camera-fit.js`, ported verbatim from `view_mode.js`'s private
`_applyOrthoFrustum`, and cover it with Node unit tests.

## Files

- Edit: `py/pytanga/viz/templates/camera-fit.js`
- Edit: `dev/src/js-tests/camera-fit.test.mjs`

## Steps

- [x] **1.1 — Add `applyOrthoFrustum` to `camera-fit.js`**
  - Port the body of `_applyOrthoFrustum` from `view_mode.js` (currently lines
    43–80) byte-for-byte, renaming it `applyOrthoFrustum` and exporting it.
  - Keep all three branches: stored-`_view2d` recompute, preserve-current-height
    letterbox, corrupt-frustum reset to a 10-unit-high default box.
  - No `three`/DOM references — it only reads/writes `camera.left/right/top/bottom`
    and `camera.userData`.
- [x] **1.2 — Update the module header comment**
  - Note that `applyOrthoFrustum` is a mutating helper (still `three`/DOM-free
    and Node-testable).
- [x] **1.3 — Add Node unit tests**
  - `applyOrthoFrustum` recomputes from a stored `_view2d` rect (e.g.
    `{xmin:-5,xmax:5,ymin:-5,ymax:5,uniform:true,border_px:0}` in a 200×800 pane
    → `left:-5,right:5,top:20,bottom:-20`).
  - `applyOrthoFrustum` preserves the current full height when `_view2d` is
    absent (e.g. `left:-10,right:10,top:-5,bottom:5` in a 100×100 pane →
    `left:-10,right:10,top:10,bottom:-10`).
  - `applyOrthoFrustum` resets a corrupt (NaN) frustum to the default 10-high box.

## Validation

`node --test dev/src/js-tests/camera-fit.test.mjs`

## Notes

- Function declarations are hoisted, so `applyOrthoFrustum` may call
  `finiteAspect`/`orthoFrustum` regardless of declaration order.
- Keep the optional chain `camera.userData?._view2d` so plain-object Node test
  fixtures work.
