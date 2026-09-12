# Phase 1 — Counting-axis reduction + broadcast at the `AffineExpression` top level

## Goal

Let `AffineExpression.__call__` (and therefore `bind`/`evaluate`) recognize and
reduce a counting-axis binding (`affine_expr(pt=weights)`) across a sum: terms
that carry the axis reduce it, and terms that never carried the batched variable
broadcast as constants (scaled by `weights.sum()`) instead of raising.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/expression/_expression.py`

## Steps

- [x] **1.1 — Add `Expression._counting_axes()`**
  - Add a private method on `Expression` returning `dict[str, int]`: iterate
    `_axis_names(self._tensor.labels)` for axes `1..n`, keeping entries whose
    `self._tensor.tensor.masks[i] is None`, mapped `name -> shape[i]`.
  - Place it next to the existing `_var_axes` helper.

- [x] **1.2 — Add `AffineExpression._counting_axes_union()`**
  - Union each term's `_counting_axes()` into one `dict[str, int]`; if a name is
    carried by two terms with different lengths, raise `ValueError`.

- [x] **1.3 — Add broadcast support to `Expression._evaluate`**
  - Add an optional third parameter `extra_counting: dict[str, int] | None =
    None`.
  - `unknown = set(bindings) - set(self._names) - set(counting) -
    set(extra_counting or {})`.
  - For a binding key in `extra_counting` but not in this term's `counting`:
    require a sum-reduction value (raw 1-D array; `_count_binding_mode == "*"`)
    and record a broadcast scale `float(np.sum(value))`; raise `ValueError` for
    element-wise (`"_"`) broadcast.
  - After computing the result (`MV` / `Expression` / batched list), apply each
    broadcast scale via scalar multiplication (recursively over list leaves).

- [x] **1.4 — Update `AffineExpression.__call__`**
  - `counting = self._counting_axes_union()`.
  - `unknown = set(bindings) - self.names - set(counting)`; raise on non-empty.
  - Split bindings: `var_bindings` = keys in `self.names`, `count_bindings` =
    keys in `counting`.  Apply the scalar→MV conversion and `_check_blades` only
    to `var_bindings` (against `self._union_masks()`).
  - Per term: `sub = {k: v for k, v in var_bindings.items() if k in term.names}`
    plus `{k: v for k, v in count_bindings.items()}`, then
    `term._evaluate(sub, False, extra_counting=counting)`.

## Validation

`uv run pytest py/tests/expression/test_affine.py py/tests/expression/test_expression.py -q`

## Notes

- `_combine_terms` already re-sums per-term results, so per-term reduction +
  broadcast and re-combining is sufficient.
- Leave `bind`/`evaluate` untouched: they delegate to `__call__`.
- Existing `test_unknown_variable` must stay green: a genuinely unknown key is
  not a variable name nor a union counting axis, so it still raises.
- Broadcast applies only to sum-reduction (`"*"` mode); element-wise (`"_"`)
  broadcast is out of scope.
