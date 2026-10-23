# Phase 2 — labelme export uses the entity's frame

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `LabelMeStore` bullet).  The
> store stays data-only; this only fixes how oriented shapes are projected back.

## Goal

Make labelme export consistent with the entity's own `dir_u`/`dir_v` + `angle`,
and write the ellipse `angle` in the documented pixel frame.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`

## Steps

- [x] **2.1 — Ellipse pixel-frame angle.**
  - In `_shape_from_ellipse`, write `angle_px = ellipse.angle +
    signed_angle(pixel_u → ellipse.dir_u)` (signed about the plane normal) instead
    of `ellipse.angle`.  Add a `_signed_angle(u, v, normal)` helper.

- [x] **2.2 — `_ellipse_axes` / `_rect_axes` fallback.**
  - When the entity has no `dir_u`/`dir_v`, fall back to `_plane_basis(normal)`
    (not world x/y), so tilted normals stay consistent.

- [x] **2.3 — Tests.**
  - Ellipse with a non-pixel `dir_u` exports its `angle` in the pixel frame.
  - Rectangle with explicit `dir_u`/`dir_v` exports via those axes.

## Validation

`uv run pytest py/tests/viz/test_labelme.py -q`

## Notes

- Rectangles already use the entity's `dir_u`/`dir_v` (via `_basis`); the ellipse
  angle frame is the remaining gap.
