# Phase 3 — Grade-1/dual analysis + `refine()` to specific entities

## Goal

`analyze(mv)` in quadric spaces returns the raw `Conic`/`Quadric3D` (level 1);
`refine(Conic/Quadric3D)` (and `geo(conic)`/`geo(quadric3d)`) returns the
specific entity (level 2) when the matrix is projectively one of those, else raises
`ValueError`.

## Files

- New: `py/pytanga/geometry/analysis_q2.py`
- New: `py/pytanga/geometry/analysis_q3.py`
- New: `py/pytanga/geometry/refine.py` (`refine`, `refine_entity`)
- Modify: `py/pytanga/geometry/analysis.py` (detect + dispatch q2/q3)
- Modify: `py/pytanga/geometry/_geometry.py` (`analyze`, `refine`, `__call__` branch)
- New: `py/tests/geometry/test_conic_analysis.py`

## Steps

- [ ] **3.1 — `analysis_q2.py`**
  - `analyze_entity(mv)`: OPNS/IPNS-aware (`mv.algebra.opns`) — grade 1 (or grade 5
    dual) → `Conic(from_coeffs(coeffs))`; reject mixed-grade/zero.
  - Grade 1 OPNS point embedding (rank-1 matrix) → `Point`.

- [ ] **3.2 — `analysis_q3.py`** — grade 1 (or grade 9 dual) → `Quadric3D`;
  grade 1 OPNS rank-1 → `Point`.

- [ ] **3.3 — `refine.py`**
  - `refine_quadric(Quadric3D)`: by rank/signature of `Q = [[A,b],[bᵀ,c]]` →
    `Sphere`/`Ellipsoid`/`Cylinder`/`Cone`/`Plane`; else `ValueError`.
  - `refine_conic(Conic)`: rank/signature → `Circle`/`Ellipse`/`Hyperbola`/
    `Parabola`/`Line`/`LinePair`/`ParallelLinePair`; imaginary → raise (no real
    entity) or `None`.

- [ ] **3.4 — dispatch** — register q2/q3 in `analysis._detect`; add
  `refine` to `Geometry` and a `Conic`/`Quadric3D` branch in `Geometry.__call__`
  before the generic `Entity → create` branch.

- [ ] **3.5 — Tests** — known matrices: circle → `Circle`, ellipse → `Ellipse`,
  hyperbola/parabola/line pair matrices → their entities, ellipsoid → `Ellipsoid`,
  sphere → `Sphere`, cylinder/cone/plane; a general hyperboloid raises; round-trip
  `analyze(mv) → refine(...)`.

- [ ] **3.6 — Validate** — `uv run pytest py/tests/geometry/test_conic_analysis.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_conic_analysis.py -q`

## Notes

- Classification uses the standard affine block form (`A` = quadratic part,
  `b` = linear part, `c` = constant) and its rank/signature; parabola is the
  `rank(A)=1` non-degenerate case (thesis only central conics — implement the
  standard parabola extraction separately).
