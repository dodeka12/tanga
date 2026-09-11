# Phase 2 — counting-axis reduction (sum or element-wise multiply)

## Goal

Let `Expression.__call__` bind a `None`-mask counting axis that is already
present in the expression, and either **sum it away** or **multiply it
element-wise and keep it**:

- `contract(pnt_idx=scalars)` sums over `pnt_idx` (1-D array).
- `contract(pnt_idx=(scalars, ("pnt_idx_",)))` multiplies each `pnt_idx` slice by
  the corresponding scalar and keeps the `pnt_idx` axis.
- `contract(pnt_idx=(scalars2d, ("pnt_idx", "group_idx_")))` sums over `pnt_idx`
  and keeps the new `group_idx` counting axis element-wise.

A spec ending in `_` means element-wise/keep; a spec without `_` means
contracted/summed.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_numpy_binding.py`

## Steps

- [x] **2.1 — Detect counting axes and split bindings**
  - In `Expression._evaluate`, compute the ordered raw axis names and masks of
    `self._tensor`; a counting axis is any non-output axis (index ≥ 1) whose mask
    is `None`.
  - Split `bindings` into variable bindings (keys in `self._names`) and
    counting-axis bindings (keys among the counting-axis names). Raise the
    existing `ValueError` for any key that is neither.

- [x] **2.2 — Add the 1-D reduction helper (sum)**
  - Add `_count_binding_tensor(name, value, length)` that accepts a 1-D
    `np.ndarray`, `list`, or `tuple` of scalars, validates `value.shape[0] ==
    length`, and returns `MVLabeledTensor(MVTensor(np.asarray(value), (None,)),
    [(name, "*")])`.

- [x] **2.3 — Add the `(array, specs)` reduction helper**
  - Add a helper for `(array, specs)` where `specs` is a `str` or a Sequence of
    `str`:
    - A spec equal to `"_"` means the binding key element-wise: name = `name`,
      mode `"_"`.
    - A spec ending in `_` (and not `"_"`) is element-wise: name `spec[:-1]`,
      mode `"_"`.
    - A spec without `_` is contracted: name `spec`, mode `"*"`.
    - Exactly one spec's axis name must equal the binding key `name`; its mode
      decides sum (`"*"`) vs element-wise multiply (`"_"`). (`"_"` resolves to
      the key, so `"_"` + `name` together are a duplicate-key error.)
    - Every other spec names a **new** counting dimension and is always kept
      element-wise (stored `"_"`), whether or not it ends in `_`.
  - Validate: a bare `str` spec is allowed only for a 1-D array; `len(specs) ==
    array.ndim`; names unique and disjoint from every axis name that remains in
    the expression after this reduction; the bound axis length equals the
    expression counting-axis length.

- [x] **2.4 — Relabel and contract**
  - For each counting-axis binding, build a copy of `self._tensor`'s labels:
    - if the binding is a sum (`name` spec without `_`, or a 1-D array), change
      that axis's mode from `"_"` to `"*"`;
    - if the binding is an element-wise multiply (`name_` spec), leave that
      axis's mode as `"_"`.
  - Append each reduction tensor (from 2.2/2.3) to the `labeled` list; new
    dimensions from non-key specs always use mode `"_"`.
  - Compute `remaining = set(self._names) - set(variable_bindings)` (counting-axis
    keys must not be treated as variables) and return the result exactly as the
    current partial/full evaluation logic does.

- [x] **2.5 — Add tests**
  - Reduce a single counting axis with `contract(pnt_idx=scalars)`; assert the
    result is an `Expression` over `bi_var` with no counting axes, and that
    binding `bi_var` yields the same MV as the manual contraction.
  - Element-wise multiply: `contract(pnt_idx=(scalars, ("pnt_idx_",)))`; assert
    the result still has a `"pnt_idx"` counting axis (mode `"_"`), and that
    binding `bi_var` yields MVs equal to `manual[i] * scalars[i]`.
  - Two counting axes: bind `x_pnt=(points, ("pnt_idx", "group_idx", point_mask))`,
    then `contract(pnt_idx=(scalars, ("pnt_idx", "group_idx_")))`; assert the
    result keeps `"group_idx"` (mode `"_"`) and drops `"pnt_idx"`. Also assert
    the bare spelling `("pnt_idx", "group_idx")` produces the same kept
    `"group_idx"` (mode `"_"`).
  - Bare-string and `"_"` shorthands: assert `(scalars, "pnt_idx_")`,
    `(scalars, ("pnt_idx_",))`, and `(scalars, "_")` all produce the same
    element-wise multiply result; assert `(scalars, "pnt_idx")` equals the raw
    `contract(pnt_idx=scalars)` sum form.
  - Error cases: unknown counting-axis key raises; wrong length raises; duplicate
    or colliding kept-axis names raise (including a new name that collides with
    an existing axis name); a bare `str` spec on a non-1-D array raises; and
    `"_"` together with an explicit key spec raises a duplicate-key error.

## Validation

`uv run pytest py/tests/expression/test_numpy_binding.py -q`

## Notes

- The relabel-to-`"*"` step is required for sums because `contract_labeled`'s
  `_build_subscript` keeps a shared name element-wise whenever either occurrence
  has mode `"_"`; contracting requires both occurrences to be `"*"`.
- Element-wise (`_`) reduction does **not** relabel: both occurrences stay `"_"`,
  so `contract_labeled` keeps the axis and multiplies along it.
- `AffineExpression.__call__` is intentionally left rejecting counting-axis keys
  (they are not in `self.names`) — see Non-goals.
