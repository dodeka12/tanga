# Phase 2 — `AffineExpression` matrix builder

## Goal

Add `_has_counting_axes()` and `_variable_matrix()` — the shared machinery that
turns a single-linear-map `AffineExpression` into a flat NumPy matrix.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/expression/_expression.py`

## Steps

- [x] **2.1 — Add `AffineExpression._has_counting_axes()`**
  - `return any(t._has_counting_axes() for t in self._terms)`.

- [x] **2.2 — Add `AffineExpression._variable_matrix()`**
  - Return `(var_name, var_mask, matrix)`.
  - Require `len(self.names) == 1` (raise `ValueError` otherwise).
  - Require that variable to appear exactly once in **every** term
    (`name in t._names and len(t._names[name]) == 1` for each term); this rules
    out constant offsets and repeated-variable (nonlinear) terms.
  - `var_mask = self._union_masks()[name]`, `out_mask = self.out_mask`.
  - For each blade id in `var_mask.ids`: bind `name` to
    `self.algebra.multivector({blade_id: 1.0})`, evaluate `self(**{name: basis})`,
    and flatten the result (an `MV` or a nested list of `MV`) depth-first into
    coefficient columns over `out_mask` via `to_tensor(leaf, mask=out_mask).data`.
  - Assemble a `(rows, n_var)` array (`np.column_stack`); counting axes contribute
    extra rows.

## Validation

`uv run pytest py/tests/expression/test_affine.py -q`

## Notes

- Mirror `Expression._variable_matrix` semantics: single variable, single
  occurrence, output blades as rows, variable blades as columns.
- The "once per term" check (not "once total") is what makes a sum like
  `(x*w) + (x*x*w)` a valid single linear map even though `w` appears in two
  terms — this matches the report's `J_at_R` case.
- Row order of counting-axis flattening is not correctness-critical for
  `svd`/homogeneous `lstsq` (SVD is row-permutation invariant), but flatten in
  the order `from_tensor` produces to stay deterministic.
