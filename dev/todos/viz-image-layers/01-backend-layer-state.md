# Phase 1 — Backend `ImageView` per-layer state + API

## Goal

Seed per-layer uniforms (`u_layer{i}_enabled/opacity/blend/mode/value_min/
value_max`) on `set_image`/`add_image`, expose thin `set_layer_*` wrappers, and
project the per-layer fields into each serialized `images[]` entry.

## Files

- Edit: `py/pytanga/viz/image.py` (add `LayerBlendMode`)
- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/pytanga/viz/__init__.py` (export `LayerBlendMode`)
- Edit: `py/tests/viz/test_image_view.py`

## Steps

- [x] **1.1 — Add `LayerBlendMode` to `image.py`.**  IntEnum NORMAL=0, ADD=1,
  MULTIPLY=2, SCREEN=3; export from `pytanga.viz`.

- [x] **1.2 — Per-layer uniform keys + seeding helpers in `ImageView`.**
  - Add `_layer_uniforms(i, image)` returning the six `u_layer{i}_…` defaults
    from `image.channels`/`image.dtype` (`default_mode`/`default_value_range`).
  - Seed them with `setdefault` in `_seed_image_defaults` and overwrite them in
    `_reset_image_defaults` (so `set_image` re-derives from the new image).

- [x] **1.3 — Per-layer setters on `ImageView`.**
  - `set_layer_enabled(i, bool)`, `set_layer_opacity(i, float)`,
    `set_layer_blend(i, int|LayerBlendMode)`, `set_layer_value_range(i, lo, hi)`,
    `set_layer_channel(i, int|ImageChannelMode)` — thin `set_uniform` wrappers
    with index validation (0 ≤ i < `len(self._images)`).

- [x] **1.4 — Project per-layer fields into `images[]`.**
  - Extend `ImageView._serialize_image` (or `ImageData.layer_meta()` callers) to
    merge `enabled`, `opacity`, `blend`, `mode`, `value_min`, `value_max` read
    from `_uniforms` for each layer index.

- [x] **1.5 — Tests.**  Seeding defaults, per-layer setter writes the right
  uniform key, serialization of a multi-layer `ImageView` carries per-layer
  fields on each `images[]` entry, dtype-dependent `value_max` per layer.

## Validation

```
uv run pytest py/tests/viz/test_image_view.py -q
uv run ruff check py/pytanga/viz/image.py py/pytanga/viz/_image_view.py py/pytanga/viz/__init__.py
uv run ty check
```
