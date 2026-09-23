# General camera/transform calibration support — Overview

**Created:** 2026-09-22 | **Status:** Done | **Branch:** `feat/calib-cam-view`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a general, typed way to express coordinate-frame conventions (OpenCV ↔
right-handed), scale input data, and map read-in camera calibration (``K``/``R``/
``t``) onto pytanga camera classes — reusable for any single- or multi-camera
setup, while keeping the internal world frame right-handed so rotations keep
working.

## Architecture (short)

- `pytanga.geometry.Matrix` — a plain numeric square matrix (3×3/4×4),
  column-vector convention, numpy-backed, no algebra/viz dependency.
- `pytanga.geometry.MatrixProvider` — a runtime-checkable Protocol for anything
  with `to_matrix() -> np.ndarray`.
- `pytanga.geometry.CoordinateFrame` + `OpenCVFrame` — named axis conventions;
  `to_matrix()` returns the 4×4 change-of-basis (a proper rotation, det = +1).
- `pytanga.viz.CameraCalibration` — `K`/`R`/`t` + `frame` + `units` →
  `PinholeCamera` + world pose + extrinsics.
- `set_transform` / `apply_transform` accept `MatrixProvider`, so
  `set_transform(frame)` works through the existing scene-graph path.

## Decisions (confirmed)

- OpenCV → standard is a 180° rotation about +x (`diag([1,-1,-1])`, det = +1),
  right-handed preserved; `OpenCVFrame` is a **subclass** of `CoordinateFrame`
  with no `opencv()` classmethod.
- A `MatrixProvider` Protocol (`typing.Protocol`, `@runtime_checkable`), not reuse
  of `MVTensor`/`MVMatrix` (which are algebra-bound).
- `Matrix`/`CoordinateFrame` live in `pytanga.geometry`; `CameraCalibration` in
  `pytanga.viz.camera`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-matrix.md](./01-matrix.md) | `Matrix` + `MatrixProvider`; wire into `set_transform` |
| 2 | [02-coordinate-frame.md](./02-coordinate-frame.md) | `CoordinateFrame` + `OpenCVFrame` |
| 3 | [03-camera-calibration.md](./03-camera-calibration.md) | `CameraCalibration` in `viz.camera` |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | developer docs + changelog |

## Testing as you go

- `uv run pytest py/tests/geometry/test_matrix.py py/tests/geometry/test_coordinate_frame.py py/tests/viz/test_camera_calibration.py -q`
- `uv run ruff check .`
- `uv run ty check`
- `uv run mkdocs build --strict`

## Non-goals

- No rewrite of the T-LESS example yet (follow-up once the types land).
- No MV/algebra integration; no frontend changes.
