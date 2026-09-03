# Expression numpy binding + subsystem type hints — Overview

**Created:** 2026-09-02 | **Status:** Done | **Branch:** `fix/expression`

## Goal

1. Let `Expression.__call__` bind a variable to a plain NumPy array using the
   *further streamlined* tuple form, e.g.
   `expr(x_pnt=(points, ("pnt_idx", point_mask)))` (or a single-`None`-axis
   `MVTensor`, which is treated like a list of MVs), and then reduce a resulting
   counting axis: `contract(pnt_idx=scalars)` sums it away,
   `contract(pnt_idx=(scalars, ("pnt_idx_",)))` multiplies element-wise and
   keeps it, and `contract(pnt_idx=(scalars2d, ("pnt_idx", "group_idx_")))`
   sums one counting axis while keeping another.
2. Add complete type hints to every class and function in the expression and
   tensor subsystems so the data flow is readable without running the code.

The `MVTensor(..., masks=("pnt_idx", point_mask))` string-mask spelling from
`_input/test_expression_2.py` is **not** implemented: `MVTensor` stays data +
`BladeMask | None` masks, and axis names remain the concern of
`MVLabeledTensor`/the binding DSL. A plain `MVTensor` with one matching blade
axis and one `None` axis *is* accepted as a variable binding.

## Background

- `_input/test_expression_2.py` currently performs the contraction manually:

  ```python
  contract = expr.tensor["kabc"] * data["n_a"] * data["n_c"]
  scalar_contract = contract["kbn"] * scalar_data["n"]
  ```

  The desired DSL collapses this into the `__call__` binding syntax above.
- The existing `Expression._evaluate` (`py/pytanga/expression/_expression.py`)
  already contracts variable occurrences against labeled tensors via
  `contract_labeled`; multi-character axis names (`"pnt_idx"`) already work
  through the structured `AxisLabel(name, mode)` labels and list-form `einsum`.
  The missing pieces are: accepting the `(array, specs)` value shape, and
  treating a `None`-mask counting axis as something `__call__` can bind/reduce.
- `_input/test_expression_1.py` is a Python operator-precedence issue, not an
  evaluation bug: `^`/`|` bind looser than `+`, so
  `a * (bi_var | e3) ^ e3 + (b * (bi_var ^ e3) | e3)` parses as
  `(a * (bi_var | e3)) ^ (e3 + (b * (bi_var ^ e3) | e3))`. Sums of products
  must be parenthesised. This is documented, not "fixed" in code.

## Decisions (confirmed)

- No `MVTensor(masks=(...str...))` string-mask syntax and no new
  `MVLabeledTensor` binding path. A **plain** `MVTensor` variable binding is
  allowed only when it has exactly one blade axis equal (`==`) to the variable's
  mask and exactly one `None` axis; that is treated like a list of MVs (the
  `None` axis becomes an auto-named counting axis).
- A variable binding `(array, specs)` requires exactly one `BladeMask` in
  `specs`, equal (`==`) to the bound variable's mask; every other spec is a
  `str` counting-axis name (kept element-wise, mode `"_"`).
- A counting-axis reduction `(array, specs)` requires every spec to be a `str`;
  `specs` itself may be a bare `str` for a 1-D array (a single-axis spec).
  A spec equal to `"_"` means "the binding key, element-wise" (name = key, mode
  `"_"`); otherwise a spec ending in `_` is **element-wise** (kept/multiplied,
  name = `spec[:-1]`) and a spec without `_` is **contracted** (summed, name =
  `spec`). Exactly one spec's name must equal the binding key, and its mode
  decides sum vs multiply. Every other spec names a **new** counting dimension
  that is always kept element-wise (stored `"_"`), whether or not it ends in
  `_`.
- Counting-axis names must be unique within a binding and disjoint from every
  axis name already present in the expression being evaluated.
- Contracting a counting axis relabels that axis in the expression tensor from
  `"_"` to `"*"` before `contract_labeled`, so it is summed away. An
  element-wise (`_`) reduction keeps the axis in `"_"` mode and only multiplies.
