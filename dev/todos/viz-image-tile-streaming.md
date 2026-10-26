# Image tile streaming (viewport-based) — rough plan / notes

**Created:** 2026-10-26 | **Status:** Planned (rough) | **Branch:** `fix/image-lod-oscillation`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (image canvas + calibrated camera
> view) and `docs/dev/architecture/viz-controls-and-interactions.md` (image load
> events).  This file is a **rough** note — it records the intended fix and the
> open multi-layer problem, but is **not** a phased implementation plan.

## Why this exists

The frontend composes a whole pyramid level into one texture.  At level 0 a huge
image has hundreds of tiles, and `makeTiledDataTexture` / `makeTiledCanvasTexture`
fetch them all in a single `Promise.all` — flooding the browser + server, so
requests abort (`status: 0`) and the level never loads.

- **Stop-gap (done):** fetch the full level in small batches
  (`_TILE_FETCH_CONCURRENCY = 8`) so a full level eventually completes.
- **Real fix (below):** fetch only the tiles that are actually visible.

## The real fix (intent only)

Replace whole-level composition with **viewport-based per-tile streaming**:

- Per-layer cache of tile textures/meshes keyed by `level,x,y`.
- Each frame, derive the normalized viewport (ortho frustum for the image
  entity; the background `uCrop`) and compute the visible tile set via
  `visibleTiles(viewport, pyramid, level, border = 1)`.
- Fetch only missing visible tiles (batched), attach their quads, dispose tiles
  that left the view.
- **Mesh-grid** approach: one `PlaneGeometry` quad per tile, each sampling its
  own tile texture through the existing single-layer color pipeline
  (`tangaSampleLayer` + brightness/contrast/colormap).
- Emit per-tile `image_tile_load` / `image_tile_loaded` events (add `tile_x` /
  `tile_y` to `ImageStatusRecord`).

## Open problem: multi-layer

The current shader composites every layer in **one fragment pass**: one
`uImage{i}` sampler per layer, sampled with the primary frame's UV, with
per-layer `add` / `multiply` / `screen` blend done in GLSL (`tangaBlend`).  A
mesh-grid tiled layer cannot be sampled as a single `uImage{i}` texture, which
is exactly why per-tile streaming is hard for multi-layer images:

- A tiled layer becomes N tile quads (N textures), not one texture.
- There is no single fragment pass that samples both "one texture" (non-tiled
  layer) and "many tile textures" (tiled layer) while preserving exact
  per-layer blend modes.
- Rendering each layer as its own quad/grid stack and relying on GPU alpha
  blending loses exact `add` / `multiply` / `screen` (they are not standard
  alpha-blend modes).
- A full-screen composite pass that re-samples the tile grid could preserve the
  blend modes, but adds a render target and an extra pass.

**Working decision:** scope the real fix to the **single-tiled-layer** case (the
common one).  Multi-layer images where a tiled layer must blend with other
layers keep the current whole-level path.  A multi-layer solution is **not**
planned yet.

## Non-goals (for now)

- No multi-layer compositing where a tiled layer blends with other layers
  (exact `add`/`multiply`/`screen`).
- No tile atlas (single-texture batching) — deferred.
