# Phase 3 — `ActCircle` plane-relative geometry (non-rotating shape)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This stays inside the existing `ActiveObject`
> composite recipe; no architecture change.

## Goal

`ActCircle` is the one non-rotating shape: it has no `angle`/`_dir_u`/`_dir_v`.
Give it an explicit `normal` plus a single in-plane radius direction (`u0`), and
make its geometry full 3D.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_circle.py`

## Steps

- [x] **3.1 — Store `normal` + basis.**
  - Add kw-only `normal: Direction | None = None` to `ActCircle.__init__`;
    store `_normal`, `_u0`, `_v0 = _plane_basis(self._normal)`.

- [x] **3.2 — Reconstruct with `normal`.**
  - `_build_circle()` passes `normal=self._normal`.

- [x] **3.3 — Full-3D radius handle.**
  - `_radius_handle_position()` returns `center + radius·u0` (all three components).

- [x] **3.4 — Full-3D resize/translate.**
  - `_resize_radius()` uses the full 3D distance `|pos − center|`.
  - `_translate_by()`: `center + delta` (all three components).

- [x] **3.5 — Tests.**
  - Keep existing `TestPlaneZ`/`TestLimits` green (flat case).
  - Add tilted-`normal` cases: `entity.normal` preserved, radius handle on-plane
    (non-zero `z`), resize is the 3D distance, translate applies `delta.z`.

## Validation

`uv run pytest py/tests/viz/test_act_circle.py -q`

## Notes

- No rotation: `v0` is cached only for symmetry with `_plane_basis`'s return;
  only `u0` (the radius direction) is used.
