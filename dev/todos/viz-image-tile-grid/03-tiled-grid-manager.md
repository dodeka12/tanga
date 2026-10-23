# Phase 3 — Per-tile grid manager (`image-tile-grid.js`)

## Goal

Build the mesh-grid engine: a per-layer cache of tile textures + meshes, the
per-frame update loop, single-tile fetching, and per-tile events.

## Files

- New: `py/pytanga/viz/templates/renderers/image-tile-grid.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js` (extract single-tile fetch)
- Regenerate: `js/tanga-viewer.js`

## Steps

- [ ] **3.1 — Extract single-tile fetch (`image.js`)**
  - Pull the per-tile work out of `makeTiledCanvasTexture` /
    `makeTiledDataTexture` into `fetchTileTexture(img, level, x, y)` returning a
    `CanvasTexture` (uint8) or `DataTexture` (float) for one edge-clipped tile.
  - Keep `buildTiledTextureAtLevel` as the whole-level fallback (multi-layer
    non-goal), now composed from `fetchTileTexture` or left as-is.

- [ ] **3.2 — `TiledImageGrid` class (`image-tile-grid.js`)**
  - State: `Map("level,x,y" → { texture, mesh })`, `img`, `level`, shared
    per-layer uniforms.
  - `update(maxDim, viewport)` per the README contract (hysteresis level pick,
    reset on level change, `visibleTiles(viewport, img, level, 1)`, diff-based
    add/prune).
  - Position each tile mesh with `tileRect` in the image plane's pixel frame.
  - `dispose()` frees textures/geometries/materials.

- [ ] **3.3 — Per-tile material**
  - Build a `ShaderMaterial` from `buildImageLayerPipeline(1)` +
    `buildImageVertex()`, with `uImage0` = the tile texture and the
    `u_layer0_*` / `u_brightness` / `u_contrast` / `u_midpoint` uniforms copied
    from the parent; expose `applyUniforms(patch)` that writes all tile
    materials (for `image_update` patches).

- [ ] **3.4 — Per-tile events**
  - Emit `image_tile_load` right before `fetchTileTexture` and
    `image_tile_loaded` once the tile mesh is added, with `tile_x`/`tile_y` in
    the payload (via `sendImageEvent`).

## Validation

```
node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run python tools/build-viewer-js.py --check
```

## Notes

- This module is renderer-agnostic (no scene/background specifics); Phases 4 and
  5 wire it in and provide the viewport.
- Keep the manager `three`-dependent but DOM-independent (no `document`), so it
  stays bundle-safe like the other renderers.
