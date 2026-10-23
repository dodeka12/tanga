# Image view layers — Overview

**Created:** 2026-10-16 | **Status:** Done | **Branch:** `feat/multi-layer-image-view`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Image canvas (extension recipe)" and "Image background" sections).  This work
> **extends** the `image` entity and `CameraView.background_image` contracts, so
> the developer docs must be updated in Phase 6.

## Goal

Support multiple image layers in the image canvas and the calibrated image view
(background), so several images — possibly at different resolutions and from
different sources (`data` frame, `url`, or `tiled` pyramid) — can be uploaded
and mixed via per-layer uniforms: **enable/disable**, **opacity**, and a
**standard blend mode** (normal / add / multiply / screen), with **per-layer
value-range normalization** so a depth map or segmentation mask displays
correctly regardless of its dtype.

## Architecture (short)

Reuse the existing `ImageView` (`py/pytanga/viz/_image_view.py`), which already
holds up to `MAX_IMAGE_LAYERS = 4` images, a shared shader, and a uniform dict.
Per-layer state lives **only** in the uniform dict (`u_layer{i}_…` keys) and is
projected into the serialized `images[]` entries — one source of truth.

- **Shared model** — `ImageView` seeds per-layer uniforms on `set_image` /
  `add_image` and exposes thin `set_layer_*` wrappers over `set_uniform`.
- **Shared serialization** — one canonical per-image producer emits a common
  base + additive `url` / `tile_size`+`levels`+`tile_version` keys (so
  `data`/`url`/`tiled` differ only additively) with per-layer compositing fields
  merged.  Used by both the canvas `image` entity and the background metadata.
- **Two renderers** stay separate (scene-entity mesh vs NDC background quad) but
  share the default compositing GLSL (per-layer `tangaSampleColor` +
  `tangaBlend`).

## Fixed contract (decided up front)

### Per-layer uniform namespace (layer `i` ∈ 0..3)

| Uniform | Type | Default | Meaning |
|---|---|---|---|
| `u_layer{i}_enabled` | int | 1 | toggle visibility |
| `u_layer{i}_opacity` | float | 1.0 | 0..1 |
| `u_layer{i}_blend` | int | 0 | NORMAL=0, ADD=1, MULTIPLY=2, SCREEN=3 |
| `u_layer{i}_mode` | int | `default_mode(channels)` | gray/rgb/magnitude/alpha |
| `u_layer{i}_value_min` | float | `default_value_range(dtype)[0]` | normalization lower bound |
| `u_layer{i}_value_max` | float | `default_value_range(dtype)[1]` | normalization upper bound |

Global `u_brightness`/`u_contrast`/`u_midpoint` remain the shared adjustment.

### Canonical serialized image layer (every source)

```json
{ "id", "width", "height", "channels", "dtype", "source", "version",
  "url"? , "tile_size"? , "levels"? , "tile_version"? ,
  "enabled", "opacity", "blend", "mode", "value_min", "value_max" }
```

- `version` is always the `ImageData` uuid (identity); `tile_version` (tiled
  only) is the `ImagePyramid` cache key used in the `/image/…` tile URL.
- `data`/`url`/`tiled` differ only additively; transport never affects the
  layer scheme.

### Public API

```python
from pytanga.viz import LayerBlendMode, ImageChannelMode

view.set_layer_enabled(i, True)
view.set_layer_opacity(i, 0.5)
view.set_layer_blend(i, LayerBlendMode.ADD)
view.set_layer_value_range(i, 0.0, 65535.0)
view.set_layer_channel(i, ImageChannelMode.GRAY)
```

## Decisions (confirmed)

- **Full per-layer state** — enabled + opacity + blend modes + per-layer
  value-range normalization, all as uniforms.
- **Uniforms are the single source of truth** — per-layer state is stored as
  `u_layer{i}_…` keys and projected into `images[]` at serialization time.
- **Resolution alignment = stretch-to-primary-frame** via normalized UV.
- **Harmonize serialization first** (Phase 0) and disambiguate `version` (uuid)
  vs `tile_version` (pyramid cache key).
- **Transport is orthogonal** — the layer scheme never depends on how pixels
  arrive.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 0 | [00-serialize-harmonization.md](./00-serialize-harmonization.md) | One canonical image-layer serialization + `version`/`tile_version` split |
| 1 | [01-backend-layer-state.md](./01-backend-layer-state.md) | `ImageView` per-layer uniforms + `set_layer_*` API + serialization |
| 2 | [02-canvas-layer-api.md](./02-canvas-layer-api.md) | `ImageCanvas` per-layer API + granular `image_update` patches |
| 3 | [03-frontend-canvas-shader.md](./03-frontend-canvas-shader.md) | Default multi-layer compositing shader + `image.js` uniforms |
| 4 | [04-background-layers.md](./04-background-layers.md) | Background `images[]` + multi-texture compositing quad |
| 5 | [05-example-controls.md](./05-example-controls.md) | Example app with per-layer enable/opacity/blend controls |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Developer docs + user docs + branch changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` and `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate.
- `node --test js/dev/tests/*.test.mjs` — JS unit tests.
- `uv run python tools/build-viewer-js.py` — rebuild the committed viewer bundle after template edits.
- `uv run mkdocs build --strict` — docs gate (Phase 6).

## Non-goals

- No per-layer fit/crop for mismatched aspect ratios (stretch-to-primary-frame only).
- No blend modes beyond normal/add/multiply/screen.
- No per-layer brightness/contrast (stays global).
- No raising `MAX_IMAGE_LAYERS` beyond 4.
- No merge of the two renderers (scene mesh vs NDC background quad).
