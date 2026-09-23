# Phase 2 — GA-native conic/quadric from-points fit

## Goal

Reimplement `conic_from_points_svd` / `quadric_from_points_svd` on the expression
system, add MV-returning helpers, and expose a singular-spectrum / nullity diagnostic so
callers can detect a degenerate (coplanar) point set instead of getting a silent mis-fit.

## Files

- Edit: `py/pytanga/quadric/_build.py`
- Edit: `py/pytanga/quadric/__init__.py`
- New: `py/tests/quadric/test_fit_ga.py`

## Steps

- [x] **2.1 — `_incidence_expression(basis, points)`**
  - `mask = BladeMask(basis, grades=[1])`; `c = Variable("c", mask)`,
    `p = Variable("p", mask)`; `eqn = c.sp(p)`; bind
    `eqn(p=DataArray([embed_point(basis, *pt) for pt in points], masks=("pnt_idx", mask)))`;
    return the resulting expression over `c`.
- [x] **2.2 — `_from_points_expression(basis, points) -> MV`**
  - Return `_incidence_expression(basis, points).lstsq()` (the grade-1 conic/quadric blade).
- [x] **2.3 — reimplement the `_svd` entry points on it**
  - `conic_from_points_svd` / `quadric_from_points_svd` →
    `from_coeffs(_mv_coeffs(basis, _from_points_expression(basis, points)))` (return type
    unchanged: `np.ndarray`).
- [x] **2.4 — MV helpers + diagnostics**
  - `conic_from_points_mv` / `quadric_from_points_mv` → return the MV directly.
  - `fit_singular_values(basis, points) -> list[float]` →
    `_incidence_expression(basis, points).svd()[0]`.
  - `fit_nullity(basis, points, *, tol=None) -> int` → count singular values ≤
    `tol·max(s)` (default `tol = basis.precision`); `1` = well-posed.
- [x] **2.5 — exports + tests**
  - Export the new helpers in `__init__.py` / `__all__`.
  - `test_fit_ga.py`: exact 5-point ellipse and 9-point quadric recover zero residual;
    coplanar circle + apex (issue 1) reports `fit_nullity >= 2`; a noise sweep (0…1e-2)
    stays a rank-3 `cone` when reduced to a 2D-conic fit (defer the cone composition to
    phase 3/4 tests).

## Validation

`uv run pytest py/tests/quadric -q`

## Notes

- Keep `conic_from_points` / `quadric_from_points` (dual/wedge) as-is; only the `_svd`
  variants move onto the expression path.
- Import `Variable`, `DataArray`, `BladeMask` from `pytanga.expression` / `pytanga.blade_mask`
  (downward imports — no cycle with `pytanga.quadric`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
