# Phase 4 — Public `get_tensor()` and `MVTensor.get_array()`

## Goal

Add `Expression.get_tensor()` / `AffineExpression.get_tensor()` returning the raw
`MVTensor` (one raw `BladeMask` per dimension), and `MVTensor.get_array()` for
recombining those axes into named bases.  `lstsq` / `svd` / `inv` keep using the
private raw `_variable_matrix()`.

## Files

- Edit: `py/pytanga/tensor/_data.py`
- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_tensor.py`

## Steps

- [x] **4.1 — `MVTensor.get_array()` + shared helpers**
  - Move `_resolve_basis_directions` / `_basis_right_matrix` / `_basis_left_matrix`
    into `py/pytanga/tensor/_data.py`.
  - Add `MVTensor.get_array(*, out_basis=None, axis_bases=None) -> np.ndarray`:
    axis 0 uses the dual mapping `pinv(B_out) @ data`, other `BladeMask` axes use
    `data @ B_axis`; `None` axes unchanged; directions default to each mask's
    `basis_vectors`.

- [x] **4.2 — `Expression.get_tensor()`**
  - Return `self._tensor.tensor` (the raw `MVTensor`).

- [x] **4.3 — `AffineExpression.get_tensor()`**
  - Single-linear-map guard (one variable, once per term, no counting axes);
    sum each term's raw `_variable_matrix()` matrix into the union output and
    union variable masks; return `MVTensor(data=raw, masks=(out_union, var_union))`.

- [x] **4.4 — tests**
  - `Expression.get_tensor()` returns an `MVTensor` (raw shape).
  - `get_tensor().get_array()` default and `out_basis` overrides.
  - `AffineExpression.get_tensor()` raw data matches `_variable_matrix()`, and
    `get_array()` matches the manual `C_out @ raw @ B_var` recombination.

## Validation

`uv run pytest py/tests/expression/ py/tests/tensor/ -q`

## Notes

- `_variable_matrix()` (raw) stays private and unchanged — `lstsq`/`svd`/`inv`
  still reconstruct `MV`s over the raw `var_mask`.
- Full multi-variable `AffineExpression.get_tensor()` (variables in subsets of
  terms, multi-occurrence) is a follow-up, not this phase.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

