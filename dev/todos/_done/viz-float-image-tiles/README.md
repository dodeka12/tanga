# Float32 image tiles (lossless zlib) — Overview

**Created:** 2026-09-26 | **Status:** Done | **Branch:** `fix/image-display`

## Goal

Serve the tile pyramid's `float32` (and `uint16`) tiles to the browser as
lossless **zlib-compressed raw pixels** and assemble them into a float
`THREE.DataTexture`, so the image shader's `u_value_min`/`u_value_max` and
brightness/contrast operate on the **full dynamic range** instead of an 8-bit
canvas.

## Architecture (short)

- Backend `ImagePyramid.get_tile(..., "zlib")` returns zlib (RFC 1950)
  compressed source-dtype tile bytes, reusing `_image_wire.encode_zlib_raw`.
  The `/image/{id}/{level}/{x}/{y}?format=zlib` route already serves arbitrary
  formats via `FORMAT_CONTENT_TYPE` — no new route.
- Frontend `makeTiledTexture` (`renderers/image.js`) branches on `img.dtype`:
  `uint8` keeps the existing JPEG/PNG canvas path; `float32`/`uint16` fetch
  `format=zlib` tiles, inflate them (`DecompressionStream('deflate')`), expand
  to RGBA (`typedArrayFor` + `toRgba`), place them edge-clipped into a
  full-level buffer, and upload a `THREE.DataTexture` with
  `FloatType`/`RGBAFormat` — mirroring `makeDataTexture`.
- The fragment shader (`image-shader.js`) already normalizes in float
  (`(color - u_value_min) / (u_value_max - u_value_min)`) — **no shader change**.

## Decisions (confirmed)

- Tile format **`zlib`** = zlib over the raw source-dtype bytes;
  `Content-Type: application/octet-stream` (same as `raw`).  Frontend inflates
  with `DecompressionStream('deflate')` — matches the frame `codec=zlib` path.
- **Reuse** `_image_wire.encode_zlib_raw` (no duplicate zlib logic).
- Float texture: `FloatType`/`RGBAFormat`, `flipY=true`, `NearestFilter`
  magnification / `LinearFilter` minification (no float mipmaps), matching
  `makeDataTexture`'s float path.
- `uint8` tiled images keep the existing canvas path (JPEG for 1/3-channel,
  PNG for 4-channel).  The PNG float32/uint16 normalization added earlier stays
  as a direct-`get_tile(..., "png")` fallback.
- Each tile's clipped W/H = `min(tile_size, level_dim − coord·tile_size)`,
  computed client-side from the grid (matching `ImagePyramid._extract_tile`).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-backend-zlib-tile-format.md](./01-backend-zlib-tile-format.md) | Add the `zlib` tile format + backend tests |
| 2 | [02-frontend-float-tiles.md](./02-frontend-float-tiles.md) | Assemble raw float tiles into a `DataTexture` + JS tests + bundle regen |
| 3 | [03-docs-changelog.md](./03-docs-changelog.md) | Developer + user docs, changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz/test_image_pyramid.py -q`
- JS: `cd js/dev && npm test`
- Bundle drift: `uv run python tools/build-viewer-js.py --check`
- Lint/types: `uv run ruff check py/ && uv run ty check`
- Docs: `uv run mkdocs build --strict`

## Non-goals

- No change to the non-tiled (data-frame) path — it already sends lossless float.
- No shader change (normalization is already done in float).
- No server-side `Content-Encoding: gzip` (zlib is applied per tile, in-band).
- No viewport-only tile streaming (still fetch the whole best-fit level, as today).
- No change to the `uint8` tiled path.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
