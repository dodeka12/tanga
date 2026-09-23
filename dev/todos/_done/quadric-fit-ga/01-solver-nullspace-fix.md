# Phase 1 — Solver null-space fix

## Goal

Make `Expression.lstsq(rhs=None)` and `Expression.svd` (and their `AffineExpression`
twins) return the correct null space of a **wide** (underdetermined) homogeneous
system. Today they use `np.linalg.svd(..., full_matrices=False)`, which drops the
null-space right-singular vector when the matrix has more columns than rows — exactly
the conic (5×6) and quadric (9×10) fit.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_nullspace_fit.py`

## Steps

- [x] **1.1 — `Expression.lstsq(rhs=None)` uses `full_matrices=True`**
  - In the homogeneous branch, change `np.linalg.svd(matrix, full_matrices=False)` to
    `full_matrices=True`; keep `x = vt[-1]` (now the true null vector for wide systems;
    identical for square/tall).
- [x] **1.2 — `Expression.svd()` returns the full right-singular basis**
  - Use `full_matrices=True`; return `(values, mvs)` where
    `values = list(s) + [0.0] * (n - len(s))` with `n = len(var_mask)`, and `mvs` are the
    `n` right-singular MVs in descending singular-value order (trailing zero values =
    null space).
- [x] **1.3 — mirror in `AffineExpression.lstsq`/`svd`**
  - Apply the same `full_matrices=True` + padding in the `AffineExpression` homogeneous
    `lstsq` branch and its `svd()`.
- [x] **1.4 — tests**
  - `test_nullspace_fit.py`: a 5×6 and a 9×10 wide system return a null vector with
    (near-)zero residual; a square system's `lstsq`/`svd` output is unchanged; `svd()`
    returns `len(var_mask)` MVs with the trailing singular values 0.

## Validation

`uv run pytest py/tests/expression -q`

## Notes

- `np.linalg.svd` returns `s` of length `min(m, n)` regardless of `full_matrices`; only
  `vt` grows. Padding `values` keeps `values`/`mvs` 1:1.
- `inv()` (square-only) and the `rhs`-given `lstsq` (`np.linalg.lstsq`) are unchanged.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
