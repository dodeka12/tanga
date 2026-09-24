# Phase 5 — Tiled ImageView / background (frontend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Let the frontend display a tiled image by requesting only the tiles intersecting
the current viewport (with a one-tile border and slight over-resolution), so
zoom/pan don't require immediate retransmission.

## Files

- New: `py/pytanga/viz/templates/renderers/image-tiles.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/pytanga/viz/views/scene_view.py` (serialize a tiled `source`/meta)
- New: `py/tests/viz/test_image_pyramid.py` (extend for the serialized meta)
- New: `js/dev/tests/*.test.mjs` (tile-range math)

## Steps

- [x] **5.1 — serialized tiled meta (Python)**
  - `ImageData`/`ImageView` serialize a new source kind (`source: "tiled"`) with
    `{id, width, height, tile_size, levels, dtype, channels}` so the frontend
    knows the pyramid without transferring pixels.

- [x] **5.2 — tile-range math (`image-tiles.js`, Node-testable)**
  - Pure function `visibleTiles(viewport, pyramid, border)` → the set of
    `{level, x, y}` tiles covering the pane (pick level so one tile ≈ one screen
    px, clamp border to grid, over-fetch one tile margin).

- [x] **5.3 — tiled texture manager**
  - Maintain a small `Map` of loaded `THREE.Texture`s keyed by `(level,x,y)`;
    fetch missing tiles via `fetch('/image/...')` + `createImageBitmap`; drop
    tiles outside the viewport; show a lower level while higher levels load
    (progressive).
  - Compose tiles into a single display quad via a shader or a per-tile mesh
    grid (prefer one shader sampling a tile atlas; fall back to a `Group` of
    tile meshes).

- [x] **5.4 — wire into `image.js` / `image-background.js`**
  - When `source === "tiled"`, build the tiled renderer instead of
    `makeDataTexture`; update tiles on camera/viewport change (hook the existing
    resize + viewport-navigation events).

- [x] **5.5 — tests**
  - Node test for `visibleTiles` (border, level selection, clamping); Python
    test for the `source: "tiled"` serialization shape.

## Validation

```powershell
node --test 'js/dev/tests/*.test.mjs'
node js/dev/tests/check-syntax.mjs
uv run pytest py/tests/viz -q
```

## Notes

- The backend route (Phase 4) is a prerequisite; this phase consumes it.
- Multi-consumer is inherent: each browser fetches its own tiles; the server LRU
  makes shared views cheap.
