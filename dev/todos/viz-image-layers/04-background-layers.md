# Phase 4 — Background layers

## Goal

Carry the full layer set through the calibrated background, and composite
multiple textures in the NDC quad.

## Files

- Edit: `py/pytanga/viz/views/_helpers.py` (`_image_view_meta` emits `images[]`)
- Edit: `py/pytanga/viz/_layout.py` (`_collect_background_frames`/`push_background_image` iterate all layers)
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `py/tests/viz/test_image_background.py`

## Steps

- [x] **4.1 — `_image_view_meta` emits `images[]`.**
  - Keep the flat primary fields (back-compat for framing/`uImageAspect`), and
    add `"images": [layer_meta(...) for each layer]` (with per-layer fields).

- [x] **4.2 — Encode/send all background layer frames.**
  - `_collect_background_frames` and `push_background_image` iterate every layer
    (not just `primary_image`); skip layers with `data is None` (url/tiled).

- [x] **4.3 — Multi-texture background quad.**
  - `image-background.js` builds `uImage0..3` (+ per-layer uniforms) and the
    default background fragment composites the layers inside the letterbox/crop
    UV block.  `updateImageBackground` resolves each layer's texture.

- [x] **4.4 — Tests.**  Multi-layer background serializes `images[]`; a tiled
  background still emits `images[]` with its tiled extras; two data layers send
  two frames.

## Validation

```
uv run pytest py/tests/viz/test_image_background.py py/tests/viz/test_image_view.py -q
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py
```
