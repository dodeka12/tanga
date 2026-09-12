# Phase 3 — `analyze()` on the IPNS grade-2 blade

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Replace the deferred `NotImplementedError` in `_analyze_q3` for IPNS grade 2 with
the real path: factor the bivector into two quadrics and call
`intersect_quadrics`.

## Files

- Edit: `py/pytanga/quadric/_analysis.py`
- Edit: `py/pytanga/quadric/__init__.py` (if `analyze` needs a new export)
- Edit: `py/tests/geometry/test_conic_analysis.py`

## Steps

- [x] **3.1 — `_quadric_intersection_from_blade(mv)`**
  - In `quadric/_analysis.py` (or `_intersection.py`), factor the grade-2 IPNS
    blade with `mv.blade_factorize()` (two grade-1 factors, as used by
    `_pointset.py`).
  - Convert each factor to a 4×4 matrix via `from_coeffs(_coeffs(factor, 10))`,
    and call `intersect_quadrics(Q1, Q2)`.
- [x] **3.2 — Wire `_analyze_q3`**
  - In the IPNS branch, replace the `raise NotImplementedError(…)` for grade 2
    with `return _quadric_intersection_from_blade(mv)`.
  - Leave grades 3..8 deferred (raise as before); grade 1 / 9 unchanged.
- [x] **3.3 — Tests**
  - Build the cube pencil bivector `(x²−y²) ∧ (y²−z²)` as an IPNS grade-2 MV
    (`basis.multivector({blade_ids})` in `BasisQ3(opns=False)`), call
    `analyze_entity` → `PlaneConicPair` with the four body-diagonal lines.
  - `analyze()` (the combined dispatcher) returns the same entity for that MV.
  - A non-grade-2 IPNS MV (e.g. grade 3) still raises `NotImplementedError`.

## Validation

`uv run pytest py/tests/geometry/test_conic_analysis.py -q`

## Notes

- The two factorized generators are arbitrary members of the pencil (usually
  cones), not the plane pairs — `intersect_quadrics` re-derives the degenerate
  members internally, so the factorization basis does not matter.
- `blade_factorize` returns grade-1 MVs; reuse `_coeffs` (already in
  `_analysis.py`/`_pointset.py`) to read their coefficients.
