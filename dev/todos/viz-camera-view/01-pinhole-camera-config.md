# Phase 1 — `PinholeCamera` config + `fit` + `pinhole_camera` factory

## Goal

Introduce a first-class `PinholeCamera` config type (`type: "pinhole"`) carrying
intrinsics, pose, clipping, and a `fit` aspect policy. `pinhole_camera()` returns
it; `CameraConfig3d.intrinsics` is removed; `Frustum.from_camera` learns to read
it.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/geometry/entities/frustum.py`
- Edit: `py/tests/viz/test_camera_pinhole.py`
- Edit: `py/tests/geometry/test_frustum.py`

## Steps

- [x] **1.1 — `PinholeCamera(CameraConfig)` dataclass**
  - `type: Literal["pinhole"] = "pinhole"`; fields `fx, fy, cx, cy: float`,
    `width, height: int`, `position/target/up`, `near/far`, and
    `fit: Literal["fit", "fill"] = "fit"`.
  - Reuse the generic `CameraConfig.to_dict` (nested `intrinsics` is gone — the
    intrinsics are now flat fields).

- [x] **1.2 — `pinhole_camera()` returns `PinholeCamera`**
  - Change the factory to build a `PinholeCamera` (same `K/R/t` math, plus the
    `fit` kwarg). Drop the `include_intrinsics` kwarg (intrinsics are inherent).

- [x] **1.3 — remove `CameraConfig3d.intrinsics`**
  - Delete the field and the `PinholeIntrinsics` serialization path from
    `CameraConfig3d`/`_to_json` (keep the `PinholeIntrinsics` dataclass only if
    it is still referenced; otherwise remove it and its export).

- [x] **1.4 — `Frustum.from_camera` accepts `PinholeCamera`**
  - Read `fx/fy/cx/cy/width/height` directly when the camera is a `PinholeCamera`,
    else fall back to `fov` + `aspect` for a symmetric `CameraConfig3d`.

- [x] **1.5 — exports + tests**
  - Export `PinholeCamera` from `pytanga.viz`; update the pinhole-camera and
    frustum tests for the new shape (no `intrinsics` dict).

## Validation

`uv run pytest py/tests/viz/test_camera_pinhole.py py/tests/geometry/test_frustum.py -q`

## Notes

- After this phase the frontend no longer sees `intrinsics` on a `"3d"` camera, so
  the pinhole camera renders with a symmetric `fov` until phase 3 wires the
  `"pinhole"` branch — the symmetric path still renders (no crash).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
