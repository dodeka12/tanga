# Phase 2 — Move Q2/Q3 analysis into quadric

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Move the Q2/Q3 MV→entity analysis and the point-recovery helpers into quadric
(`quadric/_analysis.py` + `quadric/_pointset.py`); turn the geometry modules into
thin re-export shims.

## Files

- New: `py/pytanga/quadric/_analysis.py`, `py/pytanga/quadric/_pointset.py`
- Edit: `py/pytanga/quadric/__init__.py`
- Replace (shim): `py/pytanga/geometry/analysis_q2.py`, `py/pytanga/geometry/analysis_q3.py`, `py/pytanga/geometry/_pointset.py`

## Steps

- [x] **2.1 — Move `_pointset.py` → `quadric/_pointset.py`**
  - Move `point_from_embedding`, `pointset_from_blade`, `two_conic_intersection`,
    and their private helpers (`_points_from_two_point_join`,
    `_points_from_join_via_conics`, `_line_pair_from_matrix`, …).
  - Imports: `from_coeffs` from `._mapping`; `Point`/`PointSet` lazily via
    `_entities()` (mirror `quadric/refine.py`).
- [x] **2.2 — Create `quadric/_analysis.py`**
  - Move `analysis_q2.analyze_entity` and `analysis_q3.analyze_entity` into one
    `analyze_entity(mv)` that dispatches on `mv.algebra.dim` (6 → Q2 branch,
    10 → Q3 branch).
  - Import `point_from_embedding`/`pointset_from_blade` from `._pointset` and
    `Conic`/`Quadric3D` from `.conic` (no `geometry.entities` import at module level).
- [x] **2.3 — Shim `geometry/analysis_q2.py`, `analysis_q3.py`, `_pointset.py`**
  - `analysis_q2.py` / `analysis_q3.py` → re-export `quadric._analysis.analyze_entity`.
  - `_pointset.py` → re-export `quadric._pointset.two_conic_intersection` (and the
    other public helpers for any internal users).
  - Keep `geometry/__init__.py`'s `from ._pointset import two_conic_intersection`
    working via the shim.
- [x] **2.4 — Export from `quadric/__init__.py`**
  - Import `analyze_entity` (or the analysis entry point) and `two_conic_intersection`
    from the new modules and add to `__all__`.
- [x] **2.5 — Tests**
  - Verify `analyze` round-trips (Conic / Quadric3D / Point / PointSet) and
    `two_conic_intersection` still pass: `test_conic_analysis.py`,
    `test_conic_intersections.py`, `test_pointset_*`.

## Validation

`uv run pytest py/tests/geometry -q`

## Notes

- The analysis dispatcher `geometry/analysis.py` keeps calling
  `analysis_q2.analyze_entity` / `analysis_q3.analyze_entity`; the shims return the
  same dim-dispatching function, so no dispatcher edit is needed.
- `_pointset.py` returns `Point` / `PointSet` (geometry entities), so those imports
  stay lazy inside `quadric/_pointset.py`.
