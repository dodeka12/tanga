# Phase 2 — unified binding API in `Expression` / `AffineExpression`

## Goal

Refactor `Expression._evaluate` and `AffineExpression.__call__` so the only
accepted value forms are: a single `MV`/`int`/`float` (variable binding), a
`DataArray` (variable binding or counting-axis reduction), and a raw 1-D
`np.ndarray`/`list` (counting-axis sum sugar). Remove the
`list`/`tuple`-of-MVs, `(label, [mvs])`, plain `MVTensor`, and `(array, specs)`
tuple paths, and migrate the affected expression/affine tests.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_numpy_binding.py`
- Edit: `py/tests/expression/test_expression.py`
- Edit: `py/tests/expression/test_affine.py`

## Steps

- [x] **2.1 — Extend spec resolution**
  - In `_expression.py`, extend `_parse_count_spec` so `spec == "*"` returns
    `(key, "*")` (the binding key, contract/sum). Keep `"_"` → `(key, "_")` and
    trailing `_` → `(spec[:-1], "_")`.

- [x] **2.2 — DataArray helpers**
  - Add `_variable_dataarray_binding_tensors(data, mask, labels, used)` that
    finds the single `BladeMask` axis equal (`==`) to `mask` and builds one
    `MVLabeledTensor` per occurrence label (blade axis `(lab, "*")`, counting
    axes `(name, "_")`), reusing the validation rules from the removed
    `(array, specs)` builder.
  - Add `_count_dataarray_binding_tensor(name, data, length, used, counting_names)`:
    - `data.ndim == 1` → the single axis is the key; resolve its mode via
      `_parse_count_spec(spec, name)` (sum `"*"` or multiply `"_"`), validate
      length, return `MVLabeledTensor(MVTensor(arr, (None,)), [(name, mode)])`.
    - `data.ndim > 1` → build `(arr, data.masks)` and delegate to the existing
      `_count_array_binding_tensor` (which already enforces exactly-one key and
      keeps other axes).

- [x] **2.3 — Refactor `Expression._evaluate` input parsing**
  - Keep the variable/counting-axis split and base-tensor relabelling.
  - Replace the variable-binding value branches with:
    - `DataArray` → `_variable_dataarray_binding_tensors`.
    - `int`/`float` → single MV.
    - `MV` → single MV.
    - anything else → `TypeError` with a "use a single MV or DataArray" message.
  - Replace the counting-binding value branches with:
    - `DataArray` → `_count_dataarray_binding_tensor`.
    - raw 1-D `np.ndarray`/`list` → existing 1-D sum helper.
    - anything else → `TypeError`.
  - Remove `_is_array_spec_binding`, `_array_spec_parts`,
    `_variable_array_binding_tensors`, `_variable_mvtensor_binding_tensors`, and
    the `(label, [mvs])` / `list`/`tuple` / `MVTensor` branches (keep
    `_count_array_binding_tensor` and `_parse_count_spec`).

- [x] **2.4 — Refactor `AffineExpression.__call__`**
  - Remove `_split_bindings`, `_call_full_batch`, and `_call_batch_loop`.
  - Evaluate every term with the given bindings; combine results by summing
    element-wise, broadcasting a single `MV` against a `list` result
    (`val = r[i] if isinstance(r, list) else r`). If any term returns an
    `Expression` (partial), return a new `AffineExpression` of the per-term
    results (converting `MV`/`list` results to `Expression` where needed via the
    existing helpers).
  - Skip `_check_blades` for non-`MV` values (`DataArray`) as today.

- [x] **2.5 — Migrate tests**
  - `test_numpy_binding.py`: replace `(array, specs)` and `MVTensor` bindings
    with `DataArray`; keep the same assertions, add the `"_"`/`"*"`/1-D-implicit
    and `DataArray([mv...])` cases.
  - `test_expression.py` / `test_affine.py`: replace `list`/`(label, [mvs])`
    batch bindings with `DataArray` (or `DataArray([...])`); remove/adjust tests
    that only exercised removed forms (`e(V1=[])`, batch-only affine tests).

## Validation

`uv run pytest py/tests/expression/ -q; uv run ruff check py/pytanga/expression`

## Notes

- The broadcast step in 2.4 is the essential logic formerly in `_call_full_batch`;
  it stays because `from_tensor` materialises a kept counting axis as a list.
- Counting-axis reduction remains `Expression`-only (see the previous plan's
  non-goal); `AffineExpression` accepts `DataArray` for variable binding but does
  not accept counting-axis keys.
