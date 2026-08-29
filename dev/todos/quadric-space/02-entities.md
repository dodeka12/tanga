# Phase 2 — Entity dataclasses (Conic, Quadric3D, conic kinds, PointSet)

## Goal

Frozen entity dataclasses for the raw conic/quadric representation, the specific
2D conic kinds, and finite point sets. All reuse the 3D `Point`/`Line`/`Direction`
entities with `z = 0` for 2D. Exported from `pytanga.geometry`.

## Files

- New: `py/pytanga/geometry/entities/conic.py` (`Conic`, `Quadric3D` + kind enums)
- New: `py/pytanga/geometry/entities/hyperbola.py` (`Hyperbola`)
- New: `py/pytanga/geometry/entities/parabola.py` (`Parabola`)
- New: `py/pytanga/geometry/entities/line_pair.py` (`LinePair`, `ParallelLinePair`)
- New: `py/pytanga/geometry/entities/point_set.py` (`PointSet`)
- Modify: `py/pytanga/geometry/entities/__init__.py`
- Modify: `py/pytanga/geometry/__init__.py`
- New: `py/tests/geometry/test_conic_entities.py`

## Steps

- [ ] **2.1 — `conic.py`**
  - `EConicKind` StrEnum: `ellipse, circle, hyperbola, parabola, line, line_pair,
    parallel_line_pair, point_pair, imaginary`.
  - `EQuadricKind` StrEnum: `ellipsoid, sphere, hyperboloid_1s, hyperboloid_2s,
    elliptic_paraboloid, hyperbolic_paraboloid, cone, elliptic_cylinder,
    hyperbolic_cylinder, parabolic_cylinder, plane, plane_pair, imaginary`.
  - `Conic(coeffs)` (6-tuple) and `Quadric3D(coeffs)` (10-tuple) — frozen,
    manual `__init__` via `object.__setattr__`; cached properties `matrix`, `kind`,
    `rank`, `signature`, `center`, principal directions, eigenvalues, `rho`.
  - `Quadric2D = Conic` module-level synonym (symmetric with `Quadric3D`); exported
    from `pytanga.geometry`.

- [ ] **2.2 — `hyperbola.py`** — `Hyperbola(center, dir1, dir2, a, b)` (transverse /
  conjugate semi-axes; `dir1`/`dir2` are `Direction`).

- [ ] **2.3 — `parabola.py`** — `Parabola(vertex, direction, p)` (focal parameter).

- [ ] **2.4 — `line_pair.py`** — `LinePair(line1, line2)` (intersecting) and
  `ParallelLinePair(line1, line2)` (parallel); coerce via existing `Line`.

- [ ] **2.5 — `point_set.py`** — `PointSet(points, kind=None)` holding
  `tuple[Point, ...]`; optional `kind` (`single/pair/triplet/quadruplet/n_tuple`).

- [ ] **2.6 — exports** — add the new classes to `entities/__init__.py` and
  `geometry/__init__.py` `__all__`. `Conic`/`Quadric3D` join the `Entity` union;
  `Hyperbola`/`Parabola`/`LinePair`/`ParallelLinePair`/`PointSet` are viz/analysis
  outputs (decide union membership per the `create()`/`analyze()` contracts in
  Phase 3/5).

- [ ] **2.7 — Tests** — constructor defaults/coercion, `__repr__`, cached
  `Conic`/`Quadric3D` derived properties for a known circle/ellipsoid matrix,
  `LinePair` vs `ParallelLinePair` classification fields.

- [ ] **2.8 — Validate** — `uv run pytest py/tests/geometry/test_conic_entities.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_conic_entities.py -q`

## Notes

- Store coefficients as tuples (frozen/hashable), not numpy arrays.
- `center`/directions/eigenvalues are computed lazily and cached
  (`functools.cached_property`), using `numpy.linalg.eigh`/`svd`.
