# Phase 2 — `ImageCanvas` per-layer API + granular updates

## Goal

Forward the per-layer setters from `ImageCanvas` and emit granular `image_update`
uniform patches (the existing channel patches any uniform key by name).

## Files

- Edit: `py/pytanga/viz/_image_view.py`
- Edit: `py/tests/viz/test_image_canvas_integration.py`

## Steps

- [x] **2.1 — `ImageCanvas` per-layer setters.**
  - Add `set_layer_enabled/opacity/blend/value_range/channel` mirroring
    `ImageView`, each calling the view's setter then sending a granular
    `image_update` `{uniforms: {key: value}}` (mirroring `ImageCanvas.set_uniform`).

- [x] **2.2 — Tests.**  Each setter emits one `image_update` with the correct
  per-layer uniform key and no binary frame.

## Validation

```
uv run pytest py/tests/viz/test_image_canvas_integration.py -q
uv run ruff check py/pytanga/viz/_image_view.py
```
