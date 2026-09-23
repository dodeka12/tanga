# Phase 5 — Live viewer wiring

## Goal

Integrate the underlay container and the overlay/underlay renderers into
`ThreeJsView` so `grid_underlay` renders behind the transparent scene and
`axes_overlay` renders in front, both updated every frame.

## Files

- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **5.1 — per-pane layer containers**
  - In `_initScene`, create a dedicated `underlay` DOM container (absolute,
    `pointer-events:none`, z-index below the WebGL canvas) inserted before
    `renderer.domElement`; give the WebGL canvas / CSS2D canvas explicit stacking
    so the order is `underlay → renderer → labelRenderer → overlay`.
  - Add `this._gridUnderlay = null` and `this._axesOverlay = null` in the
    constructor.

- [x] **5.2 — route `grid_underlay` / `axes_overlay` in `_upsertObject`**
  - Import `AxesOverlay` (`../axes-overlay.js`) and `GridUnderlay`
    (`../grid-underlay.js`).
  - `layer === 'underlay' && kind === 'grid_underlay'` → create/replace
    `GridUnderlay`, mount into the underlay container, register a registry entry.
  - `layer === 'overlay' && kind === 'axes_overlay'` → create/replace
    `AxesOverlay`, mount into `this.el`, register a registry entry.

- [x] **5.3 — render + resize + transparency**
  - In `render()`, after `controls.update()`, call `gridUnderlay.update(...)` then
    `axesOverlay.update(...)` when present.
  - In `resize()`, update both renderers.
  - When a `grid_underlay` is present, set `scene.background = null` and
    `renderer.setClearColor(0x000000, 0)` so the underlay shows through; restore
    `applyThemeBackground()` when the underlay is removed.

- [x] **5.4 — cleanup**
  - In `_removeSceneObject` and `clearAll`, `dispose()` and null the matching
    renderer; also release them in `clearOverlays()`.

- [x] **5.5 — smoke + regression**
  - `node --check` the file; run `py/tests/viz`; browser-smoke pan/zoom with a
    2D overlay coordinate system.

## Validation

`node --check py/pytanga/viz/templates/views/three-view.js && uv run pytest py/tests/viz -q`

## Notes

- No interaction/event changes — the renderers only read the camera.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
