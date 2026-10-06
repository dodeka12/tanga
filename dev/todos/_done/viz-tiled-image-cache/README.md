# Viz tiled-image cache — Overview

**Created:** 2026-09-28 | **Status:** Done | **Branch:** `fix/viz-tiled-image-cache`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Fix **Issue D**: swapping a large (auto-tiled) `CameraView.background_image`
under a reused `image_id` silently keeps showing the previous image, because the
tile HTTP responses are browser-cached (`Cache-Control: public, max-age=3600`)
and the tile URL is keyed only by `image_id`. Add a **version** to the tile URL
so a freshly registered pyramid gets fresh URLs, and stop browser-caching tiles
as a belt-and-suspenders fallback.

## Architecture (short)

- `ImagePyramid` gains a `version: int` (default `0`), emitted in `meta()`.
- `Visualizer._register_pyramid` stamps `pyramid.version` from a per-`image_id`
  counter (`self._image_versions`), so every re-registration of the same id
  bumps it. This covers `set_layout`/`add_layout` (via
  `_register_background_pyramids`), `set_background_image`, `ImageCanvas._sync_image`,
  and the public `register_image_pyramid` — all funnel through `_register_pyramid`.
- The tile route becomes `/image/{image_id}/{version}/{level}/{x}/{y}`; the
  handler serves by `image_id` (the `version` is a pure cache key) and returns
  `Cache-Control: no-store`.
- The frontend builds tile URLs with the version from the serialized tiled meta.

### Fixed wire/API contract (do not change across phases)

1. Tiled meta (`ImagePyramid.meta()` → `_image_meta` → the serialized
   `background_image` / `image.images[]`) gains one field:

   ```json
   { "id": "camera", "width": 4056, "height": 3040, "tile_size": 256,
     "levels": 13, "dtype": 0, "channels": 3, "source": "tiled",
     "version": 2 }
   ```

2. Tile URL: `/image/{id}/{version}/{level}/{x}/{y}?format=jpeg|png|raw|zlib`.
   `version` is a monotonically increasing per-`image_id` integer, bumped on
   every `_register_pyramid` call for that id.

3. `ImagePyramid.version` defaults to `0` for a standalone pyramid; the
   `Visualizer` assigns the real value on registration. Direct
   `VizServer.register_image_pyramid` callers (tests) keep `version=0` and still
   serve correctly because the route serves by id.

## Decisions (confirmed)

- **URL shape = path segment** — `/image/{id}/{version}/{level}/{x}/{y}`.
- **Also set `Cache-Control: no-store`** on tile responses (defense-in-depth).
- **Version = monotonic counter per `image_id`** (not a data hash) — O(1) and no
  hashing of multi-MB arrays; content-addressing was considered and rejected.
- **Server serves by id and ignores the version value** (version is a cache key,
  not a staleness/auth check).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-python-version-model.md](./01-python-version-model.md) | `ImagePyramid.version` + `meta()` + per-id counter in `Visualizer` |
| 2 | [02-server-route-version.md](./02-server-route-version.md) | versioned route + `no-store` + route tests |
| 3 | [03-frontend-version-url.md](./03-frontend-version-url.md) | frontend tile URL + export bundle rebuild |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | docs + changelog |

## Testing as you go

```bash
uv run pytest py/tests/viz/test_image_pyramid.py -q   # phase 1 & 2
uv run pytest py/tests/viz -q                         # full viz suite
cd js/dev && npm run check                            # JS syntax over templates + tests
uv run python tools/build-viewer-js.py --check        # export bundle drift gate
uv run mkdocs build --strict                          # docs (phase 4)
```

> Note: the live frontend (`templates/`) is served directly as ES modules;
> `build-viewer-js.py` bundles the export renderer library (`js/tanga-viewer.js`)
> and must be rebuilt after `image.js` changes.

## Non-goals

- No content-addressable versions (data hashing).
- No server-side staleness rejection (the `version` value is ignored by the route).
- No change to the binary-frame `source: "data"` path.
- No change to the `_camera_stream` MJPEG path.
