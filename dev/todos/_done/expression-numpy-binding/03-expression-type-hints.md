# Phase 3 — expression subsystem type hints

## Goal

Add complete parameter and return type hints to every class, function, and method
in `py/pytanga/expression/`, including the new helpers from Phases 1–2, without
changing behaviour.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/pytanga/expression/_variable.py`
- Edit: `py/pytanga/expression/_labels.py`
- Edit: `py/pytanga/expression/__init__.py` (docstring/`__all__` only, if needed)

## Steps

- [x] **3.1 — `_expression.py` class methods**
  - Annotate `Expression.__init__`, `names`, `masks`, `out_mask`, `algebra`,
    `ndim`, `_var_axes`, `__call__`, `_evaluate`, the arithmetic/involution
    dunders, `_scale`, `inv`, `_variable_matrix`, `lstsq`, and `svd`.
  - Use `dict[str, ...]`, `tuple[int, ...]`, `BladeMask`, `MV`,
    `MVLabeledTensor`, `MVTensor`, and `Any`/`TYPE_CHECKING` forward references
    where the concrete type is unavailable at runtime.
  - For operator dunders that can return `NotImplemented`, annotate the return
    as the concrete type `| NotImplementedType` (or a permissive union with
    `Any`) so callers understand the fallback path.

- [x] **3.2 — `_expression.py` `AffineExpression` + module helpers**
  - Annotate `AffineExpression` and its methods (`terms`, `names`, `masks`,
    `_union_masks`, `out_mask`, `algebra`, `__call__`, `_call_singles`,
    `_call_full_batch`, `_call_batch_loop`, arithmetic/involution dunders,
    `_scale`, `inv`).
  - Annotate every module-level helper: `_items_of`, `_split_bindings`,
    `_coerce_addend`, `_affine_add`, `_operand`, `_value_mask`, `_product`,
    `_to_expression`, `_reindex_output`, `_add`, `_involution_tensor`,
    `_apply_involution`, `_involution`, `_check_blades`, `_validate_items`,
    `_next_batch_label`, and the Phase 1/2 helpers.
  - Keep `from __future__ import annotations` and use `TYPE_CHECKING` for the
    `MV`/`Algebra` imports that are runtime-lazy.

- [x] **3.3 — `_variable.py`**
  - Annotate all arithmetic/involution methods (`__mul__`, `__rmul__`, `__or__`,
    `__ror__`, `__xor__`, `__rxor__`, `__neg__`, `__add__`, `__radd__`,
    `__sub__`, `__rsub__`, `__invert__`, `conj`), including `NotImplemented`
    fallbacks where applicable.

- [x] **3.4 — `_labels.py`**
  - Verify `max_variables`, `allocate_block`, `allocate_label`,
    `block_for_label`, `_reset_allocator` are fully annotated; add any missing
    return/param types.

- [x] **3.5 — Import/lint/behaviour check**
  - Confirm the package imports cleanly and the expression test suite passes
    unchanged.

## Validation

`uv run pytest py/tests/expression/ -q; uv run ruff check py/pytanga/expression`

## Notes

- Type hints only; no runtime refactoring in this phase.
- `dict`/`list`/`tuple`/`set` annotations should be subscripted
  (`dict[str, BladeMask]`, `list[MV]`, `tuple[int, ...]`, `set[str]`).
