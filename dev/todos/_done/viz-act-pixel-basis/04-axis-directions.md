# Phase 4 — `axis_directions()` entity helpers

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/geometry-module-layering.md` (entities are plain data
> classes; a helper method is fine, cf. `Rectangle2D.between`).  Keep `geometry`
> free of `viz` imports.

## Goal

Add `Rectangle2D.axis_directions()` and `Ellipse.axis_directions()` returning the
effective in-plane axes (`dir_u`/`dir_v` rotated by `angle`), and use them
wherever the axes are needed, so code that reads `dir_u` alone stops being wrong.

## Files

- Edit: `py/pytanga/geometry/entities/rectangle.py`
- Edit: `py/pytanga/geometry/entities/ellipsoid.py`
- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/pytanga/quadric/_intersection.py`

## Steps

- [x] **4.1 — Entity methods.**
  - `Rectangle2D.axis_directions()` / `Ellipse.axis_directions()`: when
    `dir_u`/`dir_v` are set, return them rotated by `angle` about `normal`;
    otherwise return `None` (the caller applies a `_plane_basis(normal)` fallback).

- [x] **4.2 — Use them.**
  - Replace `_ellipse_axes`/`_rect_axes` (labelme) and `_ellipse_axes_2d`
    (quadric) with `entity.axis_directions()` + the viz-layer fallback.

- [x] **4.3 — Docs note.**
  - Document "effective axes = `dir_u`/`dir_v` rotated by `angle`" in the entity
    docstrings; add a changelog note that code reading `dir_u` alone must switch.

## Validation

`uv run pytest py/tests/geometry py/tests/viz/test_labelme.py -q`

## Notes

- Returning `None` (rather than importing `_plane_basis`) keeps the `geometry`
  entities self-contained; the viz layer owns the `normal → basis` fallback.
