# Phase 2 — `CoordinateFrame` + `OpenCVFrame`

## Goal

Named axis conventions with a 4×4 `to_matrix()` (a proper rotation), and the
`OpenCVFrame` subclass that self-initialises to the OpenCV axes.

## Files

- New: `py/pytanga/geometry/frame.py`
- New: `py/tests/geometry/test_coordinate_frame.py`
- Edit: `py/pytanga/geometry/__init__.py`

## Steps

- [x] **2.1 — `CoordinateFrame(x, y, z)`** with `to_matrix()` (4×4) and `handedness()`.
- [x] **2.2 — `OpenCVFrame()`** subclass (no args): `x=(1,0,0), y=(0,-1,0), z=(0,0,-1)`.
- [x] **2.3 — tests** incl. `set_transform(OpenCVFrame())` integration.

## Validation

`uv run pytest py/tests/geometry/test_coordinate_frame.py -q && uv run ruff check . && uv run ty check`
