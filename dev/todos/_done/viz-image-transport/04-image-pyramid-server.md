# Phase 4 — Image pyramid server (tiles over HTTP)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Serve very large images as an on-demand tile pyramid at
`/image/{id}/{level}/{x}/{y}`, so the frontend can fetch only the region and
resolution it needs.  Multi-consumer is pull-based: each browser requests its
own viewport tiles, and the server caches encoded tiles.

## Files

- New: `py/pytanga/viz/_image_pyramid.py` (pyramid build + tile encode + LRU)
- Edit: `py/pytanga/viz/server.py` (register `/image/...` route + registry)
- Edit: `py/pytanga/viz/visualizer.py` (public `register_image_pyramid` / hook)
- New: `py/tests/viz/test_image_pyramid.py`

## Steps

- [x] **4.1 — `ImagePyramid` class (`_image_pyramid.py`)**
  - Holds a source numpy array (`uint8`/`uint16`/`float32`, 1/3/4 channels),
    `tile_size=256`, and computes `levels`/`tile_grid` lazily (level 0 = full
    resolution, each level halves dims).
  - `get_tile(level, x, y, format)` crops (edge-clipped) and encodes:
    `jpeg` for uint8 display, `png`/`raw` for lossless/float.  Out-of-range →
    `None`.
  - Keep the source array referenced once (no eager full pyramid copy).

- [x] **4.2 — LRU tile cache**
  - An `OrderedDict`-based LRU (bounded, e.g. 256 tiles) keyed by
    `(id, level, x, y, format)` storing the encoded bytes.

- [x] **4.3 — server route + registry**
  - `VizServer` gains `register_image_pyramid(image_id, pyramid)` and an
    aiohttp `GET /image/{image_id}/{level}/{x}/{y}` handler (registered before
    the `/{name:.*}` catch-all) that returns the encoded tile with the correct
    `Content-Type`, `404` for out-of-range, `400` for unknown id.

- [x] **4.4 — public hook**
  - `Visualizer.register_image_pyramid(image_id, data, *, tile_size=256)` stores
    the pyramid and registers the route (no-op before server boot, mirroring
    `set_background_image`).

- [x] **4.5 — tests**
  - `ImagePyramid` dims/tiling math (edge tiles, level counts), tile encode
    round-trips per format, LRU eviction, and a route smoke test against a fake
    `VizServer`/`aiohttp` test client.

## Validation

```powershell
uv run pytest py/tests/viz/test_image_pyramid.py -q
uv run ruff check py/pytanga/viz/_image_pyramid.py py/pytanga/viz/server.py
uv run ty check py/pytanga/viz/_image_pyramid.py
```

## Notes

- Reuse the Phase 1 JPEG/zlib encoders; do not duplicate encode logic.
- `ImagePyramid` is data-only (no server imports) so it stays unit-testable,
  mirroring `image.py`/`camera.py`.
- Tile `format` is chosen by the client's `?format=` (the frontend picks based
  on the dtype in Phase 5).
