# Phase 5 — Wire the grid into the `background_image`

## Goal

Use the tile grid for a tiled background image (single tiled layer), driven by
the live crop window, so panning the calibrated pane loads newly-visible tiles.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Regenerate: `js/tanga-viewer.js`

## Steps

- [ ] **5.1 — Grid in `createImageBackground` (`image-background.js`)**
  - For a single tiled background, build a `THREE.Group` of tile quads positioned
    in the letterboxed NDC space (from `uCrop`/`uHx`/`uHy`) with the same
    per-tile material, instead of the NDC quad sampling one full-level texture.
  - Keep the existing NDC-quad path for non-tiled backgrounds and the multi-layer
    fallback.

- [ ] **5.2 — Crop/letterbox plumbing**
  - On `setBackgroundCrop`/`setBackgroundLetterbox`/`setBackgroundAspect`, also
    notify the grid so tile quads reposition; the grid's `update` reads the
    current `uCrop` as its viewport.

- [ ] **5.3 — Per-frame update (`three-view.js`)**
  - In `_updateBackgroundLod`, when `_backgroundMesh.userData._tileGrid` exists,
    compute `maxDim` (existing `_backgroundScreenLongSide`) and the viewport from
    `uCrop` and call `grid.update(maxDim, viewport)`; keep the old
    `updateImageLod` path for the fallback case.

## Validation

```
node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run pytest py/tests/viz/test_image_background.py -q
```

## Notes

- The `huge_image_background.py` example exercises this path (the motivating
  case for per-tile streaming); a manual smoke run should show new tile loads on
  pan at the same zoom.
