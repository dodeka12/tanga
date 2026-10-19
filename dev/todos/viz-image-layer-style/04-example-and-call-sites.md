# Phase 4 — Example + call sites

## Goal

Update the example to the new API and verify the internal `set_image` call
sites still work (they pass no style → default).

## Files

- Edit: `py/examples/viz/image/image_layers.py`
- Edit: `py/pytanga/viz/views/camera_view.py` (verify only)
- Edit: `py/pytanga/viz/_layout.py` (verify only)
- Edit: `py/tests/viz/test_image_layers_example.py`
- Follow `dev/workflows/example-docs.md` (regenerate docs after editing).

## Steps

- [x] **4.1 — Example uses `add_layer` + `ImageLayerStyle`.**
  - `set_image(rgb)`, `add_layer(depth, ImageLayerStyle(enabled=False, opacity=0.5))`,
    `add_layer(seg, ImageLayerStyle(enabled=False, opacity=0.5))`.
  - Control handlers call `set_layer_style(i, ImageLayerStyle(enabled=…))`,
    `…(opacity=…)`, `…(blend=LayerBlendMode(str(v)))`.

- [x] **4.2 — Verify internal call sites.**
  - `camera_view.py` `ImageView(image.id); set_image(image)` and `_layout.py`
    `existing.set_image(image)` still work with the new default-arg signature.

- [x] **4.3 — Smoke test + example docs.**
  - Update `test_image_layers_example.py` to the new API; run
    `generate-example-docs.py` + `--check`.

## Validation

```
uv run pytest py/tests/viz/test_image_layers_example.py -q
uv run ruff check py/examples/viz/image/image_layers.py
uv run ty check
uv run python tools/generate-example-docs.py --check
```
