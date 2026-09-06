# Phase 1 — `+`/`-` merge for stacked expressions

## Goal

Allow `_add` to merge two stacked (batched) `Expression`s when their ordered
axis-name sequences match exactly, instead of raising unconditionally. This is
the concrete fix from `dev/notes/pytanga-batched-expression-merge.md`.

## Files

- Edit: `py/pytanga/tensor/_labeled.py`
- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py`

## Steps

- [x] **1.1 — Add the stable `_axis_names` accessor**
  - In `py/pytanga/tensor/_labeled.py`, add
    `def _axis_names(labels) -> tuple[str, ...]: return tuple(_raw_names(labels))`
    next to `_raw_names`.
  - It returns the ordered raw axis names (single characters for now). Phase 3
    will reimplement it over the structured labels without changing its meaning.

- [x] **1.2 — Relax the guard in `_add`**
  - In `py/pytanga/expression/_expression.py`, import `_axis_names` instead of
    `_raw_names`.
  - Rewrite `_add` (near the end of the file) to:
    ```python
    def _add(left, right, subtract: bool = False):
        L = _to_expression(left)
        R = _to_expression(right)
        same_axes = _axis_names(L.tensor.labels) == _axis_names(R.tensor.labels)
        if (L._has_counting_axes() or R._has_counting_axes()) and not same_axes:
            raise ValueError(
                "cannot add stacked (batched) expressions with different axis "
                "layouts; fully evaluate them before addition"
            )
        if same_axes:
            union = L.out_mask.union(R.out_mask)
            Lt = _reindex_output(L, union)
            Rt = _reindex_output(R, union)
            result = Lt - Rt if subtract else Lt + Rt
            return Expression(result, dict(L.names), dict(L.masks))
        return AffineExpression([L, R._scale(-1.0) if subtract else R])
    ```
  - Keep the `AffineExpression` fallback for genuinely different layouts.

- [x] **1.3 — Update and extend tests**
  - In `py/tests/expression/test_expression.py`, change `test_stacked_guards` so
    `partial + partial` now **merges** into a single `Expression` (assert it no
    longer raises and evaluates correctly), instead of expecting `ValueError`.
  - Add a regression test mirroring the note: build `motor * X` and `Y * motor`
    in `BasisN3`, bind `X`/`Y` to their own batches, and assert `lm - rm` is a
    single stacked `Expression` whose evaluation matches the per-entry
    `motor * x_i - y_i * motor`.
  - Add a negative case: two stacked expressions with *different* counting-axis
    labels still raise `ValueError`.

## Validation

`uv run pytest py/tests/expression/test_expression.py -q`

## Notes

- Same raw labels imply same variable occurrences because the letter pool never
  reuses a label, so no extra mask check is required here.
- If the counting axes share a label but have different lengths, the merge's
  `Lt - Rt` / `Lt + Rt` raises a NumPy broadcast error — an acceptable, correct
  failure for a genuine mismatch.
