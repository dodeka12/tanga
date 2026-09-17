# Phase 3 — Module `project_onto` dispatcher with `@overload`

## Goal

Expose `project_onto(x, other)` from `pytanga.expression`, precisely typed with
`@overload`, and keep `ty` green.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/pytanga/expression/__init__.py`
- Edit: `py/tests/expression/test_ops.py`

## Steps

- [x] **3.1 — Add `overload` to the typing import**
  - In `_expression.py`, extend `from typing import TYPE_CHECKING, Any, cast` with
    `overload`.

- [x] **3.2 — Add the dispatcher**
  - Next to `gp`/`ip`/…, add three `@overload` signatures (`MV`, `Expression`,
    `AffineExpression`) plus an implementation
    `project_onto(x, other) -> x.project_onto(other)`.

- [x] **3.3 — Export**
  - In `py/pytanga/expression/__init__.py`, import `project_onto` and add it to
    `__all__`.

- [x] **3.4 — Tests**
  - Add `project_onto(MV, mask)`, `project_onto(Expression, mask)`, and
    `project_onto(AffineExpression, mask)` cases to `test_ops.py`.

## Validation

`uv run pytest py/tests/expression/ -q && uv run ty check`

## Notes

- The methods from Phase 2 have a constant return type and do not need overloads;
  `@overload` is reserved for the dispatcher whose return type depends on `x`
  (Rule 4 of `docs/dev/architecture/typing-and-annotations.md`).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
