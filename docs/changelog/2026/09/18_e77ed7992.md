# Changes since version 2.8.0

## New Features

- **Compiled expression evaluation** — `Expression.compile()` and
  `AffineExpression.compile()` return a fast callable for fully-bound
  `MV`/scalar bindings that equals `__call__` but is reduced to the numeric
  contraction; `__call__`/`evaluate` route the same case through the compiled
  path automatically.
- **Multilinear `AffineExpression.get_tensor()`** — a single variable appearing
  `k >= 1` times per term now extracts as a rank-`(1 + k)` `MVTensor`, so a
  quadratic operator (`Omega` twice) can be precomputed once and contracted
  with `np.einsum("ijk,j,k->i", Q, c, c)`.
- **`BladeMask.ids_outside(mv)`** — a cheap single-call membership diff of an
  `MV` against a mask, used to validate expression bindings without rebuilding
  the display basis.
- **Examples** — `compile_fastpath.py` and `quadratic_get_tensor.py` under
  `py/examples/ga/expression/`.

## Refactor

- **Faster repeated evaluation** — `_check_blades` no longer builds a full
  `BladeMask`/display basis per binding; `AffineExpression` memoizes its
  `_union_masks`/`out_mask`/`_counting_axes_union`; and the fully-bound
  `MV`/scalar path precomputes the einsum layout and a greedy contraction path
  once, reusing them on every call.
