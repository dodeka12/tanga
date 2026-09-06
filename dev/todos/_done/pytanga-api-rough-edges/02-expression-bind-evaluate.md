# Phase 2 — `Expression.bind()` / `Expression.evaluate()`

## Goal

Give callers who know statically whether a binding is still partial (→
`Expression`) or fully collapsed (→ `MV`) an intent-specific entry point with a
narrow return type, instead of the always-wide `MV | Expression | list` from
`__call__`.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py`
- Edit: `py/tests/expression/test_affine.py`

## Steps

- [x] **2.1 — Add `Expression.bind` / `Expression.evaluate`**
  - In `_expression.py`, add two methods in the `Evaluation` section (after
    `_evaluate`, ~line 214), both delegating to `self._evaluate(bindings, True)`
    and narrowing by a runtime `isinstance` check:
    ```python
    def bind(self, **bindings: Any) -> "Expression":
        result = self._evaluate(bindings, True)
        if not isinstance(result, Expression):
            raise ValueError(
                "bind() expected a partially-evaluated Expression, but the "
                "binding fully collapsed it. Use evaluate() or __call__()."
            )
        return result

    def evaluate(self, **bindings: Any) -> MV:
        result = self._evaluate(bindings, True)
        if not isinstance(result, MV):
            raise ValueError(
                "evaluate() expected a fully-bound MV, but the binding left "
                "variables/axes unbound (Expression) or produced a batched "
                "result (list)."
            )
        return result
    ```
  - `MV` and `Any` are already imported at module top; `Expression` is the
    enclosing class, so no new imports are required.

- [x] **2.2 — Add `AffineExpression.bind` / `AffineExpression.evaluate`**
  - In the `AffineExpression` `Evaluation` section (after `__call__`, ~line 584),
    add the same pair, delegating to `self(**bindings)` and narrowing to
    `AffineExpression` / `MV` respectively (reuse the same error wording, with
    "AffineExpression" in the `bind` message).

- [x] **2.3 — Tests: `bind` returns `Expression` and raises on full collapse**
  - In `test_expression.py`, add a `bind()` test mirroring the note's repro: a
    two-variable expression bound with only one variable returns an
    `Expression` (assert `isinstance` and the remaining `names`), and binding
    the last variable raises `ValueError`.

- [x] **2.4 — Tests: `evaluate` returns `MV` and raises on partial/batched**
  - Add an `evaluate()` test: a single-variable expression fully bound to an
    `MV` returns that `MV`; a two-variable expression with one variable left
    unbound raises `ValueError`; a `DataArray` binding that still carries a
    counting axis (batched → `list`) raises `ValueError`.
  - In `test_affine.py`, add the analogous `AffineExpression.bind`/`evaluate`
    happy-path and raise-path tests.

## Validation

`uv run pytest py/tests/expression/ -q`

## Notes

- `__call__` is intentionally left untouched as the dynamic fallback for
  interactive/exploratory use; `bind`/`evaluate` are the static-intent entry
  points.
- Use a runtime `raise` (not `typing.cast`): the check is actually executed, so
  a wrong "still partial"/"fully bound" assumption fails loudly at the point of
  the mistake — the exact rationale in the note's `_as_expression` workaround.
