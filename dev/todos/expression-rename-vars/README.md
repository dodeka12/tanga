# Expression Variable Rename & Unify — Overview

**Created:** 2026-09-16 | **Status:** Done | **Branch:** `feat/viz-detached-subtree`

## Goal

Let expressions that were built independently from *separately-created*
`Variable` instances with the same name (or different names sharing the same
blade mask) be re-keyed onto one canonical variable, so they merge into a single
expression under `+`/`-` instead of remaining an `AffineExpression` of distinct
terms.  This enables the "many class instances each build an expression with a
variable, then combine them" pattern.

## Architecture (short)

- `pytanga.expression` keys variables by an integer **label block**
  (`Variable.labels` from `_labels.allocate_block`), not by `name`.  Two
  `Variable("X", mask)` instances get different blocks, so their expressions do
  not merge (`_add` merges only when the axis-label sequences match).
- A pure **relabel** re-keys a variable's axis labels onto a target `Variable`'s
  block; the tensor data (the multilinear form) is unchanged.  All three public
  operations are built on one private helper, `Expression._substitute(mapping)`.
- File to edit: `py/pytanga/expression/_expression.py` (plus `__init__.py`).

## Canonical contract (fixed up front)

### 1. `Expression._substitute(mapping) -> Expression` (private)

`mapping: dict[str, Variable]` maps variable *names* to target `Variable`s.

- **Lenient**: names in `mapping` that are not in `self._names` are skipped.
- For each present source name `n`, require `mapping[n].mask == self._masks[n]`
  (`BladeMask.__eq__`: same algebra + same ids); else `ValueError`.
- Group sources by target (`id(target)`).  Each source's occurrences take the
  next free slots of `target.labels`; a target whose name is already present (or
  several sources mapping to one target) **merges** occurrences into one block.
  Total occurrences per target must be ≤ `len(target.labels)`; else `ValueError`.
- Rebuild `_tensor.labels` via an `old_label → new_label` map, and produce new
  `_names`/`_masks`; the output axis `"k"` and any `None`-mask counting axes are
  untouched.  Returns a new `Expression`.

### 2. `Expression.rename_var(old, new_name) -> Expression`

- `old`: `str` or `Variable` (uses its `.name`); must be present (`ValueError`).
- `new_name`: `str`; must not collide with a different existing name
  (`ValueError`).
- Name-only: change the `_names` key, keep labels/masks/tensor.

### 3. `Expression.bind(**bindings)` (extended, backward-compatible)

- Split bindings: values that are `Variable` → **substitutions**; all other
  values → value bindings.
- Apply substitutions first (strict: each substitution name must be present,
  else `ValueError`), then value bindings through the existing `_evaluate` path.
- With only substitutions (no value bindings), return the substituted
  `Expression` — never raise the "fully collapsed" error.
- Existing value-binding behaviour is unchanged.

### 4. `AffineExpression` mirrors

- `_substitute` / `rename_var` distribute over `self._terms`; `bind` splits
  substitutions (per term) then value-binds the re-keyed sum.  All return
  `AffineExpression`.

### 5. `unify(expressions, **mapping) -> list[Expression | AffineExpression]`

- Module-level in `pytanga.expression`.
- `mapping`: name → `Variable` (same form as `bind`); **lenient** per expression
  (absent names skipped).
- Returns a new list of re-keyed expressions, same order.  Callers combine with
  `+` / `sum`.

## Decisions (confirmed)

- `bind` is repurposed for variable substitution: a `Variable` binding value
  means "replace that variable"; it does not collide with value binding because
  the value type distinguishes the two cases.
- `rename_var(old, new_name)` is **name-only** (keeps the label block); full
  re-keying + renaming is `bind(old_name=target_variable)`.
- `unify` returns a **list** (composable); combining is a separate `+`.
- Mask change (reindexing onto a different-mask variable) is out of scope — the
  target mask must equal the source mask.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-substitute-rename-var.md](./01-substitute-rename-var.md) | `Expression._substitute` + `Expression.rename_var` + tests |
| 2 | [02-bind-variable-substitution.md](./02-bind-variable-substitution.md) | Extend `Expression.bind` to accept `Variable` values + tests |
| 3 | [03-affine-expression-support.md](./03-affine-expression-support.md) | `AffineExpression._substitute`/`rename_var`/`bind` + tests |
| 4 | [04-unify-module-function.md](./04-unify-module-function.md) | Module-level `unify()` + export + tests |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | User docs + example + changelog + full validation |

## Testing as you go

- Python: `uv run pytest py/tests/expression/test_rename.py -q`
- Lint: `uv run ruff check py/pytanga/expression py/tests/expression/test_rename.py`
- Types: `uv run ty check py/pytanga/expression`
- Example docs: `uv run python tools/generate-example-docs.py --check`

## Non-goals

- No mask change / reindexing (projecting a variable onto a different blade mask).
- No automatic canonicalization at `Variable(...)` construction (explicit
  operations only).
- No change to `__call__` / `evaluate` (they stay value-only).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
work touches, so the new code aligns with the documented architecture.  If this
work introduces or changes architecture, update the developer docs.

Relevant docs: `docs/py/ga/expression/index.md` and
`docs/py/ga/expression/usage.md` (the authoritative Python expression API);
`docs/dev/architecture/system-overview.md` (module layering).  This work is
additive (new methods + one module function) and changes no documented
architecture.
