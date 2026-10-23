# Image layer style API — Overview

**Created:** 2026-10-16 | **Status:** Done | **Branch:** `feat/multi-layer-image-view`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Image canvas (extension
> recipe)" section) and `docs/dev/architecture/typing-and-annotations.md`.  This
> work **reshapes the public per-layer API** (new `ImageLayerStyle`, `StrEnum`
> blend modes, `add_layer`/`set_layer`/`set_layer_style`), so the developer docs
> and the branch changelog must be updated in Phase 5.

## Goal

Replace the six per-parameter setters (`set_layer_enabled/opacity/blend/
value_range/channel`) with one `ImageLayerStyle` value object that bundles all
per-layer parameters, expose a string-enum blend mode, and provide a small set
of layer functions: `add_layer` (returns the new layer index), `set_image`,
`set_layer`, and `set_layer_style`.

## Architecture (short)

- `ImageLayerStyle` is a **plain `@dataclass` in `image.py`** (pure data, like
  `ImageData`), **not** a `VizStyle` — it is a per-layer compositing descriptor,
  not a scene-entity style.
- `LayerBlendMode` becomes a **`StrEnum`** (values `"normal"/"add"/"multiply"/
  "screen"`), matching the codebase's `StrEnum` usage (`CameraLock`, `EProduct`,
  `ECompose`).  Its `.code` int property feeds the `u_layer{i}_blend` uniform.
- Style application lives on `ImageView` (the model); `ImageCanvas` forwards and
  syncs.  Two semantics:
  - **full apply** (`set_image`/`add_layer`/`set_layer`): `None` → auto-derived
    (channel from `channels`, range from `dtype`), the rest from the dataclass.
  - **partial merge** (`set_layer_style`): `None` → keep the current value.

## Fixed contract (decided up front)

### `ImageLayerStyle`

```python
@dataclass(slots=True)
class ImageLayerStyle:
    enabled: bool = True
    opacity: float = 1.0
    blend: LayerBlendMode | str = LayerBlendMode.NORMAL
    channel: ImageChannelMode | str | None = None   # None → default_mode(channels)
    value_min: float | None = None                  # None → default_value_range(dtype)[0]
    value_max: float | None = None                  # None → default_value_range(dtype)[1]

DEFAULT_IMAGE_LAYER_STYLE = ImageLayerStyle()
```

`__post_init__` coerces `blend`/`channel` strings to their enums and validates
`0 ≤ opacity ≤ 1` and `value_min ≤ value_max`.

### `LayerBlendMode` (`StrEnum`)

```python
class LayerBlendMode(StrEnum):
    NORMAL = "normal"; ADD = "add"; MULTIPLY = "multiply"; SCREEN = "screen"
    @property
    def code(self) -> int: ...            # 0/1/2/3
    @classmethod
    def from_code(cls, code: int) -> "LayerBlendMode": ...
```

### `ImageView` / `ImageCanvas` API

| Method | Returns | Semantics |
|---|---|---|
| `add_layer(image, style=DEFAULT)` | `int` (the new layer index) | append + full apply |
| `set_image(image, style=DEFAULT)` | `None` | replace layer 0 + full apply |
| `set_layer(index, image, style=DEFAULT)` | `None` | overwrite `index` + full apply |
| `set_layer_style(index, style)` | `None` | partial merge |

The granular `ImageCanvas.set_layer_*` setters are removed (replaced by
`set_layer_style`).

## Decisions (confirmed)

- **Full style** — `ImageLayerStyle` includes `enabled` + `opacity` + `blend` +
  `channel` + `value_min` + `value_max`.
- **`add_layer` returns the layer index.**
- **`StrEnum` blend mode**, wire stays int (`u_layer{i}_blend`).
- **Rename `add_image` → `add_layer`** on both `ImageView` and `ImageCanvas`.
- **`set_layer_style` = partial merge**; `set_image`/`add_layer`/`set_layer` =
  full apply.
- **Wire contract unchanged** — no shader / `image.js` / `image-background.js`
  changes.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-str-enum-and-style.md](./01-str-enum-and-style.md) | `LayerBlendMode` → `StrEnum`; add `ImageLayerStyle` + `DEFAULT_IMAGE_LAYER_STYLE`; export |
| 2 | [02-imageview-model-api.md](./02-imageview-model-api.md) | `ImageView`: `add_layer` (returns index), `set_image(style)`, `set_layer`, `set_layer_style` + apply/merge helpers |
| 3 | [03-imagecanvas-forwarders.md](./03-imagecanvas-forwarders.md) | `ImageCanvas` forwarders + `_push_uniforms`; remove granular setters |
| 4 | [04-example-and-call-sites.md](./04-example-and-call-sites.md) | Example + `camera_view.py`/`_layout.py` call sites |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Developer docs + branch changelog + index |

## Testing as you go

- `uv run pytest py/tests/viz -q` — Python regression.
- `uv run ruff check .` and `uv run ty check` — lint + type gates.
- `node js/dev/tests/check-syntax.mjs` — frontend syntax gate (should be no-op here).
- `uv run python tools/build-viewer-js.py --check` — bundle drift (no template edits expected).
- `uv run mkdocs build --strict` — docs gate (Phase 5).

## Non-goals

- No change to the wire format or the frontend shaders/renderers.
- No `VizStyle` integration — `ImageLayerStyle` is a standalone value object.
- No change to `register_uniform`/`register_shader` (global shader/uniform state
  stays as-is).
