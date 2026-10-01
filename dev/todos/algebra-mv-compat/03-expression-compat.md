# Phase 3 — Relax `Expression` algebra-identity checks

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Let `Expression` operands and `project_onto` targets from equal-parameter
algebras combine.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- New: `py/tests/expression/test_expression_compat.py`

## Steps

- [x] **3.1 — operand guard (l.1965)**
  - `if m_L.algebra is not m_R.algebra:` → `if m_L.algebra != m_R.algebra:`
    (keep the message "expression operands belong to different algebras").

- [x] **3.2 — `project_onto` guard (l.776)**
  - `if target.algebra is not self.algebra:` → `if target.algebra !=
    self.algebra:` (keep the message).

- [x] **3.3 — Tests**
  - New `py/tests/expression/test_expression_compat.py` (annotate `-> None`):
    build two expressions from two `BasisN3()` instances with the same
    `BladeMask` and combine them (e.g. `+` and `*`) — no `ValueError`; a
    genuinely different algebra still raises.

## Validation

```
uv run pytest py/tests/expression -q
```

## Notes

- The expression layer's operand check is a `raise ValueError` (not an
  `assert`); keep it a raise.
