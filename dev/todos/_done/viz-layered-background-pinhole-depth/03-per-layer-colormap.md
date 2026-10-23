# Phase 3 — Per-layer colormap + RGBA alpha compositing

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` ("Image canvas (extension recipe)",
> "Image background") for the shared layer-shader contract.  This phase extends
> the `image` layer shader only.

## Goal

Verify and fix 4-channel RGBA alpha compositing (texture alpha must modulate the
layer opacity), and add an optional built-in per-layer colormap (gray/viridis/
turbo) for scalar (1-channel/magnitude/alpha) layers, reusing the `DepthColormap`
palette math.

## Files

- Edit: `py/pytanga/viz/image.py`
- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/templates/renderers/image-shader.js`
- Edit: `py/pytanga/viz/templates/renderers/image.js`
- Edit: `js/tanga-viewer.js` (regenerated)
- Edit: `py/tests/viz/test_image_layer_style.py` (+ JS `image-layers.test.mjs`)

## Steps

- [x] **3.1 — `ImageColormap` enum + `ImageLayerStyle.colormap`**
  - Add `ImageColormap` to `image.py` (`GRAY=0`, `VIRIDIS=1`, `TURBO=2`) with
    `from_str`; export from `py/pytanga/viz/__init__.py`.
  - Add `colormap: ImageColormap | str | None = None` to `ImageLayerStyle`;
    coerce strings in `__post_init__`.

- [x] **3.2 — Uniform seeding + serialization**
  - In `_image_view.py` `_apply_layer_style` / `_merge_layer_style`, seed/merge
    `u_layer{i}_colormap` (default `0`).
  - In `_serialize_image`, project `colormap` into the per-layer meta (like the
    other `u_layer{i}_*` fields).

- [x] **3.3 — Frontend colormap GLSL**
  - Add `buildImageColormap()` to `image-shader.js` (viridis/turbo polynomials +
    `imageColormap(float t, int m)` mirroring `depth-shader.js`).
  - Change `tangaSampleLayer` to return `vec4` (rgb + a): `a = tex.a` for
    4-channel layers (default RGB mode), else `1.0`; for scalar modes
    (gray/magnitude/alpha) map the normalized value through
    `imageColormap(t, u_layer{i}_colormap)`.
  - Update `tangaComposite` / `layerComposite` to blend with
    `u_layer{i}_opacity * sample.a` so a 4-channel layer's alpha is respected.

- [x] **3.4 — Frontend uniform defaults**
  - In `image.js` `buildLayerUniforms`, add
    `u_layer{i}_colormap: { value: s[`u_layer${i}_colormap`] ?? 0 }`.

- [x] **3.5 — Tests**
  - Python: a 4-channel `uint8` layer serializes `mode == ALPHA`-able and
    `colormap` projects correctly; `ImageLayerStyle(colormap="viridis")` → code 1;
    unknown colormap raises.
  - JS: extend `image-layers.test.mjs` to assert `buildImageLayerPipeline(8)`
    emits 8 samplers and that the fragment declares `u_layer{i}_colormap`.
  - Add a focused shader-source assertion that the composite multiplies layer
    alpha (`u_layer{i}_opacity *`).

- [x] **3.6 — Rebuild bundle**
  - `uv run python tools/build-viewer-js.py`.

## Validation

```
uv run pytest py/tests/viz/test_image_layer_style.py py/tests/viz/test_image_view.py -q
uv run ruff check py/pytanga/viz/image.py py/pytanga/viz/_image_view.py
node --test js/dev/tests/image-layers.test.mjs
uv run python tools/build-viewer-js.py
```

## Notes

- Verify (and document in Phase 6) that a 4-channel layer is **alpha-composited**
  with `opacity` and the blend mode: the effective blend alpha is
  `u_layer{i}_opacity * textureAlpha`, and `chmode == 3` still exposes the alpha
  channel as grayscale color when needed.
- Built-in colormap only here; a per-layer LUT *texture* remains a non-goal.
