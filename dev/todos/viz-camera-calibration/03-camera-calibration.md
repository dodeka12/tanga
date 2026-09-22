# Phase 3 — `CameraCalibration`

## Goal

A typed bundle of camera intrinsics/extrinsics that maps read-in K/R/t (in a
named frame, with units) onto `PinholeCamera`, and exposes the camera's world
pose + extrinsics for multi-camera setups.

## Files

- Edit: `py/pytanga/viz/camera.py` (`CameraCalibration`)
- Edit: `py/pytanga/viz/__init__.py` (export)
- New: `py/tests/viz/test_camera_calibration.py`

## Steps

- [x] **3.1 — `CameraCalibration(K, R, t, image_size, *, frame=OpenCVFrame(), units=1.0)`**.
- [x] **3.2 — `to_pinhole_camera()`** (frame→standard + units, delegate to `pinhole_camera`).
- [x] **3.3 — `world_pose()` / `extrinsics()`**.
- [x] **3.4 — tests** (known K/R/t → expected PinholeCamera pose).

## Validation

`uv run pytest py/tests/viz/test_camera_calibration.py -q && uv run ruff check . && uv run ty check`
