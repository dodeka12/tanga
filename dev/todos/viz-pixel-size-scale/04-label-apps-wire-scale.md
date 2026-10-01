# Phase 4 — Label apps wire the scale from the mapper

## Goal

Replace the ad-hoc `0.5 * depth / fx` (calibrated) and `0.5` (image) literals
with the mapper's `world_units_per_pixel()`, and set `pixel_scale` on every
shape both label apps create or load.

## Files

- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **4.1 — ImageLabeler derives `pixel_scale` from its mapper**
  - Reads `self._canvas.surface.mapper.world_units_per_pixel()` (= 1.0) and
    stores `self._pixel_scale`.
  - `_apply_size_limits` now sets `act.set_pixel_scale(self._pixel_scale)` in
    addition to the existing `set_size_limits`/`set_radius_limits`.
- [x] **4.2 — CalibratedLabeler derives `pixel_scale` from the mapper**
  - Stores `self._pixel_scale = CalibratedPlaneMapper(calib, depth)
    .world_units_per_pixel()`; the `0.5 * depth / fx` literal is gone (the min
    is now `0.5 * self._pixel_scale`).
  - `_apply_size_limits` sets `act.set_pixel_scale(self._pixel_scale)` on every
    shape (created via `_add_shape` and loaded via `add_loaded_shape`).
- [x] **4.3 — Import/smoke test**
  - `test_labeler_pixel_scale_from_mapper` asserts the calibrated labeler's
    `_pixel_scale == depth / fx`.

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py py/tests/viz/test_image_canvas.py -q`

## Notes

- The 0.5-camera-pixel minimum value must not change — only its computation is
  routed through the mapper.
- `min_radius`/`min_size` remain world-unit arguments; `pixel_scale` is used
  only for the handle-derived distances (tolerance, rotate offset) and, on the
  labeler side, to convert the 0.5-px minimum.
