# Phase 0 — Harmonize image-layer serialization

> **Architecture note** — see `docs/dev/architecture/viz-architecture.md`
> ("Image canvas" / "Image background").  This phase only reshapes the
> serialized per-image dict; no behavior change to rendering.

## Goal

One canonical per-image serialization used by the canvas `image` entity and the
background metadata, with a disambiguated `version` (uuid) vs `tile_version`
(pyramid cache key).  `data`/`url`/`tiled` layers serialize with the same base
keys and differ only by additive extras.

## Files

- Edit: `py/pytanga/viz/image.py` (add `ImageData.layer_meta()`)
- Edit: `py/pytanga/viz/_image_pyramid.py` (`meta()` → `tile_version`)
- Edit: `py/pytanga/viz/_image_view.py` (`_serialize_image` uses `layer_meta()`)
- Edit: `py/pytanga/viz/views/_helpers.py` (`_image_meta`/`_image_view_meta` use `layer_meta()`)
- Edit: `py/pytanga/viz/templates/renderers/image.js` (tile URL `tile_version`)
- Edit: `py/tests/viz/test_image_pyramid.py`, `py/tests/viz/test_image_view.py`, `py/tests/viz/test_image_background.py`

## Steps

- [x] **0.1 — `ImagePyramid.meta()` emits `tile_version`, not `version`.**
  - Rename the cache-key field `"version"` → `"tile_version"` in `meta()`.

- [x] **0.2 — Frontend tile URL reads `tile_version`.**
  - In `renderers/image.js`, the two tile fetches use `img.tile_version ?? 0`
    instead of `img.version ?? 0`.

- [x] **0.3 — Add `ImageData.layer_meta()`.**
  - Emit the canonical base `{id, width, height, channels, dtype, source,
    version}` (assert dtype is set), add `url` for `source == "url"`, and add
    `tile_size`, `levels`, `tile_version` for `source == "tiled"` (from
    `self.tiled.meta()`).
  - No per-layer compositing fields yet (Phase 1 adds them).

- [x] **0.4 — Route both serializers through `layer_meta()`.**
  - `ImageView._serialize_image` returns `image.layer_meta()` (drop the verbatim
    `tiled_meta` branch).
  - `views/_helpers._image_meta` returns `image.layer_meta()`; `_image_view_meta`
    builds its primary meta from `primary.layer_meta()`.

- [x] **0.5 — Tests.**
  - `test_image_pyramid.py::test_image_data_tiled_meta`: assert `tile_version == 0`
    and `version == img.version`.
  - Add assertions that a `data`, `url`, and `tiled` `ImageData` all serialize
    with the same base keys (id/width/height/channels/dtype/source/version).
  - `test_image_view.py` / `test_image_background.py`: confirm the `image` entity
    and background metadata still serialize correctly (now with `version`).

## Validation

```
uv run pytest py/tests/viz/test_image_pyramid.py py/tests/viz/test_image_view.py py/tests/viz/test_image_background.py -q
node js/dev/tests/check-syntax.mjs
uv run python tools/build-viewer-js.py --check
```
