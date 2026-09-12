# Phase 3 — `lstsq`, `svd`, and `inv` on `AffineExpression`

## Goal

Expose `lstsq()` / `svd()` and a working `inv()` on `AffineExpression`,
delegating to `numpy.linalg` over the combined matrix from `_variable_matrix()`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/expression/_expression.py`

## Steps

- [x] **3.1 — Add `AffineExpression.lstsq(rhs=None)`**
  - `_name, var_mask, matrix = self._variable_matrix()`.
  - `rhs is None`: `np.linalg.svd(matrix, full_matrices=False)` → smallest
    right-singular vector → `from_tensor` over `var_mask`.
  - Else: require `not self._has_counting_axes()`; coerce `rhs` to an MV over
    `out_mask`; `np.linalg.lstsq(matrix, vec, rcond=None)` → `from_tensor`.
  - Mirror `Expression.lstsq` (same homogeneous/explicit-rhs semantics).

- [x] **3.2 — Add `AffineExpression.svd()`**
  - `np.linalg.svd(matrix, full_matrices=False)`; return the descending singular
    values and the right-singular MVs over `var_mask` (mirror `Expression.svd`).

- [x] **3.3 — Rewrite `AffineExpression.inv(var_name)`**
  - Reject counting axes (`self._has_counting_axes()`), require single
    variable / once-per-term (via `_variable_matrix()`), and require square
    (`len(out_mask) == len(var_mask)`).
  - `inv_mat = np.linalg.inv(matrix)`; build `MVTensor(data=inv_mat,
    masks=(var_mask, out_mask))` → `MVLabeledTensor` → `Expression` keyed by
    `var_name` with mask `out_mask` (mirror `Expression.inv`).
  - Change the return annotation to `-> "Expression"`.

- [x] **3.4 — Remove the now-unused `NoReturn` import**
  - Change `from typing import TYPE_CHECKING, Any, NoReturn` to
    `from typing import TYPE_CHECKING, Any`.

## Validation

`uv run pytest py/tests/expression/ -q`

## Notes

- The existing `test_inv_raises` stays green: `(v*v) + w` has two variables, so
  `_variable_matrix()` raises `ValueError` before any solve.
- Keep `lstsq`/`svd`/`inv` error messages in the same style as `Expression`
  (`ValueError` for no/multi/repeated variable, non-square, or stacked `inv`).
