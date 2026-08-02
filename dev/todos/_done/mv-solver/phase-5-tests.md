# Phase 5 — Tests

← [Back to Overview](./overview.md)

> **Always consider the developer docs** under `docs/dev/` when implementing any step in this plan.  
> In particular: the [Python Coding Style Guide](../../../docs/dev/guides/py-coding-style-guide.md).  
> Also review any relevant architecture docs, use-case examples, and best practice documentation found there.

## Goal

Write `py/tests/test_solver.py` (for `MVSolver`) and `py/tests/test_algebra_random.py`
(for `Algebra.random_mv()`) containing integration tests.  Unit-level tests for
each phase are described in the individual phase files; these files cover
cross-phase scenarios and regression cases.

---

## Steps

### 5.1 — Fixtures ✓

Define shared pytest fixtures:

- `alg_float` — `Algebra(3, 0, 'float64')`
- `alg_int` — `Algebra(3, 0, 'int64', modulus=97)`
- `slv_float` — `MVSolver(alg_float)`
- `slv_int` — `MVSolver(alg_int)`
- `vec_A_float` — `alg_float.random_mv(rng=42)` (reproducible general MV)
- `vec_A_int` — `alg_int.random_mv(low=-48, high=49, rng=42)` (within mod-97 range)
- `mask_A_float` — `BladeMask.from_mv(alg_float, vec_A_float)`

**Tests:** Verify fixtures construct without error.

### 5.2 — Blade-mask utilities ✓

- `BladeMask(alg_float, [4, 1, 1, 2]).ids == [1, 2, 4]` (sorted, deduplicated).
- `mask.index(2) == 1`; `4 in mask` is `True`; `7 in mask` is `False`.
- `BladeMask.from_mv(alg_float, vec_A_float).ids == [1, 2, 4]` (bits for e1, e2, e3).
- **String construction:** `BladeMask(alg_float, "1 + 2 e3 - e13").ids == [0, 4, 5]`.
- **List-of-strings:** `BladeMask(alg_float, ["e12", "1 + e13"]).ids == [0, 3, 5]`.
- **Grades:** `BladeMask(alg_float, grades=[0]).ids == [0]`.
- **Grades:** `BladeMask(alg_float, grades=[2]).ids == [3, 5, 6]` in G(3,0).
- **Grades:** `BladeMask(alg_float, grades=[0, 2]).ids == [0, 3, 5, 6]`.
- **Combined:** `BladeMask(alg_float, ["e1"], grades=[2]).ids == [1, 3, 5, 6]`.
- `BladeMask.full(alg_float).ids == list(range(8))`.
- `mask_A_float.union(BladeMask(alg_float, grades=[0])).ids == [0, 1, 2, 4]`.
- `union` on masks from different algebras raises `AssertionError`.
- `slv_float.blade_mask(vec_A_float).ids == [1, 2, 4]`.
- `slv_float.product_blade_mask(vec_A_float, mask_A_float, complete=True)` returns
  a `BladeMask` whose `.ids` is a superset of `[0, 1, 2, 3, 4, 5, 6]`.
- Unknown `product='xy'` raises `ValueError`.

### 5.3 — `to_matrix` / `from_matrix` round-trip ✓

For `vec_A_float` with `mask = slv_float.blade_mask(vec_A_float)`:
- `m = slv_float.to_matrix(vec_A_float, mask)` returns `MVMatrix` with
  `shape == (3, 1)`, `row_mask.ids == [1, 2, 4]`, and `col_mask.ids == []`.
- `slv_float.from_matrix(m).to_dict()` equals `vec_A_float.to_dict()`.
- `from_matrix` on an `MVMatrix` with non-empty `col_mask` raises `ValueError`.

### 5.4 — Product-matrix correctness ✓

For `A = 1·e1` in G(3,0) float64:
- `col_ids = [1]`, `row_ids = [1, 2, 3, 4, 5, 6, 7]` (all blades).
- `M = slv_float.product_matrix(A, col_ids, row_ids)` returns an MVMatrix
  of shape `(7, 1)`.
- Verify `M.data[row_ids.index(1), 0] == 1.0` (e1 * e1 = scalar, id 0 not
  in row_ids so verify correctly absent) and spot-check a few other entries
  against the known G(3,0) multiplication table.

### 5.5 — Float `solve` correctness ✓

In G(5,0) float64, construct an invertible grade-1 multivector A and a target
Y.  Verify:
- `X = slv.solve(A, Y)` satisfies `(A * X).to_dict() ≈ Y.to_dict()` within
  1e-10 for each blade.
- `slv.solve` on a float algebra with a singular A raises `LinAlgError`.
- `slv.solve` on an integer algebra raises `TypeError`.

### 5.6 — `solve_lsq` correctness ✓

Using the same A and Y as 5.5, verify `solve_lsq` returns the same result as
`solve` for a full-rank system (they should agree to within 1e-8).

### 5.7 — `solve_mod` correctness and cross-check against `inv` ✓

In G(3,0) int64 with modulus 97:
- For an invertible A, compute `X = slv_int.solve_mod(A, alg_int({0: 1}), 97)`.
- Verify `(A * X).reduce(97).to_dict() == {0: 1}` (scalar 1 mod 97).
- Cross-check: `X.to_dict() == alg_int.inv(A, 97).to_dict()`.
- For a non-invertible A (e.g. modulus not coprime to a pivot), verify
  `RuntimeError` is raised.
- `slv_float.solve_mod(...)` raises `TypeError`.

### 5.8 — `Algebra.solver` property ✓

- `alg.solver` returns an `MVSolver`.
- `alg.solver._alg is alg`.
- `alg.solver` creates a fresh `MVSolver` each call (no caching — verify the
  property docstring states this).

### 5.9 — `MVLike` coercion ✓

Verify that every public `MVSolver` method that accepts `MVLike` correctly
coerces scalar and string inputs:

- `slv_float.solve(vec_A_float, 1.0)` produces the same result as
  `slv_float.solve(vec_A_float, alg_float({0: 1.0}))`.
- `slv_float.solve(vec_A_float, "1")` produces the same result.
- `slv_float.to_matrix(0.5, mask_A_float)` equals
  `slv_float.to_matrix(alg_float({0: 0.5}), mask_A_float)`.
- `slv_float.blade_mask("e1 - e2")` returns a `BladeMask` with `.ids == [1, 2]`.
- `slv_int.solve_mod(vec_A_int, 1, 97)` produces the same result as
  `alg_int.inv(vec_A_int, 97)` (cross-check).

### 5.9 — `Algebra.random_mv()`

In `py/tests/test_algebra_random.py`:

- `alg_float.random_mv()` returns an MV with all 8 blades non-zero.
- `alg_float.random_mv(mask=BladeMask(alg_float, [1,2,4]))` returns an MV
  with blades 1, 2, 4 only (others zero or absent).
- `alg_float.random_mv(low=5.0, high=6.0)` — all coefficients in `[5.0, 6.0)`.
- `alg_float.random_mv(low=-1, high=1, rng=42)` twice gives identical results.
- `alg_float.random_mv(rng=0)` and `alg_float.random_mv(rng=1)` differ.
- `alg_int.random_mv(low=-48, high=49)` returns integer coefficients in
  `[-48, 48]` (inclusive, since high=49 is exclusive).
- Passing a `numpy.random.Generator` as `rng` works correctly.
