# Phase 1 — CoordinateMapper world size

## Goal

Add `world_units_per_pixel()` to the `CoordinateMapper` protocol and both
implementations, so the pixel→world *size* scale has a single, documented home.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/tests/viz/test_camera_fit_math.py` (or the mapper test file)
- Edit: `docs/dev/architecture/viz-architecture.md` (`CoordinateMapper` bullet)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **1.1 — Add `world_units_per_pixel()` to the `CoordinateMapper` protocol**
  - Signature `def world_units_per_pixel(self) -> float` with a docstring
    ("world size of one image pixel at the plane").
- [x] **1.2 — Implement it on `PlanarMapper`**
  - Return `1.0` (world == pixels).
- [x] **1.3 — Implement it on `CalibratedPlaneMapper`**
  - Return `self._depth / self._fx`.
- [x] **1.4 — Add a test for both mappers**
  - `PlanarMapper().world_units_per_pixel() == 1.0`;
  - `CalibratedPlaneMapper(calib, depth).world_units_per_pixel() ==
    pytest.approx(depth / calib.K.data[0, 0])`.
- [x] **1.5 — Update `viz-architecture.md`**
  - Extend the `CoordinateMapper` bullet (≈line 388) to mention
    `world_units_per_pixel()`.

## Validation

`uv run pytest py/tests/viz/test_camera_fit_math.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- The method name and scalar return (`depth / fx`) are fixed in the README
  contract; do not change them here.
- `fx` is read from `self._fx` (already stored in `__init__`).
