# Phase 3 — `SdfObject` wrapper + `_entity_to_sdf()`

## Goal

Add the `SdfObject` leaf (geometry entity + id + per-entity SDF style) and the
`_entity_to_sdf()` conversion that turns a geometry entity into an `SdfNode` tree
at **construction time** — including `Cylinder`, which the current SDF serializer
does not support. Extend `_coerce()` so raw entities wrap into `SdfObject` inside
operator expressions.

## Files

- New: `py/pytanga/viz/sdf/object.py` — `SdfObject`, `_entity_to_sdf()`.
- Modify: `py/pytanga/viz/sdf/_compose.py` — `_coerce()` wraps raw entities.
- Modify: `py/pytanga/viz/sdf/__init__.py` — export `SdfObject`.
- New: `py/tests/viz/sdf/test_sdf_object.py`.

## Steps

- [x] **3.1 — `SdfObject`** (`object.py`)
  - `@dataclass(frozen=True) class SdfObject(SdfElement)`:
    `entity: Any`, `id: str | None = None`, `style: SdfStyle | None = None`.
  - `to_sdf_node()` → `_entity_to_sdf(entity, style)`, attaching `id` to the
    root `SdfNode`.

- [x] **3.2 — `_entity_to_sdf(entity, style)`** (`object.py`)
  - Maps geometry entities to `SdfNode` via the primitive constructors, applying
    the style's shape params:
    - `Sphere` → `sphere(radius, position=center)`.
    - `Cylinder` → `capped_cylinder(length/2, radius, position=midpoint,
      rotation=align(+Y→axis))` (compute midpoint from `origin`/`axis`/
      `length`/`align_center`).
    - `Line` (finite) → `capped_cylinder(length/2, thickness=style.thickness,
      position=midpoint, rotation=align(+Y→dir))`; infinite → + `bound` box
      (reuse `_rotation_align`/`_normalize`).
    - `Circle` → `torus(radius, tube_radius=style.tube_radius, position=center,
      rotation=align(+Y→normal))`.
    - `Plane` → thin `box` slab (`rotation=align(+Z→normal)`, extent from the
      entity).
    - `Point` → `sphere(size=style.size, position=…)`.
    - `SdfNode`/`Composed`/`SdfGroup`/`Combine` → pass through (already SDF).
  - Default style by entity kind via the Phase 1 `SDF_STYLE_BY_KIND` registry
    when `style is None`.

- [x] **3.3 — `_coerce()` entity wrapping** (`_compose.py`)
  - Non-`SdfElement` operands wrap via `SdfObject(entity)` (default style), so
    `SdfObject(Sphere(...)) + Sphere(...)` and `SdfObject(...) + Box(...)` work.

- [x] **3.4 — Tests** (`test_sdf_object.py`)
  - `SdfObject(Sphere(...)).to_sdf_node()` → a `sphere` `SdfNode` at the right
    position with the right `id`.
  - `_entity_to_sdf(Cylinder(...))` → `cappedCylinder` with correct half-height,
    radius, and axis rotation (verify midpoint for `align_center=0.0`/`0.5`).
  - `Line` thickness and `Circle` tube radius come from the style.
  - `SdfObject(Sphere()) + SdfObject(Cylinder())` → `Combine(UNION, …)`.
  - `SdfObject(Sphere()) + Sphere()` → `Combine` with the raw sphere coerced.

- [x] **3.5 — Validate**
  - `uv run pytest py/tests/viz/sdf/test_sdf_object.py -q` +
    `uv run pytest py/tests/viz/ -q`.

## Validation

`uv run pytest py/tests/viz/ -q` +
`uv run pytest py/tests/viz/sdf/test_sdf_object.py -q`.

## Notes

- This is the "conversion at construction" layer — the serializer never sees
  geometry entities inside a `SdfObject`/group member again.
- `Cylinder` becomes drawable as SDF for the first time (the fullscreen
  serializer's `_dispatch_tree` is untouched; `_entity_to_sdf` is a new,
  standard-viewer-facing helper).
