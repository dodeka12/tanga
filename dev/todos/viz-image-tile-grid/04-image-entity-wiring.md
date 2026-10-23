# Phase 4 — Wire the grid into the `image` entity

## Goal

Use the tile grid for a tiled scene-plane image (single tiled layer), and drive
it from the live ortho viewport each frame.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Regenerate: `js/tanga-viewer.js`

## Steps

- [ ] **4.1 — Build the grid in `createImage` (`image.js`)**
  - For a single tiled layer (no other image layers), build a `THREE.Group` with
    a `TiledImageGrid` stored on `group.userData._tileGrid` instead of a
    full-level `uImage0` texture.
  - Keep the existing plane mesh path for non-tiled images and for multi-layer
    images that include a tiled layer (whole-level fallback).

- [ ] **4.2 — Uniform/style patches reach the grid**
  - Update `updateImage` / `applyImageUniforms` to forward per-layer/color
    uniform patches to the grid's `applyUniforms(patch)` when `_tileGrid` is
    present, otherwise to the existing material.

- [ ] **4.3 — Per-frame update (`three-view.js`)**
  - In `_updateImageLod`, when `entry.mesh.userData._tileGrid` exists, compute
    `maxDim` (existing `_imageScreenLongSide`) and the normalized viewport
    (`imageViewport(entry.data.frame, this.camera)`) and call
    `grid.update(maxDim, viewport)`; keep the old `updateImageLod` path for the
    fallback case.
  - Keep the hysteresis/generation behaviour from the earlier work inside the
    grid.

- [ ] **4.4 — Removal/transform compatibility**
  - Confirm `removeEntityMesh` (traverse-dispose) and `wrapWithNodeTransform`
    (Group/Object3D) already handle a `THREE.Group`; tag the group with
    `tagEntity` so click detection/visibility still work.

## Validation

```
node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run pytest py/tests/viz/test_image.py py/tests/viz/test_image_view.py -q
```

## Notes

- The `huge_image.py` / `image_canvas.py` examples exercise this path; a manual
  smoke run (zoom in + pan) should show per-tile loads in the browser console.
