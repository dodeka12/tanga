# Phase 1 — Dynamic layer count (`max_layers`, default 8)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Image canvas (extension recipe)",
> "Image background").  This phase extends the `image` entity + background
> metadata with `max_layers`; no new architecture seam.

## Goal

Replace the hard-coded `MAX_IMAGE_LAYERS = 4` with a serialized, single-source
`max_layers` value defaulting to 8, threaded from the Python model through both
the `image` entity and the background metadata into the frontend shader/uniform
builders.  No behavioral change for existing ≤4-layer callers.

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/views/_helpers.py`
- Edit: `py/pytanga/viz/templates/renderers/image-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `py/pytanga/viz/templates/renderers/image-background.js`
- Edit: `js/tanga-viewer.js` (regenerated via `tools/build-viewer-js.py`)
- Edit: `py/tests/viz/test_image_view.py`, `py/tests/viz/test_image_background.py`

## Steps

- [x] **1.1 — Python constant + `ImageView.max_layers`**
  - In `_image_view.py`, replace `MAX_IMAGE_LAYERS = 4` with
    `DEFAULT_MAX_IMAGE_LAYERS = 8` and keep `MAX_IMAGE_LAYERS =
    DEFAULT_MAX_IMAGE_LAYERS` as a backward-compat alias.
  - Add `max_layers: int = DEFAULT_MAX_IMAGE_LAYERS` to `ImageView.__init__`
    (store as `self._max_layers`, validate `>= 1`); change `add_layer` to check
    `len(self._images) >= self._max_layers` and update the error message.

- [x] **1.2 — Serialize `max_layers`**
  - Add `"max_layers": self._max_layers` to `ImageView._serialize_state()`.
  - Add `"max_layers"` to `_image_view_meta()` in `views/_helpers.py` (read
    `view.max_layers` via a new read-only `ImageView.max_layers` property).

- [x] **1.3 — Frontend shader builder takes a count**
  - In `image-shader.js`, change `buildImageLayerPipeline()` →
    `buildImageLayerPipeline(layerCount)` and loop `i < layerCount` (samplers,
    uniform decls, composite steps).

- [x] **1.4 — Frontend renderers read `max_layers`**
  - In `image.js`: `buildLayerUniforms(u, layerCount)`; `buildUniforms(ent)`
    reads `ent.max_layers ?? 8`; replace the `i < 4` loops in `createImage` and
    `updateImage` with the same count.
  - In `image-background.js`: `_buildMaterial` and `updateImageBackground` read
    `imageMeta.max_layers ?? 8` and loop to that count; build the background
    fragment via `buildImageLayerPipeline(layerCount)` instead of the `const`
    `_BG_FRAGMENT` (keep the NDC vertex shader as a const).

- [x] **1.5 — Tests**
  - Extend `test_image_view.py`: `ImageView(max_layers=8).add_layer(...)` allows
    8 layers and raises on the 9th; `_serialize()`/`_serialize_state()` emits
    `max_layers == 8`.
  - Extend `test_image_background.py`: background meta emits `max_layers == 8`.

- [x] **1.6 — Rebuild the viewer bundle**
  - Run `uv run python tools/build-viewer-js.py` and confirm `js/tanga-viewer.js`
    is regenerated without the hard-coded 4-layer loops.

## Validation

```
uv run pytest py/tests/viz/test_image_view.py py/tests/viz/test_image_background.py -q
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/image-layers.test.mjs
uv run python tools/build-viewer-js.py
```

## Notes

- The 8-layer floor is the WebGL 1 guaranteed fragment-shader texture-unit
  minimum; the frontend only reads the serialized count, so a later phase can
  switch it to `gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS)` with no wire change.
- `buildImageLayerPipeline(layerCount)` must stay exported for the JS unit tests
  (they import it) — keep the default arg `layerCount = 4` removed; callers pass
  the count explicitly.
