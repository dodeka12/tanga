# Phase 6 — Entity → SDF mapping

## Goal

Make every new entity renderable through the SDF paths: the per-object
`SdfObject` path (`_entity_to_sdf`) and the fullscreen SDF viewer's analytic
serializer (`_dispatch_tree` / `_*_tree`).

## Files

- Modify: `py/pytanga/viz/sdf/object.py`
- Modify: `py/pytanga/viz/sdf/serializer.py`
- Modify: `py/tests/viz/sdf/test_sdf_object.py`
- Modify: `py/tests/viz/sdf/test_sdf_serializer.py`

## Steps

- [x] **6.1 — `sdf/object.py::_entity_to_sdf`**
  - `Disk` → `capped_cylinder(half_height=thickness/2, radius)` with
    `position=center`, `rotation=align(Y → normal)`. `thickness` from
    `SdfDiskStyle.thickness` via `_style_attr(style, "Disk", "thickness", 0.02)`.
  - `PartialDisk` → `partial_disk(radius, half_height=thickness/2, angle=angle,
    position=center, rotation=align(Y → normal))`. The `start_direction` is
    baked into the local `+X` start axis by the rotation (compute a rotation
    that maps local `+X` → `start_direction` and local `+Y` → `normal`).
  - `Box` → `box((sx/2, sy/2, sz/2), position=center, rotation=…)` (Rotor →
    axis-angle via `_as_rotation`; `None` if axis-aligned).
  - `Ellipsoid` → `ellipsoid(radii, position=center, rotation=…)`.
  - `Ellipse` → `ellipsoid((radius_u, radius_v, thickness/2), position=center,
    rotation=align(Z → normal))`.
  - `RegularPolygon` → `regular_polygon(radius, sides, half_height=thickness/2,
    position=center, rotation=align(Y → normal))`.
  - Update the module docstring's supported-entity list.

- [x] **6.2 — `sdf/serializer.py::_dispatch_tree`**
  - Add the six `isinstance` branches; add matching `_disk_tree`,
    `_partial_disk_tree`, `_box_tree`, `_ellipsoid_tree`, `_ellipse_tree`,
    `_regular_polygon_tree` builders (same math as 6.1, using `_resolve` /
    `_param` for style resolution).
  - Update the module docstring's supported-kinds list.

- [x] **6.3 — Unit tests**
  - `test_sdf_object.py`: `SdfObject(<new entity>).to_sdf_node()` yields the
    expected `SdfNode` kind/params (disk→`cappedCylinder`, box→`box`,
    ellipsoid→`ellipsoid`, ellipse→`ellipsoid`, partial disk→`partialDisk`,
    polygon→`regularPolygon`).
  - `test_sdf_serializer.py`: `serialize_entity(<new entity>, ...)` returns
    `kind: "sdf"`, correct `sdfKind`, and a tree whose root kind matches the
    mapping.

- [x] **6.4 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_sdf_object.py
    py/tests/viz/sdf/test_sdf_serializer.py -q`.

## Validation

`uv run pytest py/tests/viz/sdf/test_sdf_object.py py/tests/viz/sdf/test_sdf_serializer.py -q`

## Notes

- Keep conversion at **construction** time for the per-object path (mirrors the
  existing `_entity_to_sdf` design) — never deep in the serializer.
- The partial-disk start-axis rotation is the one non-trivial bit: build the
  local basis from `(start_direction, normal × start_direction, normal)` and use
  `_rotation_align` for the two axis alignments, or compute the axis-angle
  directly. Prefer a small private helper with a unit test.
- `SDF_STYLE_BY_KIND` (Phase 2) already defaults the right `Sdf*Style` for each
  kind, so `_style_attr` resolves `thickness` correctly.
