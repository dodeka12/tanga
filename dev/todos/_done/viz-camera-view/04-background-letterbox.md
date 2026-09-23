# Phase 4 — Letterbox the NDC background quad

## Goal

Make the background image preserve aspect and letterbox (black bars), driven by
the same `pinholeFraming` `{hx, hy}` values as the projection, and update it on
pane resize.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- (build.js unchanged — the image aspect comes from `imageMeta`, the pane aspect via resize)

## Steps

- [x] **4.1 — letterbox shader**
  - Change the fragment shader to take `uImageAspect` and `uPaneAspect`, compute
    `hx/hy`, map the full-screen NDC into the contained image region, and emit
    black outside it (no geometry resize; the quad stays full-screen).

- [x] **4.2 — expose uniforms**
  - `createImageBackground(imageMeta)` sets `uImageAspect = width/height` and a
    default `uPaneAspect`; expose a way to update `uPaneAspect` (a returned mesh
    handle or a small `updateBackgroundAspect(mesh, aspect)`).

- [x] **4.3 — resize wiring**
  - In `ThreeJsView`, store the background mesh's material and update
    `uPaneAspect` from the pane size in `handleResize`/`resize`.

## Validation

`node --check py/pytanga/viz/templates/renderers/image-background.js py/pytanga/viz/templates/views/three-view.js && uv run python tools/build-viewer-js.py --check`

## Notes

- `fit === "fill"` yields `hx=hy=1` (the old full-stretch behaviour), so the
  shader also covers the fill case; the camera config's `fit` decides.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
