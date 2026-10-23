# Phase 6 — LabelMe plane-basis rectangles + new ellipse/circle storage

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `LabelMeStore` bullet).  This
> stays inside the store's data-only contract; no new architecture beyond Phase 5.

## Goal

Make labelme import/export exact on a tilted plane: rectangles built/exported in
the mapper's pixel basis, ellipse stored in the new scalar form, and the circle
radius/rim computed in full 3D (keeping labelme's standard 2-point circle).

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`

## Steps

- [x] **6.1 — `LabelShape` scalar fields + (de)serialization.**
  - Add `radius_u`, `radius_v`, `angle` (`float | None = None`).
  - `loads` reads them via `s.get(...)`; `dumps` emits them only when not `None`
    (like `description`/`mask`).

- [x] **6.2 — Format-aware `_validate_points`.**
  - `circle`: exactly 2 points (unchanged).
  - `ellipse`: 1 point when `radius_u`/`radius_v` present, else exactly 3 (legacy).

- [x] **6.3 — Rectangle build/export in the pixel basis.**
  - Load: from the two mapped corners and `mapper.pixel_axes()`, build
    `Rectangle2D(center, size=(|Δu|·|axis_u|, |Δv|·|axis_v|), angle=0,
    dir_u=axis_u, dir_v=axis_v)` (no more `Rectangle2D.between`).
  - Save: compute the four world corners from `dir_u`/`dir_v` (+`angle`) and
    `to_pixel` each; emit a 2-point `rectangle` when axis-aligned in pixels, else
    the 4-corner `polygon`.

- [x] **6.4 — Ellipse new storage.**
  - Load (new): `center` + `radius_u`/`radius_v`/`angle` + `mapper.pixel_axes()` →
    `Ellipse(center, radius_u, radius_v, dir_u, dir_v, angle)` (convert the
    pixel-space `angle` to the in-plane angle via the mapper — see Notes).
  - Load (legacy): keep the existing `[center, rim_u, rim_v]` branch.
  - Save: emit only the new form — `points=[to_pixel(center)]` + scalar
    `radius_u`/`radius_v`/`angle`.

- [x] **6.5 — Circle radius/rim.**
  - Load: `radius = ‖rim − center‖` (full 3D; replaces the XY-only `math.hypot`).
  - Save: `rim = center + radius·axis_u` (mapper `pixel_axes()[0]`), then
    `to_pixel` — keeps the standard 2-point circle and round-trips on tilt.

- [x] **6.6 — Tests.**
  - Tilted `CalibratedPlaneMapper` round-trips: rectangle, ellipse (new form),
    circle — output pixels match input to `1e-6`.
  - Legacy ellipse (3-point) still loads to the same entity.
  - `dumps` emits the new ellipse form (scalar keys, 1 point) and the standard
    circle (2 points).

## Validation

`uv run pytest py/tests/viz/test_labelme.py -q`

## Notes

- **Angle convention**: labelme `angle` is the first-axis angle in image pixel
  space (`atan2(dy, dx)`, y down).  Convert through the mapper rather than assuming
  equality with the entity's in-plane angle: on load,
  `first = normalize(to_world(center_px + (cos θ, sin θ)) − center_world)` then
  `entity.angle = atan2(det(dir_u, first, normal), dir_u·first)`; on save, project
  `center + radius_u·R(normal, angle)·dir_u` and take `atan2(dy, dx)`.  The
  round-trip test pins the sign.
- The `allow_extensions=False` ellipse fallback (circle if equal radii, else
  polygon) still applies on save and uses the angle-aware axes.
