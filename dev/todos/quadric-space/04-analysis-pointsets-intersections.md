# Phase 4 — PointSet analysis + 2D two-conic intersection

## Goal

Analyze non-grade-1 blades: OPNS point-joins → `PointSet` (easy, factorize + SVD),
and the 2D IPNS two-conic intersection → up to 4 points (thesis pencil method).

## Files

- New: `py/pytanga/geometry/_pointset.py` (join analysis + 2-conic intersect)
- Modify: `py/pytanga/geometry/analysis_q2.py` (grade 2/3/4 → PointSet)
- Modify: `py/pytanga/geometry/analysis_q3.py` (grade 2..8 OPNS → PointSet;
  IPNS intersections → `NotImplementedError` / deferred)
- New: `py/tests/geometry/test_conic_intersections.py`

## Steps

- [ ] **4.1 — OPNS point-join → `PointSet`**
  - `blade_factorize()` the (simple) blade into 1-vectors; for each, `from_coeffs`
    → 3×3 (or 4×4) symmetric matrix; rank-1 → recover the point via SVD (top
    singular vector); collect into `PointSet`.
  - Wire grade 2/3/4 (q2) and grade 2..8 (q3) in the OPNS path.

- [ ] **4.2 — 2D two-conic intersection (thesis `ConicIntersect.tex` summary)**
  - Given two conic matrices `A`, `B` (grade-2 IPNS blade or two `Conic`):
    1. `M = B⁻¹ A`; a real eigenvalue `λ` → degenerate conic `C = A − λB`.
    2. Analyze `C` as a line pair; extract the two lines.
    3. Intersect each line with `A` (quadratic root-finding) → the intersection
       points → `PointSet` (size 0–4).

- [ ] **4.3 — `analyze_entity` wiring** — q2 grade 2 (IPNS) → two-conic
  intersection; grade 3 (self-dual) and grade 4 (IPNS = 2-conic via dual) reuse
  `_pointset`; document which grades are covered and which raise.

- [ ] **4.4 — Tests**
  - Two circles (unit + offset) → the correct 2 intersection points.
  - Two ellipses with 4 intersections → `PointSet` size 4.
  - Tangency → 1 point; disjoint → empty `PointSet`.
  - OPNS join: wedge of 2/3/4 point embeddings → `PointSet` with those points.
  - q3 grade-2 OPNS (2 points) → `PointSet`; IPNS quadric intersection raises
    (deferred).

- [ ] **4.5 — Validate** — `uv run pytest py/tests/geometry/test_conic_intersections.py -q`.

## Validation

`uv run pytest py/tests/geometry/test_conic_intersections.py -q`

## Notes

- `blade_factorize` only works on simple blades; joins of points are simple by
  construction. For non-simple blades, raise a clear `ValueError`.
- 3D IPNS intersections (quartic space curves, triple-intersection point sets) are
  **deferred** — the plan renders those blades via the quadric ray renderer instead.
