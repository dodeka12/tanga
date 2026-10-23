# Viewport-based tiled image streaming (mesh grid) — Overview

**Created:** 2026-10-23 | **Status:** Planned | **Branch:** `fix/image-loading`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Image canvas (extension recipe)" and "Calibrated camera view (extension
> recipe)" sections — and `docs/dev/architecture/viz-controls-and-interactions.md`
> — the "Image load events" section).  This work **changes** the documented
> frontend image-rendering contract (one full-level texture per tiled layer →
> a grid of per-tile quads) and **extends** the image-event wire contract
> (per-tile `tile_x`/`tile_y`), so the developer docs must be updated in Phase 6.

## Goal

Replace the current "compose the whole pyramid level into one texture" behaviour
with **viewport-based, per-tile streaming**: only the tiles that intersect the
current view (plus a one-tile border) are fetched and drawn, as a mesh grid of
per-tile quads.  Panning at the same LOD now fetches newly-visible tiles, and
each new tile fetch/arrival emits an `image_tile_load` / `image_tile_loaded`
event the backend can react to.

## Architecture (short)

- **Pure math** stays in `renderers/image-tiles.js` (`levelForScreen` with the
  hysteresis added earlier, `visibleTiles`, `tileRect`, `pyramidGrid`); a new
  pure `imageViewport` helper maps the ortho frustum to a normalized viewport.
- **New `renderers/image-tile-grid.js`** holds the per-tile texture/mesh cache
  and the per-frame `update(maxDim, viewport)` loop (fetch missing visible
  tiles, drop off-screen ones, emit per-tile events).
- **Renderers** (`image.js`, `image-background.js`) build a `THREE.Group` of
  tile quads for a `source === "tiled"` layer instead of one full-level texture.
- **Per-frame hook** in `views/three-view.js` replaces the current
  `updateImageLod`/`_updateBackgroundLod` calls with the grid's `update()`,
  keyed on the live viewport (so panning triggers fetches).

## Fixed contract (decided up front)

### Tile grid (frontend)

- Cache key `"level,x,y"` → `{ texture, mesh }` per tiled layer.
- `update(maxDim, viewport)` each frame:
  1. `level = levelForScreen(img, maxDim, currentLevel)` (existing hysteresis).
  2. If `level` changed, dispose all tiles and rebuild at the new level.
  3. `tiles = visibleTiles(viewport, img, level, border = 1)`.
  4. For each tile not yet cached: create/position its mesh, start the fetch
     (emit `image_tile_load`), attach the texture when ready (emit
     `image_tile_loaded`).
  5. Dispose tiles that left the visible set.
- Tile mesh: `PlaneGeometry(tileW, tileH)` (edge-clipped via `tileRect`),
  positioned in the image plane's pixel frame `[−0.5, W−0.5] × [−0.5, H−0.5]`
  (image entity) or in the letterboxed NDC space (background).
- Per-tile material: a `ShaderMaterial` that runs the existing single-layer
  color pipeline (`buildImageLayerPipeline(1)` → `tangaSampleLayer` +
  brightness/contrast/colormap) with `uImage0` = that tile's texture and the
  layer-0/color uniforms copied from the parent entity/background.

### Per-tile event contract (extends the current `image_status` channel)

- `image_tile_load` / `image_tile_loaded` now fire **per tile** (not per level);
  the payload adds `tile_x`, `tile_y` (int, 0-based tile coords at `level`),
  alongside `image_id`, `source`, `width`, `height`, `level`, `tile_version`.
- `image_loaded` fires once when the first visible frame is displayable.
- Backend `ImageStatusRecord` gains `tile_x: int | None = None`,
  `tile_y: int | None = None`; `ImageStatus.handle_event` parses them.
- `ImageStatusHandler` alias is unchanged (`(ImageStatusRecord, ControlEvent)`).

### Pure helpers

- `imageViewport(frame, camera)` → normalized `{u0, v0, u1, v1}` (v=0 top) of
  the visible image region, from the ortho frustum (`left/right/top/bottom` +
  `zoom` + `position`) intersected with the image pixel rect; `null` for a
  non-ortho camera.  Node-testable, no `three`/DOM import.
- Reuse `visibleTiles`, `tileRect`, `pyramidGrid` as-is.

## Decisions (confirmed)

- **Mesh-grid** (per-tile quads), not a tile atlas.
- **Single tiled layer only** — the common case (`huge_image.py`,
  `huge_image_background.py`).  Multi-layer images where a tiled layer must
  composite with other layers in one pass keep the current whole-level
  composition (documented non-goal).
- **Per-tile events** with `tile_x`/`tile_y` (not a per-batch event).
- **`border = 1`** for pan headroom (matches the original `viz-image-transport`
  design).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-tile-event-contract.md](./01-tile-event-contract.md) | `ImageStatusRecord.tile_x/tile_y` + parsing + tests |
| 2 | [02-tile-viewport-math.md](./02-tile-viewport-math.md) | `imageViewport` helper + tests |
| 3 | [03-tiled-grid-manager.md](./03-tiled-grid-manager.md) | `image-tile-grid.js` cache + per-tile material + events |
| 4 | [04-image-entity-wiring.md](./04-image-entity-wiring.md) | wire grid into `image.js` + `three-view.js` |
| 5 | [05-background-wiring.md](./05-background-wiring.md) | wire grid into `image-background.js` + `three-view.js` |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | developer docs + examples + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` and `uv run ty check` — lint + type gates.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests (viewport math, tile grid).
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle.
- `uv run python tools/generate-example-docs.py` — example docs (Phase 6).
- `uv run mkdocs build --strict` — docs gate (Phase 6).

## Non-goals

- No multi-layer compositing where a tiled layer blends with other image layers
  in a single fragment pass (keeps the current whole-level path).
- No tile atlas (single-texture batching) — deferred optimization.
- No server-side change: the per-tile HTTP route + `ImagePyramid` LRU already
  exist and are unchanged.
- No change to the `image_loaded` "first frame" semantics beyond firing once for
  the initial visible tile set.

