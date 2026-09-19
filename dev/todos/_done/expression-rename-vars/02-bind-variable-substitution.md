# Phase 2 — Extend `Expression.bind` for variable substitution

## Goal

Make `expr.bind(X=X)` (a `Variable` binding value) substitute the variable,
without changing the existing value-binding behaviour.

## Files

- Edit: `py/pytanga/expression/_expression.py`

## Steps

- [x] **2.1 — Split bindings and apply substitutions first**
  - In `Expression.bind`, split `bindings` into `subs` (`Variable` values) and
    `values` (everything else).
  - For each substitution name, require it to be present (strict) and call
    `self._substitute(...)`; when there are no `values`, return the substituted
    `Expression` directly.
  - Otherwise run the existing `self._evaluate(values, True)` path on the
    substituted expression and keep the "fully collapsed" `ValueError`.

- [x] **2.2 — Preserve `ScalarExpression.bind`**
  - `ScalarExpression.bind` delegates to `super().bind`; confirm a substitution
    on a `ScalarExpression` still re-wraps through `_unwrap_scalar` (the result
    stays a `ScalarExpression`).

- [x] **2.3 — Tests**
  - `e.bind(X=X)` (canonical) returns a new `Expression` with `X` re-keyed;
    adding it to another re-keyed expression merges.
  - `e.bind(X=canonical_Y)` renames + unifies; `e.bind(Z=X)` raises (unknown).
  - `e.bind(V1=x)` still returns a partial `Expression` (regression); mixed
    `e.bind(X=X, V1=x)` substitutes first, then value-binds.

## Validation

`uv run pytest py/tests/expression/test_rename.py -q && uv run ruff check py/pytanga/expression/_expression.py && uv run ty check py/pytanga/expression`

## Notes

- `bind` is the only evaluation entry point that accepts `Variable` values;
  `__call__` and `evaluate` remain value-only (a `Variable` there still raises
  `TypeError` from `_evaluate`).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
