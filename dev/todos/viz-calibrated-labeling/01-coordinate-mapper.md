# Phase 1 — `CoordinateMapper` protocol + mappers

## Goal

Add the pixel↔world `CoordinateMapper` protocol and two implementations
(`PlanarMapper`, `CalibratedPlaneMapper`) in `camera.py`, with round-trip tests.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/tests/viz/test_coordinate_mapper.py`

## Steps

- [x] **1.1 — `CoordinateMapper` protocol**
  - Add `class CoordinateMapper(Protocol)` with `to_world(u, v) -> Point` and
    `to_pixel(point) -> tuple[float, float]` in `camera.py`.
- [x] **1.2 — `PlanarMapper` (default)**
  - `to_world(u, v)` returns `Point(u, v, 0.0)`; `to_pixel(p)` returns `(p.x, p.y)`.
- [x] **1.3 — `CalibratedPlaneMapper`**
  - `__init__(camera: CameraCalibration, depth: float)`.
  - `to_world(u, v)`: unproject `(u, v)` through `camera.K` to a camera-frame ray,
    intersect with the plane ⟂ the optical axis at `depth` (metres), map to world
    via `camera.camera_to_world()`.
  - `to_pixel(p)`: exact inverse via `world_to_camera()` + `K`.
  - Document the single-fixed-`depth` approximation in the docstring.
- [x] **1.4 — Export**
  - Export `CoordinateMapper`, `PlanarMapper`, `CalibratedPlaneMapper` from
    `pytanga.viz` (`__init__.py` import + `__all__`).
- [x] **1.5 — Tests**
  - `to_pixel(to_world(u, v)) == (u, v)` for both mappers over a grid.
  - `PlanarMapper` is identity (`to_world(u, v) == Point(u, v, 0.0)`).
  - `CalibratedPlaneMapper`: the principal point maps to a point at `depth` on the
    optical axis; `to_pixel` of a known world point returns its pixel.

## Validation

```
uv run pytest py/tests/viz/test_coordinate_mapper.py -q && uv run ruff check . && uv run ty check
```

## Notes

- The exact optical-axis sign convention (camera looking +z vs −z) is pinned by
  the round-trip invariant `to_pixel(to_world(u,v)) == (u,v)`; do not hardcode it
  without that test.
