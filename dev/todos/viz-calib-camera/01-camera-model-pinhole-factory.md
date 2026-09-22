# Phase 1 — Camera model: `PinholeIntrinsics`, `pinhole_camera`, `CameraLock`

## Goal

Add the Python camera model: a `PinholeIntrinsics` value type, an optional
`intrinsics` field on `CameraConfig3d`, a `pinhole_camera(K, R, t, ...)` factory
returning the existing `CameraConfig3d`, and the `CameraLock` string enum that
phase 3 uses. Pure Python + serialization, fully unit-testable before any
frontend work.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/tests/viz/test_camera_pinhole.py`

## Steps

- [x] **1.1 — `PinholeIntrinsics` dataclass**
  - In `camera.py`, add `@dataclass(frozen=True, kw_only=True) class PinholeIntrinsics`
    with `fx: float`, `fy: float`, `cx: float`, `cy: float`, `width: int`,
    `height: int`, and a `to_dict()` returning
    `{"fx":…, "fy":…, "cx":…, "cy":…, "width":…, "height":…}`.

- [x] **1.2 — `CameraConfig3d.intrinsics`**
  - Add `intrinsics: PinholeIntrinsics | None = None` to `CameraConfig3d`.
  - In `CameraConfig.to_dict`, make `_to_json` serialize values exposing
    `to_dict()` (e.g. `if hasattr(value, "to_dict"): return value.to_dict()`)
    so the nested dict is emitted only when `intrinsics` is not `None`.

- [x] **1.3 — `pinhole_camera(K, R, t, *, image_size, near=None, far=None, include_intrinsics=True)`**
  - Coerce `K`/`R`/`t` with `numpy.asarray(..., dtype=float)`; validate shapes
    (K 3×3, R 3×3, t length 3) and raise `ValueError` otherwise.
  - Compute `fx,fy,cx,cy` from K; `W,H` from `image_size`.
  - `fov = 2*atan((H/2)/fy)` in degrees; `position = -R.T @ t`;
    `target = position + R.T @ [0,0,1]`; `up = R.T @ [0,-1,0]`.
  - Build `intrinsics` when `include_intrinsics`, else leave `None`.
  - Return `CameraConfig3d(position, target, up, fov, near, far, intrinsics)`.

- [x] **1.4 — `CameraLock` StrEnum**
  - In `camera.py`, add `class CameraLock(StrEnum): ROTATE="rotate"; PAN="pan"; ZOOM="zoom"`.

- [x] **1.5 — exports**
  - In `__init__.py`, import and add to `__all__`: `PinholeIntrinsics`,
    `pinhole_camera`, `CameraLock`.

- [x] **1.6 — tests**
  - `test_camera_pinhole.py`: fov matches `2*atan((H/2)/fy)`; pose matches
    `-R.T@t` / `R.T@[0,0,1]` / `R.T@[0,-1,0]`; `intrinsics` round-trips through
    `to_dict` and is absent when `include_intrinsics=False`; invalid K/R/t
    shapes raise; `CameraLock(value)` validates and rejects bogus values.

## Validation

`uv run pytest py/tests/viz/test_camera_pinhole.py -q`

## Notes

- `fov` is vertical; the horizontal focal `fx` is recovered exactly for
  square-pixel cameras because a symmetric `PerspectiveCamera` yields
  `fx == fy` (the principal point is the only thing it can't encode — that is
  what the off-center projection in phase 2 supplies).
- `numpy` is already a dependency of `camera.py`'s package (used in `_nodes.py`);
  import it lazily if you want to keep `camera.py` import-free of numpy.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
