# Phase 4 — Frontend emit points + bundle rebuild

## Goal

Emit `image_loaded`, `image_tile_load`, and `image_tile_loaded` from the image
renderers, and keep the committed viewer bundle valid (the renderers are also
bundled for offline/export HTML).

## Files

- Edit: `py/pytanga/viz/templates/events.js`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Regenerate: `js/tanga-viewer.js`

## Steps

- [x] **4.1 — `sendImageEvent` helper (`events.js`)**
  - Add `export const IMAGE_STATUS_ID = 'image_status';` (next to
    `CLIENT_LOG_ID`).
  - Add `export function sendImageEvent(event, data = {}) { sendEvent(
    IMAGE_STATUS_ID, event, data); }` (mirrors `sendLog`).

- [x] **4.2 — Export-bootstrap no-op stubs (`_bootstrap/_html.py`)**
  - In `generate_library_js`, extend the `"function sendLog() {}\nfunction
    sendEvent() {}"` stub string with `const IMAGE_STATUS_ID = 'image_status';`
    and `function sendImageEvent() {}`, so bundled renderers that call
    `sendImageEvent` (import stripped) still run in offline/export HTML.

- [x] **4.3 — Emit from `image.js`**
  - Import `sendImageEvent` from `../events.js`.
  - `createImage`:
    - `url` (non-stream): in `TextureLoader.load` success callback, emit
      `image_loaded` with `{ image_id: img.id, source: 'url', width, height }`.
    - `tiled`: emit `image_tile_load` before `buildTiledTextureAtLevel`, then
      `image_tile_loaded` **and** `image_loaded` after the texture is assigned.
    - `hasImageFrame` branch: emit `image_loaded` after the texture is assigned.
    - `registerImageFrameConsumer` callback: emit `image_loaded` after the
      texture is assigned.
  - `updateImageLod`: emit `image_tile_load` right after a new level fetch is
    started (captured generation), and `image_tile_loaded` right after
    `layer.level = level` (the swap).  Do **not** emit on the no-op/cancel paths.

- [x] **4.4 — Emit from `image-background.js`**
  - Import `sendImageEvent` from `../events.js`.
  - `_bindLayerTexture`: for `tiled`, emit `image_tile_load` before
    `buildTiledTextureAtLevel`, then `image_tile_loaded` **and** `image_loaded`
    in the `.then` after the texture is assigned.
  - For url/data: emit `image_loaded` where the texture first resolves non-null
    (`_backgroundTexture` url success, and the `_backgroundTexture(...).then(tex)`
    data path / consumer callback in `_bindLayerTexture`).

- [x] **4.5 — Rebuild the bundle**
  - Run `uv run python tools/build-viewer-js.py` (regenerates
    `js/tanga-viewer.js` + manifest from the edited templates and `_bootstrap`).

## Validation

```
node js/dev/tests/check-syntax.mjs && uv run python tools/build-viewer-js.py && uv run python tools/build-viewer-js.py --check
```

## Notes

- `sendEvent` already no-ops when the socket is closed; `sendImageEvent` inherits
  that.  In offline/export HTML the bootstrap stub makes `sendImageEvent` a no-op.
- Keep payload integer fields (`width`, `height`, `level`, `tile_version`) as
  integers; `image_loaded` omits `level`/`tile_version`.
- The `image_tile_*` emits must be tied to an actual new-level fetch/swap so the
  event stream stays clean (Phase 1 hysteresis removes the boundary spam).
