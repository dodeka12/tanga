# Phase 7 — Quadric intersection applies `Ellipse.angle`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/quadric-module.md`.  This keeps the conic path's output
> identical (`angle == 0` there) while honoring the new field for rotated ellipses.

## Goal

Make `quadric/_intersection.py` treat `Ellipse.dir_u`/`dir_v` as the *basis* and
apply `angle` when sampling the ellipse outline, so a rotated `Ellipse` samples
correctly.  For the conic path (`refine.py` leaves `angle == 0`) this is a no-op.

## Files

- Edit: `py/pytanga/quadric/_intersection.py`
- Edit: `py/tests/geometry/test_conic_intersections.py`

## Steps

- [x] **7.1 — Rotate the semi-axes by `angle`.**
  - In the ellipse sampling branches (`:398-418` and `:590-601`), replace the
    direct `(entity.dir_u.x, entity.dir_u.y)` use with the angle-rotated axes
    `ux,uy = R(normal, angle)·dir_u` (2D in-plane rotation; add a small local
    helper).  Keep the `None` → `(1,0,0)`/`(0,1,0)` default.

- [x] **7.2 — Tests.**
  - A rotated `Ellipse` (angle ≠ 0) samples to the rotated outline; the conic
    `Ellipse` (`angle == 0`) is unchanged.

## Validation

`uv run pytest py/tests/geometry/test_conic_intersections.py -q`

## Notes

- `quadric/refine.py` needs no change: it sets `dir_u`/`dir_v` = principal
  directions and leaves `angle == 0`, so the basis *is* the semi-axis.
