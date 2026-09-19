# Phase 4 — Module-level `unify()`

## Goal

Add `unify(expressions, **mapping)` to re-key variables across a list in one
call (lenient per expression), and export it.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/pytanga/expression/__init__.py`

## Steps

- [x] **4.1 — Add `unify(expressions, **mapping)`**
  - Signature `def unify(expressions, **mapping) -> list[...]`; return
    `[e._substitute(mapping) for e in expressions]`.
  - Validate every `mapping` value is a `Variable`; raise `TypeError` otherwise.

- [x] **4.2 — Export**
  - Import `unify` in `py/pytanga/expression/__init__.py` and add it to
    `__all__`.

- [x] **4.3 — Tests**
  - `unify([e1, e2], X=X, Y=X)` where `e1` has `X` and `e2` has `Y` → both
    re-keyed to canonical `X`; their sum merges and evaluates correctly.
  - Lenient: a name absent from a given expression is skipped.
  - Mask mismatch → `ValueError`.

## Validation

`uv run pytest py/tests/expression/test_rename.py -q && uv run ruff check py/pytanga/expression && uv run ty check py/pytanga/expression`

## Notes

- `unify` is the only *lenient* public entry (skips absent names); `bind` and
  `rename_var` stay strict.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
