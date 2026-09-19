# Phase 3 — `AffineExpression` composition and edge cases

## Goal

Confirm `AffineExpression.bind/__call__` inherit composition through their
per-term delegation to `Expression._evaluate`, and lock down the error surface:
mask mismatch, counting axes, name collisions, self-reference, and duplicate
free names.

## Files

- Edit: `py/pytanga/expression/_expression.py` (docstrings + any collision
  fixes)
- Edit: `py/tests/expression/test_bind_expression.py`

## Steps

- [x] **3.1 — `AffineExpression.bind` with an `Expression` value**
  - `aff = (Omega_b * a) + (Omega_b * b)`; `aff.bind(Omega_b=omega_local)`
    returns an `AffineExpression` whose terms carry `Omega`; binding `Omega` to
    an `MV` matches the numeric reference `e1 * w * e1` sandwiched per term.

- [x] **3.2 — Collision: inner free name equals a remaining host variable**
  - Host `x * y`; bind `y` to an expression with free `x` → `ValueError`.

- [x] **3.3 — Collision: inner free name equals a substituted-away name**
  - Host `y`; bind `y` to an expression with free `y` (self-reference) →
    `ValueError`.

- [x] **3.4 — Collision: duplicate free name across two bindings**
  - Host `y * z`; bind both `y` and `z` to expressions that each introduce free
    `Omega` → `ValueError` (v1).

- [x] **3.5 — Counting/batch axes rejected**
  - Build an inner expression with a `None`-mask counting axis (bind a variable
    to a `DataArray`, keep the counting axis); bind a host variable to it →
    `ValueError`.

- [x] **3.6 — Docstrings**
  - Update `Expression.bind`, `Expression.__call__`,
    `AffineExpression.bind/__call__` to document the third value kind and the
    v1 limitations (mask must match, no counting axes, collision rules).

## Validation

`uv run pytest py/tests/expression/test_bind_expression.py -q && uv run ruff check py/pytanga/expression/_expression.py py/tests/expression/test_bind_expression.py && uv run ty check py/pytanga/expression`

## Notes

- `AffineExpression.bind` routes `Expression` values through its existing
  `expr(**values)` → per-term `term._evaluate(sub, False, ...)`; no new dispatch
  should be required — verify rather than assume.
- Two terms that introduce the same inner free name get *distinct* blocks (one
  per term call), so the affine sum stays affine instead of merging; that is
  correct and matches the README non-goal.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
