# Phase 1 — Python entity dataclasses

## Goal

Pure, frozen, viz-only data classes in `py/pytanga/geometry/entities/` with no
MV-conversion branch, matching the existing entity style (frozen dataclass +
manual `__init__` using `object.__setattr__`). All are exported from
`pytanga.geometry` but are **not** added to the `Entity` union.

## Files

- New: `py/pytanga/geometry/entities/disk.py` (`Disk`, `PartialDisk`)
- New: `py/pytanga/geometry/entities/box.py` (`Box`)
- New: `py/pytanga/geometry/entities/ellipsoid.py` (`Ellipsoid`, `Ellipse`)
- New: `py/pytanga/geometry/entities/polygon.py` (`RegularPolygon`, `regular_polygon`)
- Modify: `py/pytanga/geometry/entities/__init__.py`
- Modify: `py/pytanga/geometry/__init__.py`
- Modify: `py/tests/geometry/test_viz_entities.py` (or a new test file)

## Steps

- [x] **1.1 — `disk.py`**
  - `Disk(center, radius=None, normal=None)` → `center: Point` (default origin),
    `radius: float` (default `1.0`), `normal: Direction` (default `+z`).
    Coerce via `to_point` / `to_float` / `to_direction` (no `_convert_mv`).
  - `PartialDisk(center, radius=None, angle=None, start_direction=None,
    normal=None)` → `center`, `radius`, `angle: float` (**radians**, default
    `2π` = full disk), `start_direction: Direction | None`, `normal`.
  - Auto-compute `start_direction` when `None`: deterministic unit vector ⊥
    `normal` (reuse the `_compute_start_direction` helper from `arc.py` — either
    import it or extract a shared helper).
  - `__repr__` like the other entities.

- [x] **1.2 — `box.py`**
  - `Box(center=None, size=None, rotation=None)` → `center: Point` (origin),
    `size: tuple[float, float, float]` (full side lengths, default `(1, 1, 1)`),
    `rotation: Rotor | None` (optional; stored as-is or `None`).
  - Coerce `center` via `to_point`; `size` via `to_float` per component.
  - `__repr__` like the other entities.

- [x] **1.3 — `ellipsoid.py`**
  - `Ellipsoid(center=None, radii=None, rotation=None)` → `center: Point`,
    `radii: tuple[float, float, float]` (default `(1, 1, 1)`),
    `rotation: Rotor | None`.
  - `Ellipse(center=None, radius_u=None, radius_v=None, normal=None)` →
    `center`, `radius_u: float` (default `1.0`), `radius_v: float` (default
    `0.5`), `normal: Direction` (default `+z`). Filled 2D ellipse.
  - Coerce via `to_point` / `to_float` / `to_direction`.

- [x] **1.4 — `polygon.py`**
  - `RegularPolygon(center=None, radius=None, sides=None, normal=None,
    angle=None)` → `center: Point`, `radius: float` (circumradius, default
    `1.0`), `sides: int` (default `6`, validated `>= 3`), `normal: Direction`
    (default `+z`), `angle: float` (in-plane rotation in radians, default `0.0`).
  - Module function `regular_polygon(sides, radius=1.0, center=None, normal=None,
    angle=None) -> RegularPolygon` — ergonomic factory (e.g.
    `regular_polygon(6)` for a hexagon).
  - Coerce via `to_point` / `to_float` / `to_direction`; `sides` via `int`.

- [ ] **1.5 — Export from `entities/__init__.py`**
  - Import `Disk`, `PartialDisk`, `Box`, `Ellipsoid`, `Ellipse`,
    `RegularPolygon`; add to `__all__`. **Do not** extend the `Entity` union.

- [ ] **1.6 — Export from `geometry/__init__.py`**
  - Import the new classes + `regular_polygon`; add to `__all__`.

- [ ] **1.7 — Unit tests** (`py/tests/geometry/test_viz_entities.py` or new file)
  - Constructor defaults and `to_float`/`to_point`/`to_direction` coercion for
    each class.
  - `PartialDisk.start_direction` auto-computed: unit length and
    `dot(normal, start) ≈ 0`; deterministic; respects a user-supplied
    `start_direction`.
  - `RegularPolygon.sides` validated (`< 3` raises) and coerced to `int`.
  - `regular_polygon(6)` returns a `RegularPolygon` with `sides == 6`.
  - Rejection: `pytanga.geometry.create(algebra, <new entity>)` raises for each
    new type.

- [ ] **1.8 — Validate**
  - `uv run pytest py/tests/geometry/test_viz_entities.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_viz_entities.py -q`

## Notes

- Keep the new modules free of `pytanga.algebra`/`pytanga.basis` imports so they
  stay pure and importable without triggering the `analysis` registry.
- `disk.py` needs the `arc.py` start-direction helper; prefer extracting it into
  a small shared private helper (e.g. in `_util.py`) rather than duplicating it.
- `box.py`/`ellipsoid.py` accept a `Rotor` for `rotation`; Euler-triple support
  can be added if needed, but the serializer normalizes to Euler later.