- Type hints are added mechanically (no behaviour change) to **all** classes,
  functions, and methods in `py/pytanga/expression/` and `py/pytanga/tensor/`,
  using `from __future__ import annotations`, PEP 604 unions, and
  `typing.TYPE_CHECKING` for forward references.

### Fixed contract

```python
# --- variable binding (added to Expression.__call__) ---
# value = (array, specs)
#   array : np.ndarray
#   specs : Sequence, len(specs) == array.ndim, entries are:
#     * BladeMask -> the blade axis (exactly one, == variable mask)  [mode "*"]
#     * str       -> a counting-axis name (kept)                     [mode "_"]
# value = mvtensor
#   mvtensor : MVTensor with exactly one BladeMask axis (== variable mask)
#              and exactly one None axis (auto-named counting axis).
# Semantics: contract the blade axis against every occurrence of the variable;
# keep the counting axes element-wise and shared across occurrences.

expr(x_pnt=(points, ("pnt_idx", point_mask)))
expr(x_pnt=MVTensor(points, masks=(None, point_mask)))

# --- counting-axis reduction (added to Expression.__call__) ---
# key == a None-mask (counting) axis name already in the expression.
# value = scalar_array        # 1-D np.ndarray / list / tuple -> contract (sum)
# value = (array, specs)      # specs is a str, or a Sequence of str:
#   * spec == "_"         -> the binding key, element-wise (name = key, "_")
#   * spec ending in "_"  -> element-wise (kept/multiplied), name = spec[:-1]
#   * spec without "_"    -> contracted (summed), name = spec
#   * exactly one spec's name equals the binding key (its mode = sum vs multiply)
#   * every other spec is a NEW counting dimension: always kept element-wise,
#     whether or not it ends in "_"; its name must not collide with any axis
#     name already in the expression
#   * a bare str spec is allowed only for a 1-D array (single axis)

contract(pnt_idx=scalars)                                # sum over pnt_idx
contract(pnt_idx=(scalars, ("pnt_idx_",)))               # multiply, keep pnt_idx
contract(pnt_idx=(scalars, "pnt_idx_"))                  # same as above (bare str)
contract(pnt_idx=(scalars, "_"))                         # same as above (key implied)
contract(pnt_idx=(scalars2d, ("pnt_idx", "group_idx_"))) # sum pnt_idx, keep group_idx
# "group_idx" (bare) is equivalent to "group_idx_" here: it is a new dimension,
# not the binding key, so it is added as a new kept counting dimension.

# Result semantics (unchanged): partial -> Expression/AffineExpression with the
# remaining variable names and counting axes; full -> MV or nested list.
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-array-spec-variable-binding.md](./01-array-spec-variable-binding.md) | Accept `(array, specs)` and single-`None`-axis `MVTensor` variable bindings. |
| 2 | [02-counting-axis-reduction.md](./02-counting-axis-reduction.md) | Reduce a counting axis (sum or element-wise multiply) with a raw array or `(array, specs)`. |
| 3 | [03-expression-type-hints.md](./03-expression-type-hints.md) | Complete type hints in `py/pytanga/expression/`. |
| 4 | [04-tensor-type-hints.md](./04-tensor-type-hints.md) | Complete type hints in `py/pytanga/tensor/`. |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Document operator precedence and write the branch changelog. |

## Testing as you go

- New binding tests: `uv run pytest py/tests/expression/test_numpy_binding.py -q`
- Expression tests: `uv run pytest py/tests/expression/ -q`
- Tensor tests: `uv run pytest py/tests/tensor/ -q`
- Full suite (final phase): `uv run pytest`
- Lint: `uv run ruff check py/pytanga/expression py/pytanga/tensor`
- Docs build (final phase): `uv run mkdocs build --strict`

## Non-goals

- No `MVTensor(masks=(...str...))` syntax or string entries in `MVTensor.masks`.
- No counting-axis reduction on `AffineExpression` (its `__call__` keeps
  rejecting keys that are not variable names). The new *variable* tuple form and
  plain `MVTensor` form do pass through `AffineExpression.__call__` as single
  bindings.
- No change to the C++ core, blade masks, or the product-tensor machinery.
- No static type-checker gate (no mypy config); type hints are validated by
  import/pytest/ruff only.
