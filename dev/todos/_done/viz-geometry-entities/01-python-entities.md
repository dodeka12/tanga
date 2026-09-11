# Phase 1 — Python entity dataclasses (`Cylinder`, `Arc`)

## Goal

Pure, frozen, viz-only data classes in `py/pytanga/geometry/entities/` with no
MV-conversion branch, matching the existing entity style (frozen dataclass +
manual `__init__` using `object.__setattr__`). Both are exported from
`pytanga.geometry` but are **not** added to the `Entity` union.

## Steps

- [x] **1.1 — Add `py/pytanga/geometry/entities/cylinder.py`**
  - Frozen dataclass `Cylinder` with `origin: Point`, `axis: Direction`,
    `length: float`, `radius: float`.
  - `__init__` coerces via `to_point` / `to_direction` / `to_float` (no
    `_convert_mv` branch); defaults `origin=Point(0,0,0)`,
    `axis=Direction(0,0,1)`, `length=1.0`, `radius=0.1`.
  - `__repr__` like the other entities (e.g. `Cylinder(org=…, axis=…,
    len=1.00, r=0.10)`).

- [x] **1.2 — Add `py/pytanga/geometry/entities/arc.py`**
  - Frozen dataclass `Arc` with `origin: Point`, `axis: Direction`,
    `radius: float`, `tube_radius: float`, `angle: float = 2 * math.pi`
    (**radians**), `start_direction: Direction | None = None`,
    `show_arrow: bool = False`, `arrow_length: float | None = None`,
    `arrow_radius: float | None = None`.
  - `__init__` coerces via `to_point` / `to_direction` / `to_float`.
  - Auto-compute `start_direction` when `None` (deterministic):
    1. `a = axis.normalized()`.
    2. Pick reference axis `ref` = the coordinate axis (`e_x`, `e_y`, `e_z`)
       with the smallest `|a · e_i|` so the cross product is well-conditioned.
    3. `start = a.cross(ref).normalized()` (a unit vector ⊥ `axis`).
  - Store the resolved `start_direction` (always normalized).
  - `__repr__` like the other entities.

- [x] **1.3 — Export from `py/pytanga/geometry/entities/__init__.py`**
  - Import `Cylinder`, `Arc`; add both to `__all__`.
  - **Do not** extend the `Entity` union — these are not MV-representable.

- [x] **1.4 — Export from `py/pytanga/geometry/__init__.py`**
  - Import `Cylinder`, `Arc` from `.entities`; add both to `__all__`.

- [x] **1.5 — Unit tests `py/tests/geometry/test_viz_entities.py`**
  - Constructor field population and `to_float` coercion.
  - `Arc.start_direction` auto-computed: unit length and `dot(axis, start) ≈ 0`.
  - `Arc.start_direction` auto-computed is deterministic (same input → same
    result) and respects a user-supplied `start_direction`.
  - Arrow defaults: `show_arrow=False` → `arrow_length`/`arrow_radius` stay
    `None`; `show_arrow=True` keeps explicit values.
  - Rejection: `pytanga.geometry.create(algebra, Cylinder(...))` (and
    `Geometry.create`) raises for the new types.

- [x] **1.6 — Validate**
  - `uv run pytest py/tests/geometry/test_viz_entities.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_viz_entities.py -q`

## Notes

- Keep the new modules free of `pytanga.algebra`/`pytanga.basis` imports so they
  stay pure and importable without triggering the `analysis` registry.
- `arc.py` imports `math` for `2 * math.pi` only — no numpy dependency needed.
