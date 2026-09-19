# Phase 3 — `AffineExpression` support

## Goal

Mirror `_substitute`, `rename_var`, and the extended `bind` on
`AffineExpression`, distributing over its terms.

## Files

- Edit: `py/pytanga/expression/_expression.py`

## Steps

- [x] **3.1 — `AffineExpression._substitute(mapping)`**
  - `return AffineExpression([t._substitute(mapping) for t in self._terms])`.

- [x] **3.2 — `AffineExpression.rename_var(old, new_name)`**
  - `return AffineExpression([t.rename_var(old, new_name) for t in self._terms])`.

- [x] **3.3 — `AffineExpression.bind`**
  - Split `Variable` values (substitutions, applied per term) from value
    bindings; then run the existing `self(**values)` path on the re-keyed
    `AffineExpression`, keeping the "fully collapsed" `ValueError`.

- [x] **3.4 — Tests**
  - A sum of two separately-created `Variable("X")` terms, re-keyed via `bind`,
    then combined, reduces to a single merged expression and evaluates correctly.
  - `rename_var` distributes across terms.

## Validation

`uv run pytest py/tests/expression/test_rename.py -q`

## Notes

- `AffineExpression.bind` currently delegates to `self(**bindings)`; bypass that
  for the substitution part so `__call__` stays value-only.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.
