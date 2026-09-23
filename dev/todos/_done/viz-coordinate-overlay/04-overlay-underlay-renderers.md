# Phase 4 — Overlay + underlay renderers

## Goal

Two per-pane renderers: `axes-overlay.js` draws the fixed frame (SVG/DOM, overlay
layer) and `grid-underlay.js` draws the background grid (SVG, underlay layer),
both using the Phase-3 math and the live camera.

## Files

- New: `py/pytanga/viz/templates/axes-overlay.js`
- New: `py/pytanga/viz/templates/grid-underlay.js`

## Steps

- [x] **4.1 — `axes-overlay.js` (SVG frame)**
  - `class AxesOverlay { constructor(spec) }` importing `nice-ticks.js` and
    `axes-overlay-math.js`.
  - `mount(container)`: create an absolutely-positioned `<svg>` (or a DOM root)
    with `pointer-events:none`, z-index above the CSS2D label canvas.
  - `update(camera, width, height, dpr)`: read ortho params → `visibleWorldRect`
    → `worldToData` → `ticksAndGrid`, then draw axis lines, tick marks, value
    labels, and name labels (SVG `<text>`, honoring `LabelStyle` font/color/align/
    offset/rotation) inside the `border_px` margin.
  - `setSpec(spec)` / `dispose()`.

- [x] **4.2 — `grid-underlay.js` (SVG grid)**
  - `class GridUnderlay { constructor(spec) }`, same math imports.
  - `mount(container)`: an absolutely-positioned `<svg>` inserted *before* the
    WebGL canvas (underlay), `pointer-events:none`, fills the theme `--tanga-bg`
    background.
  - `update(camera, width, height, dpr)`: draw grid lines at `xGridPx`/`yGridPx`
    using `spec.grid` color/opacity/line_thickness, clipped to the `border_px`
    plot area; omit when `spec.grid` is absent.

- [x] **4.3 — syntax + smoke**
  - `node --check` both modules; browser-smoke a 2D overlay coordinate system and
    confirm the frame stays fixed while the grid + tick values track pan/zoom.

## Validation

`node --check py/pytanga/viz/templates/axes-overlay.js && node --check py/pytanga/viz/templates/grid-underlay.js`

## Notes

- Keep both files thin: numeric decisions live in `axes-overlay-math.js` /
  `nice-ticks.js`; these files only do SVG drawing + camera param extraction.
- SVG text avoids the canvas-crispness issue and reuses overlay DOM/theme tooling;
  switch the grid to `<canvas>` later only if many-lines perf requires it.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
