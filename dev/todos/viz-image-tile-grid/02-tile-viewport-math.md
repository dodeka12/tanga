# Phase 2 — Viewport → tile math

## Goal

Add a pure helper that turns the live ortho camera into the normalized viewport
`visibleTiles` needs, so the tile grid can know which tiles are visible.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image-tiles.js`
- Edit: `js/dev/tests/image-tiles.test.mjs`

## Steps

- [ ] **2.1 — `imageViewport(frame, camera)` (`image-tiles.js`)**
  - Return `{u0, v0, u1, v1}` (0..1 image coords, v=0 at top) of the visible
    image region, or `null` when `camera` is not an orthographic 2D camera.
  - Derive the visible world rect from `camera.left/right/top/bottom`,
    `camera.zoom`, and `camera.position` (zoom shrinks the effective frustum;
    position pans it) — mirror the math already used by
    `_imageScreenLongSide`/`screenWorldScale` — then intersect with the image
    pixel rect `x ∈ [−0.5, W−0.5]`, `y ∈ [−0.5, H−0.5]` and map
    `u = (x + 0.5) / W`, `v = (H − 0.5 − y) / H`.
  - No `three`/DOM dependency.

- [ ] **2.2 — Unit tests (`image-tiles.test.mjs`)**
  - Fully-contained viewport → identity `{0,0,1,1}`.
  - A panned/zoomed frustum clips to the image rect and yields the expected
    normalized rect; a non-ortho camera returns `null`.

## Validation

```
node --test js/dev/tests/image-tiles.test.mjs
```

## Notes

- `visibleTiles`, `tileRect`, `pyramidGrid` already exist and are reused; this
  phase only adds the frustum→normalized-viewport mapping the grid will consume.
