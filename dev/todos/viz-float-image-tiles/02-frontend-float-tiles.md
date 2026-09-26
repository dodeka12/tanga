# Phase 2 — Frontend: assemble float tiles into a `DataTexture`

## Goal

For `float32`/`uint16` tiled images, fetch `format=zlib` tiles, inflate, expand
to RGBA, place them edge-clipped into a full-level `Float32Array`, and upload a
`FloatType` `DataTexture` — instead of drawing into an 8-bit canvas.

## Files

- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-tiles.js` (pure helper)
- Edit: `js/dev/tests/image-tiles.test.mjs`
- Regenerate: `js/tanga-viewer.js` (via `tools/build-viewer-js.py`)

## Steps

- [x] **2.1 — pure `tileRect` helper**
  - In `image-tiles.js`, add `tileRect(pyramid, level, x, y)` returning
    `{ x0, y0, w, h }` — pixel offset + clipped size within the level, matching
    `ImagePyramid._extract_tile`: `x0 = x·tile_size`, `y0 = y·tile_size`,
    `w = min(tile_size, levelW − x·tile_size)`,
    `h = min(tile_size, levelH − y·tile_size)`.
  - Add Node unit tests for an interior tile and an edge tile.

- [x] **2.2 — `makeTiledDataTexture` + dispatch**
  - In `image.js`, add `makeTiledDataTexture(img)` that, for `dtype` 1/2:
    computes `level`/`levelW`/`levelH`/`cols`/`rows`, allocates
    `Float32Array(levelW · levelH · 4)`, fetches each
    `/image/{id}/{level}/{x}/{y}?format=zlib`, inflates via
    `DecompressionStream('deflate')`, expands via `typedArrayFor`+`toRgba`, and
    copies each tile into the buffer at its `tileRect` offset (row-major).
  - Build `THREE.DataTexture(data, levelW, levelH, RGBAFormat, FloatType)` with
    `flipY = true`, `magFilter = NearestFilter`, `minFilter = LinearFilter`,
    `needsUpdate = true` (no float mipmaps).
  - In `makeTiledTexture`, branch: `dtype` 1/2 → `makeTiledDataTexture(img)`;
    else the existing canvas path.

- [x] **2.3 — regenerate the bundle**
  - Run `uv run python tools/build-viewer-js.py` to rebuild `js/tanga-viewer.js`.

## Validation

```
cd js/dev && npm test
uv run python tools/build-viewer-js.py --check
```

## Notes

- Reuse the existing `typedArrayFor` (dtype → typed array) and `toRgba`
  (1/3/4-channel → RGBA, uint16 widened to float32); do not reimplement them.
- `flipY = true` keeps row 0 at the top, aligning with the canvas/stream/URL
  paths (same as `makeDataTexture`).
- Still fetch the whole best-fit level (not viewport-only) — a non-goal.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
