# Phase 3 — structured axis labels (`AxisLabel`) + list-form contraction

## Goal

Change `MVLabeledTensor` from a canonical label *string* to a structured tuple of
`AxisLabel(name, mode)` values whose `name` may be a `str` or an `int`, and
rewrite the contraction path to use `numpy.einsum`'s list form so integer names
work and the 52-letter ceiling disappears. String input remains fully supported.

## Files

- Edit: `py/pytanga/tensor/_labeled.py`
- Edit: `py/pytanga/tensor/ops.py`
- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/tensor/test_labeled_tensor.py`
- Edit: `py/tests/expression/test_expression.py` (only if label access is asserted)

## Steps

- [x] **3.1 — Add the `AxisLabel` type and parsing**
  - In `_labeled.py`, add `AxisName = str | int` and the frozen, slotted
    `@dataclass AxisLabel(name, mode="*")` from the README contract (validate
    `name` is `str`/`int` and not `bool`; validate `mode` is `"*"` or `"_"`;
    expose `is_elemwise`/`is_contract`/`__str__`).
  - Add a module-level `_parse_labels(labels) -> tuple[AxisLabel, ...]` accepting:
    - `str` → legacy `_canonicalise` path, split into `AxisLabel(char, mode)`;
    - `AxisName` → one `AxisLabel(name)`;
    - an iterable of `AxisName` → each `AxisLabel(name)`;
    - an iterable of `AxisLabel` → validated as-is;
    - an iterable of `(name, mode)` 2-tuples → coerced (convenience).
  - Check that the resulting count matches the tensor ndim in
    `MVLabeledTensor.__post_init__`.

- [x] **3.2 — Store `labels` as `tuple[AxisLabel, ...]`**
  - Change `MVLabeledTensor.__post_init__` to store
    `self.labels = _parse_labels(self.labels)`, replacing the string
    canonicalisation.
  - Add `_axis_names(labels) -> tuple[AxisName, ...]` and
    `_axis_modes(labels) -> tuple[str, ...]` as comprehensions over the
    `AxisLabel`s; reimplement the phase-1 `_axis_names` wrapper to call them.
  - Keep `_canonicalise`/`_raw_names` as string-only helpers, and add
    `_labels_str(labels) -> str` (raise if any name is not a single ASCII
    letter). Update `MVLabeledTensor.__repr__` to use `_labels_str`.
  - Export `AxisLabel` from `py/pytanga/tensor/__init__.py`.

- [x] **3.3 — Update `_labeled.py` internal consumers**
  - Rework `__getitem__`, `__setitem__`, `zeros_from_dict`, `sum`, `norm`,
    `_add_or_sub`, `_transpose`, `iter_labels`, and the scalar ops to use
    `_axis_names`/`_axis_modes` and tuple slicing instead of `_raw_names(...)` /
    `labels[:2*ax]` string slicing.
  - Preserve identical public behaviour for letter-only labels (the structured
    form is just a different encoding).

- [x] **3.4 — Rewrite `contract_labeled` to list-form einsum**
  - In `ops.py`, keep `contract(subscripts, *tensors)` (string form) intact.
  - Rework `_build_subscript`/`contract_labeled` to:
    - collect the ordered `AxisName`s and modes via `_axis_names`/`_axis_modes`,
    - assign each distinct name a small integer label in first-appearance order,
    - build the list-form `np.einsum(*args)` call (input axis lists + output
      axis list), and
    - port the existing mask-compatibility validation (`contract`'s registry)
      into this path.
  - Return an `MVLabeledTensor` with structured labels built from the kept names
    and their modes.

- [x] **3.5 — Update `_expression.py` for the new `.labels` type**
  - Replace `_raw_names(...)` uses with `_axis_names(...)` in `_add`, `_product`,
    and `_var_axes`.
  - Replace string-concat label construction in `_product`, `_involution`,
    `_apply_involution`, `_to_expression`, `_reindex_output`, and the `_evaluate`
    binding path with `AxisLabel` values (e.g. `["k"]`, or
    `[AxisLabel("k"), AxisLabel(label), AxisLabel(batch, "_")]`, or the
    `(name, mode)` convenience tuples).
  - Keep `OUT_LABEL` as the reserved string `"k"`; variable labels are still
    letters at this stage (integers arrive in Phase 4).

- [x] **3.6 — Update tensor tests**
  - In `test_labeled_tensor.py`, keep the string-input tests (constructor
    accepts `"kij"`/`"k*i*j*"`/`"i*n_"`) but assert against `_axis_names`/
    `_axis_modes` (or the new `.labels`) rather than `.labels == "..."`.
  - Add tests for: an integer-only label `[0, 1, 2]`, a mixed label
    `[("k", "*"), (0, "*"), ("n", "_")]`, `AxisLabel` validation (bad mode /
    `bool` name raise), `_labels_str` raising on integer names, and
    `contract_labeled` with integer names.

## Validation

`uv run pytest py/tests/tensor/test_labeled_tensor.py py/tests/expression/ -q`

## Notes

- This is the deliberate breaking change to the stored `labels` attribute called
  out in the README; string *input* is unaffected.
- The 52-letter ceiling disappears because list-form einsum uses integer axis
  labels, not the single-letter alphabet.
