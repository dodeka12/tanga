# Phase 2 — `ActRectangle2D` plane-relative geometry (rotating shape)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This stays inside the existing `ActiveObject`
> composite recipe; no architecture change.

## Goal

Apply the Phase-1 rotating-shape pattern to `ActRectangle2D`.  Like
`ActEllipse`, it stores an internal `angle` and rotates in the plane via
`_dir_u`/`_dir_v`; give it an explicit `normal` and plane-relative geometry.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`

## Steps

- [x] **2.1 — Store `normal` + basis.**
  - Add kw-only `normal: Direction | None = None` to `ActRectangle2D.__init__`;
    store `_normal`, `_u0`, `_v0` exactly as in Phase 1.2.

- [x] **2.2 — Plane-relative `_dir_u`/`_dir_v`.**
  - Rewrite to `cos(angle)·u0 + sin(angle)·v0` and `−sin(angle)·u0 + cos(angle)·v0`.

- [x] **2.3 — Full-3D `_corners()`.**
  - Compute `center ± hw·dir_u ± hh·dir_v` in full 3D (drop the hardcoded
    `cz`/`ux,uy`/`vx,vy`).

- [x] **2.4 — Reconstruct with `normal`.**
  - Every `Rectangle2D(...)` call (constructor + `_resize_corner` + `_rotate_to`
    + `_translate_by`) passes `normal=self._normal`.

- [x] **2.5 — Full-3D handle + mutations.**
  - `_rotate_handle_position` adds `r·d.z`.
  - `_resize_corner`: center midpoint and `hw = |(pos−center)·dir_u|`,
    `hh = |(pos−center)·dir_v|` in full 3D (drop the `center.z` constant and 2D dots).
  - `_rotate_to`: `angle = atan2((pos−center)·v0, (pos−center)·u0)`.
  - `_translate_by`: `center + delta` (all three components).

- [x] **2.6 — Tests.**
  - Keep existing `TestPlaneZ`/`TestLimits` green (flat case).
  - Add tilted-`normal` cases mirroring Phase 1.7: `entity.normal` preserved,
    corners/handles at the on-plane position (non-zero `z`), resize/rotate in the
    tilted basis, translate applies `delta.z`.

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py -q`

## Notes

- Mirrors Phase 1 exactly — the two rotating shapes are symmetric at the `Act*`
  level.  The only difference is the wrapped entity: `Rectangle2D` stores
  rotation as a scalar `angle`, so `entity.angle` round-trips directly into
  `ActRectangle2D(angle=...)` in Phase 5 (vs `Ellipse`'s `dir_u`/`dir_v`).
