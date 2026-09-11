# Phase 1 — `(array, specs)` and `MVTensor` variable binding

## Goal

Teach `Expression._evaluate` to accept a variable bound to a plain NumPy array
via the tuple form `(array, specs)`, and via a plain `MVTensor` with exactly one
blade axis matching the variable mask and exactly one `None` axis. Both forms
return a partial `Expression` with the remaining variables plus counting axes;
the blade axis is contracted against every occurrence of the variable and the
counting axes are kept element-wise.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_numpy_binding.py`

## Steps

- [x] **1.1 — Add array-spec parsing helpers**
  - Add `_is_array_spec_binding(value) -> bool` returning `True` iff `value` is
    a `tuple`/`list` of length 2 whose first element is an `np.ndarray` and whose
    second is a `tuple`/`list` **or a bare `str`** (a single-axis spec).
  - Add `_array_spec_parts(value) -> tuple[np.ndarray, Sequence]` (or equivalent)
    that validates and returns `(array, specs)`; a bare `str` spec is normalised
    to a 1-tuple `(specs,)` and is only valid when `array.ndim == 1`. Raise
    `TypeError` if the value is not an `(array, specs)` pair.

- [x] **1.2 — Add the `(array, specs)` per-occurrence builder**
  - Add a helper `_variable_array_binding_tensors(value, mask, labels, used)`
    returning one `MVLabeledTensor` per occurrence label in `labels`:
    - `array = np.asarray(value[0])`, `specs = value[1]`.
    - Require `len(specs) == array.ndim`.
    - Find the single spec that is a `BladeMask`; require it equals `mask`
      (`==`). Every other spec must be a `str`.
    - Require the counting `str` names to be unique and disjoint from `used`
      (the set of axis names already in the expression).
    - Build `MVTensor(array, masks=...)` with `None` for counting axes and the
      `BladeMask` for the blade axis.
    - For each occurrence label `lab`, build an `MVLabeledTensor` whose blade
      axis is `(lab, "*")` and whose counting axes are `(name, "_")`.

- [x] **1.3 — Add the `MVTensor` per-occurrence builder**
  - Add a helper `_variable_mvtensor_binding_tensors(value, mask, labels, used)`
    for `value` an `MVTensor`:
    - Require `value.ndim == 2`, with exactly one `BladeMask` axis equal (`==`)
      to `mask` and exactly one `None` axis (reject any other shape).
    - Assign the single `None` axis an auto counting name via
      `_next_batch_label(used)` (reusing the same name across occurrences, like
      the list-of-MVs path).
    - For each occurrence label `lab`, build an `MVLabeledTensor` whose blade
      axis is `(lab, "*")` and whose `None` axis is `(auto_name, "_")`.

- [x] **1.4 — Wire the new bindings into `Expression._evaluate`**
  - In the variable-binding loop, after the existing `(str, list)` named-batch
    branch and **before** the generic `isinstance(value, (list, tuple))` batch
    branch:
    - when `_is_array_spec_binding(value)` is true, use the 1.2 builder;
    - when `isinstance(value, MVTensor)` is true, use the 1.3 builder.
  - Append the resulting tensors to the `labeled` list; keep the existing
    `used`/`_next_batch_label` bookkeeping unchanged for the legacy
    list/`(label, [mvs])` paths.

- [x] **1.5 — Let `AffineExpression` pass the new bindings through**
  - In `_split_bindings`, classify `(array, specs)` (via `_is_array_spec_binding`)
    as a **single** binding, not a batch (`MVTensor` is already non-list/tuple).
  - In `AffineExpression.__call__`, only call `_check_blades` on single values
    that are `MV` (after the existing int/float → MV coercion); skip the new
    array-spec tuples and `MVTensor` values so they are forwarded to each term's
    `_evaluate`.

- [x] **1.6 — Add tests**
  - New `py/tests/expression/test_numpy_binding.py` (reset the label allocator
    in `setup_method`):
    - Build `expr = x_pnt ^ (bi_var | x_pnt)` with `BasisN3`,
      `bi_mask = BladeMask(N3, [E12, E13, E23])`,
      `point_mask = BladeMask(N3, [E1, E2, E3])`.
    - Bind `x_pnt=(points, ("pnt_idx", point_mask))` with
      `points = np.random.default_rng(0).random((100, 3))`; assert the result is
      an `Expression`, `names == {"bi_var"}`, `_has_counting_axes()` is true, and
      its labels contain a `"pnt_idx"` axis with mode `"_"`.
    - Bind `x_pnt=MVTensor(points, masks=(None, point_mask))` (and the transposed
      `(point_mask, None)` layout); assert both produce the same partial
      `Expression` shape as the tuple form (with an auto-named counting axis).
    - Bind `bi_var` to a fixed bivector MV and compare the result (list of MVs)
      against the manual `contract_labeled` path from
      `_input/test_expression_2.py`.
    - Add a two-counting-axis case `(points, ("pnt_idx", "group_idx", point_mask))`
      with a `(100, 2, 3)` array to lock in multi-axis support.
    - Add error cases: missing `BladeMask`, non-matching mask, wrong spec
      length, a counting name that collides with an existing axis name, and an
      `MVTensor` with more than one `None` axis or the wrong blade mask.

## Validation

`uv run pytest py/tests/expression/test_numpy_binding.py -q`

## Notes

- This phase only *introduces* counting axes; reducing them is Phase 2.
- `_check_blades` is deliberately skipped for array-spec tuples and `MVTensor`
  values (the data is already restricted to the variable mask by construction).
- The `MVTensor` binding is the "just like a list of multivectors" path: its
  `None` axis is treated as an unnamed batch axis and gets an auto label.
