# Phase 4 — Tests

## Goal

Add regression tests for the three gaps and keep the existing
`AffineExpression` suite green.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/tests/expression/test_affine.py`

## Steps

- [x] **4.1 — Counting-axis reduction test (gap 1)**
  - Build `a = (v*v*w) + (v*w)` (two non-mergeable terms that both contain `V1`
    and `V2`); bind `V1` to a `DataArray` with counting axis `"n"`; assert the
    partial is an `AffineExpression` whose terms each carry `"n"`.
  - Assert `partial(n=weights)` equals `sum(t(n=weights) for t in partial.terms)`
    evaluated at a sample `V2`.

- [x] **4.2 — Broadcast test (gap 3)**
  - Build `a = (v*w) + c` where `c` is a constant MV (one term containing `V1`,
    one constant term); bind `V1` to a `DataArray` with counting axis `"n"`.
  - Assert the constant term does **not** carry `"n"`, and that
    `partial(n=weights)` equals `carrying_term(n=weights) + c * weights.sum()`
    evaluated at a sample `V2` (raw 1-D `weights`).

- [x] **4.3 — `lstsq` / `svd` test (gap 2)**
  - Build `(u*w) + (u*u*w)`; bind `u` to a constant MV to obtain a
    single-linear-map `AffineExpression` in `w` (two terms, each linear in `w`).
  - Assert `lstsq(rhs=...)` recovers a solution (≈ a manual `numpy` solve /
    round-trip) and `svd()` returns descending values plus right-singular MVs.

- [x] **4.4 — `inv` round-trip test (gap 2)**
  - On the same bound expression, assert `inv("W")(W=expr(W=w0)) ≈ w0` (choose
    the bound `u` value so the combined map is square and full-rank).

- [x] **4.5 — Negative tests**
  - `lstsq`/`svd`/`inv` raise `ValueError` for a two-variable or
    repeated-variable `AffineExpression`; `inv` raises for a non-square output.
  - A counting-axis broadcast with an element-wise (`"_"`) `DataArray` raises
    `ValueError` (sum-only broadcast).

## Validation

`uv run pytest py/tests/expression/ -q`

## Notes

- Use `_reset_allocator()` in `setup_method` (existing convention).
- Use `pytest.approx` / the module's `_close` helper for MV comparisons.
- Keep the existing `test_inv_raises` and `test_unknown_variable` unchanged.
