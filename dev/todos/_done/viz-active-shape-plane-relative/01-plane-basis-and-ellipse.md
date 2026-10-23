# Phase 1 — `_plane_basis` helper + `ActEllipse` plane-relative geometry

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This stays inside the existing `ActiveObject`
> composite recipe; no architecture change.

## Goal

Add the in-plane basis helper and make `ActEllipse` lie on, and edit within, an
arbitrary `normal` plane (default `+z`), preserving the exact current behaviour
when `normal` is unset.  This is the rotating-shape pattern `ActRectangle2D`
mirrors in Phase 2 (`ActCircle`, Phase 3, is non-rotating).

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_ellipse.py`

## Steps

- [x] **1.1 — `_plane_basis(normal)` helper.**
  - Add a module-level `def _plane_basis(normal: Direction) -> tuple[Direction, Direction]:`
    in `_active.py`, near `_default_drag_triggers`.
  - `n = normal.normalized()`; `ref = Direction(0.0, 1.0, 0.0)`; if
    `abs(ref.dot(n)) > 0.999` use `ref = Direction(1.0, 0.0, 0.0)`.
  - Return `u0 = ref.cross(n).normalized()` and `v0 = n.cross(u0)`.
  - For `normal=+z` the result must be `u0 == (1,0,0)`, `v0 == (0,1,0)`.

- [x] **1.2 — Store `normal` + basis on `ActEllipse`.**
  - Add kw-only `normal: Direction | None = None` to `ActEllipse.__init__`.
  - Store `self._normal = Direction(0,0,1) if normal is None else normal.normalized()`
    and `self._u0, self._v0 = _plane_basis(self._normal)`.

- [x] **1.3 — Plane-relative `_dir_u`/`_dir_v`.**
  - Rewrite to `cos(angle)·u0 + sin(angle)·v0` and `−sin(angle)·u0 + cos(angle)·v0`.

- [x] **1.4 — Reconstruct with `normal`.**
  - `_build_ellipse()` passes `normal=self._normal` (keeping `dir_u`/`dir_v` from 1.3).

- [x] **1.5 — Full-3D handle positions.**
  - `_radius_handle_position`/`_rotate_handle_position` build
    `Point(center.x + r*d.x, center.y + r*d.y, center.z + r*d.z)` (add the `z` term).

- [x] **1.6 — In-plane resize/rotate/translate.**
  - `_resize_radius`: `value = (pos - center) · dir` (full 3D dot).
  - `_rotate_to`: `angle = atan2((pos-center)·v0, (pos-center)·u0)`.
  - `_translate_by`: `center + delta` (all three components).

- [x] **1.7 — Tests.**
  - Keep the existing `TestPlaneZ` tests green (flat case; they use `delta.z == 0`
    and `normal=+z`).
  - Add: default `normal=+z` round-trip is unchanged; a tilted `normal`
    (e.g. `Direction(0,0,1)` rotated, or a 45° normal) yields `entity.normal`
    preserved, `dir_u`/`dir_v` perpendicular to `normal` and unit-length, the
    radius handle at `center + radius_u·dir_u` (with non-zero `z`), resize/rotate
    computed in the tilted basis, and `_translate_by` applying `delta.z`.

## Validation

`uv run pytest py/tests/viz/test_act_ellipse.py -q`

## Notes

- `Ellipse` renders from `dir_u` + `normal` (serializer decomposes to a
  quaternion) — no serializer change needed (see
  `dev/todos/_done/viz-active-shape-labeling/03-act-ellipse.md`).
- `_plane_basis` uses `Direction.cross`/`dot`/`normalized` (already on `Vec3`).
