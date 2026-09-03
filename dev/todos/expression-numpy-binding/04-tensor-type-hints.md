# Phase 4 — tensor subsystem type hints

## Goal

Add complete parameter and return type hints to every class, function, and method
in `py/pytanga/tensor/`, without changing behaviour.

## Files

- Edit: `py/pytanga/tensor/_data.py`
- Edit: `py/pytanga/tensor/_labeled.py`
- Edit: `py/pytanga/tensor/convert.py`
- Edit: `py/pytanga/tensor/ops.py`
- Edit: `py/pytanga/tensor/product.py`
- Edit: `py/pytanga/tensor/__init__.py` (docstring/`__all__` only, if needed)

## Steps

- [x] **4.1 — `_data.py`**
  - Annotate `_rebuild_mvtensor`'s `key` parameter and `MVTensor.__getitem__`'s
    `key` parameter (a permissive `Any`/index union is acceptable because NumPy
    indexing accepts many shapes).
  - Confirm `MVTensor.__post_init__`, `shape`, `algebra`, `__repr__`,
    `mul_scalar`, `div_scalar`, `rdiv_scalar`, `zeros`, `zeros_like` are fully
    annotated; add any missing parameter/return types.

- [x] **4.2 — `_labeled.py`**
  - Annotate `_canonicalise`, `_raw_names`, `_axis_names`, `_mode_at`,
    `_is_elemwise`, `_validate_labels`, `_extended_from_raw`, `_parse_labels`,
    `_axis_modes`, `_labels_str`, `_labels_from_names`.
  - Annotate `AxisLabel` (`__post_init__`, `is_elemwise`, `is_contract`,
    `__str__`) and `MVLabeledTensor` (`__post_init__`, `__repr__`, `ndim`,
    `shape`, `data`, `__getitem__`, `__setitem__`, `zeros`, `zeros_from_dict`,
    scalar ops, `sum`, `norm`, `__mul__`/`__rmul__`/`__truediv__`/`__rtruediv__`,
    `__add__`/`__radd__`/`__sub__`/`__rsub__`, `_add_or_sub`, `_transpose`,
    `iter_labels`).
  - Use `AxisName`/`AxisLabel` in signatures and subscripted builtins
    (`tuple[AxisLabel, ...]`, `tuple[AxisName, ...]`).

- [x] **4.3 — `convert.py`**
  - Confirm `to_tensor` and `from_tensor` (and the nested `_build`/`_recurse`)
    are fully annotated; add any missing types.

- [x] **4.4 — `ops.py`**
  - Annotate `_parse_subscripts`, `_check_masks_compatible`, `contract`,
    `_build_subscript`, and `contract_labeled`; give `_build_subscript` explicit
    parameter and return types (`tuple[list[list[AxisName]], list[AxisName],
    list[AxisName], dict[AxisName, str]]` or a small `NamedTuple` if clearer).

- [x] **4.5 — `product.py`**
  - Confirm `product_tensor`, `product_tensor_rev`, `product_tensor_conj` are
    fully annotated; add any missing types.

- [x] **4.6 — Import/lint/behaviour check**
  - Confirm the package imports cleanly and both tensor and expression test
    suites pass unchanged.

## Validation

`uv run pytest py/tests/tensor/ py/tests/expression/ -q; uv run ruff check py/pytanga/tensor py/pytanga/expression`

## Notes

- Type hints only; no runtime refactoring in this phase.
- Prefer `np.ndarray` for NumPy arrays and `AxisName`/`BladeMask`/`MVTensor`/
  `MVLabeledTensor` for the domain types already exported from the package.
