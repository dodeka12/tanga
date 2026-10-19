# Phase 5 — Example app with per-layer controls

## Goal

A self-contained example that uploads an RGB image + depth map + segmentation at
different resolutions, and exposes per-layer enable/opacity/blend controls.

## Files

- New: `py/examples/viz/image/image_layers.py`
- New: `py/tests/viz/test_image_layers_example.py`
- Follow `dev/workflows/example-docs.md` (description + `Keywords:` header).

## Steps

- [x] **5.1 — Example script.**  Build an `ImageCanvas` with three `ImageData`
  layers (RGB `uint8`, depth `uint16`, segmentation `uint8`), and a `ControlView`
  panel with per-layer Checkbox (enabled), Slider (opacity), Dropdown (blend) →
  Python handler → `canvas.set_layer_*`.

- [x] **5.2 — Smoke test.**  Import/construct the layout without error; assert
  the layer set is populated.

- [x] **5.3 — Regenerate example docs.**  `uv run python tools/generate-example-docs.py`
  and `--check`.

## Validation

```
uv run pytest py/tests/viz/test_image_layers_example.py -q
uv run python tools/generate-example-docs.py --check
uv run ruff check py/examples/viz/image/image_layers.py
```
