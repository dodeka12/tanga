# Phase 2 — relax `_product`'s stacked guard

## Goal

Explain what `_product`'s stacked guard is for, then relax it so a stacked
(batched) expression may be composed with a constant MV or a `Variable`, while
still rejecting the composition of two stacked expressions.

## What the guard is

`_product` (`py/pytanga/expression/_expression.py`) builds `left ∘ right` by
contracting the 3-D product tensor against each operand via a single
`np.einsum`. Its `add("expr", ...)` branch loops over every non-output axis of an
operand expression and appends a fresh einsum axis (`next_ax`), then the result
labels are rebuilt as all-`"*"` (contractible) axes.

That is correct for *variable* axes, but wrong for a counting axis: a counting
axis carries `None` mask / `"_"` mode and must pass through **element-wise**
into the output, not be treated as a contractible variable axis. Because the
builder does not yet track per-axis mode, it refuses any stacked expression
operand upfront (the guard at the top of `_product`).

## Chosen relaxation

- Allow **one** stacked operand; the other side may be a constant MV or a
  `Variable` (or a non-stacked `Expression`). In those cases the counting axis
  is an independent per-entry axis and passes through untouched.
- Keep **rejecting** `stacked * stacked` (both operands stacked): aligning two
  counting axes needs explicit zip semantics (`_` vs `*`) that `_product` does
  not express yet, and silently emitting an outer product would be wrong.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py`

## Steps

- [x] **2.1 — Thread counting-axis modes through `add("expr", ...)`**
  - In `_product`, replace the `var_labels: list[str]` bookkeeping with a list of
    `(label, mode)` pairs (e.g. `var_specs: list[tuple[str, str]]`).
  - In the `kind == "expr"` branch, for each non-output axis `i`, record its
    mode from the operand's mask: `mode = "_" if e_masks[i] is None else "*"`,
    and append `(label, mode)` instead of just `label`.
  - Leave the einsum `sub`/`out_axes` logic unchanged — a counting axis becomes
    a passthrough output axis automatically because it appears in only one
    operand and in `out_axes`.

- [x] **2.2 — Build the result label string from `(name, mode)` pairs**
  - Replace
    `labels = "".join(ch + "*" for ch in raw_labels)` with a build from
    `[("k", "*"), *var_specs]`, joining each pair as `name + mode`.
  - Keep `OUT_LABEL` as the output axis name (`"k"`, mode `"*"`).

- [x] **2.3 — Relax the guard to allow one stacked operand**
  - Replace the current blanket loop with a count of stacked operands:
    ```python
    stacked = [
        kind
        for kind, val in ((Lkind, Lval), (Rkind, Rval))
        if kind == "expr" and val._has_counting_axes()
    ]
    if len(stacked) == 2:
        raise ValueError(
            "cannot compose two stacked (batched) expressions; "
            "fully evaluate one of them before the product"
        )
    ```

- [x] **2.4 — Update and extend tests**
  - In `test_expression.py`, update `test_stacked_guards`: `partial * const_mv`
    and `const_mv * partial` should now succeed (not raise) and evaluate
    correctly; add `partial * variable` and `variable * partial` cases.
  - Add a negative case: `stacked * stacked` still raises `ValueError`.
  - Assert a stacked-composition result keeps its counting axis in `"_"` mode
    (e.g. the label string contains `n_`).

## Validation

`uv run pytest py/tests/expression/test_expression.py -q`

## Notes

- Phase 3 reworks label construction to structured `AxisLabel` values; the
  mode-carrying logic introduced here is the durable part and carries over
  directly (the `(label, mode)` pairs become `AxisLabel` instances).
- `stacked * stacked` remains an explicit decision point — if per-correspondence
  product (zip) semantics are later required, that is a separate plan.
