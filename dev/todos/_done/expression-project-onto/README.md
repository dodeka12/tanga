# Expression `project_onto`, `BladeMask` empty construction, `TwistBivector` — Overview

**Created:** 2026-09-17 | **Status:** Done | **Branch:** `fix/expression-unify`

## Goal

Add `project_onto()` as an expression-system operation (mirroring
`MV.project_onto`), so an `Expression` / `AffineExpression` can be restricted to a
blade subspace.  Along the way, fix the latent `BladeMask` bug where
`BladeMask(alg, [])` (an explicit empty id list) silently returns the full algebra
mask, and ship a runnable N3 example that projects an expression with `einf`/`eo`
components onto the Euclidean basis.  Finally, add a N3-only `TwistBivector`
geometry operator (rotor + translator → motor → twist-bivector blade mask).

## Architecture (short)

- `BladeMask(alg)` (no ids) → full mask; `BladeMask(alg, [])` → empty mask.  Fix
  via a `None` sentinel default for `ids` in `py/pytanga/blade_mask/_mask.py`;
  this also makes `intersection` / `union` / `from_mv` correct for the empty case.
- `Expression.project_onto(other)` / `AffineExpression.project_onto(other)`
  restrict the output axis to `other` (`MV` → its non-zero blades, `BladeMask` →
  exact id membership), pruning the output mask to the intersection.  A disjoint
  intersection collapses to a constant zero expression.  Implemented by a
  `_restrict_output` helper next to `_reindex_output` in
  `py/pytanga/expression/_expression.py`.
- A module-level `project_onto(x, other)` dispatcher (in `pytanga.expression`,
  next to `gp`/`ip`/…) uses `@overload` for `MV` / `Expression` /
  `AffineExpression` return types, per `docs/dev/architecture/typing-and-annotations.md`
  Rule 4.
- `TwistBivector` is an N3-only geometry operator whose blade mask is the
  intersection of the motor blade mask and the grade-2 mask of CGA; it is built
  by creating a motor and projecting onto that mask (`MV.project_onto`).

## Decisions (confirmed)

- **Prune, don't zero.** `project_onto` reduces the output mask to the kept blades
  (matching `MV.project_onto`), rather than keeping the original mask with zeroed
  rows.
- **Disjoint → zero.** A projection that keeps no blades returns a constant zero
  expression (`Expression(alg.multivector({}))`); `AffineExpression.project_onto`
  drops annihilated terms and, if all are dropped, returns a single zero term.
- **`BladeMask` sentinel.** `ids` default changes `()` → `None`; `None` means "not
  given → full (unless `grades` narrows)", an explicit empty iterable means "empty
  mask".
- **`@overload` lives on the module dispatcher** (return type depends on `x`), not
  on the methods (constant return type).
- **No `MV.project_onto(expression)`** dispatch — the subspace argument is always a
  fixed `MV` / `BladeMask`, never an expression.
- **`TwistBivector` is an `Operator`** (versor-derived), placed in
  `operators.py` and the `Operator` union, so `create()` / `mask_for()` /
  `create_var()` all work through the existing generic paths.
- **`TwistBivector` is N3-only.** `create_operator` raises `TypeError` for any
  other basis; no `create_twist_bivector` exists in the other `create_*` modules.
- **Twist mask = `mask_for(alg, Motor) ∩ BladeMask(alg, grades=[2])`** — the 9
  motor bivectors (rotation + translation), excluding the `e∞∧e₀` dilator
  bivector.  "create_mask" in the request maps to the existing `mask_for`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-blademask-empty-construction.md](./01-blademask-empty-construction.md) | Fix `BladeMask` empty construction + tests |
| 2 | [02-expression-project-onto.md](./02-expression-project-onto.md) | `_restrict_output` + `Expression`/`AffineExpression.project_onto` + tests |
| 3 | [03-project-onto-dispatch-overload.md](./03-project-onto-dispatch-overload.md) | Module `project_onto` dispatcher with `@overload` + export + tests |
| 4 | [04-example-project-onto-euclidean.md](./04-example-project-onto-euclidean.md) | N3 Euclidean-projection example script + example-docs regen |
| 5 | [05-twist-bivector-entity.md](./05-twist-bivector-entity.md) | N3-only `TwistBivector` operator + tests |
| 6 | [06-docs-changelog.md](./06-docs-changelog.md) | Docs + changelog + full validation |

## Testing as you go

- `uv run pytest py/tests/blade_mask/test_blade_mask.py -q`
- `uv run pytest py/tests/expression/ -q`
- `uv run pytest py/tests/geometry/ -q`
- `uv run ruff check py/pytanga/blade_mask py/pytanga/expression py/pytanga/geometry py/tests/blade_mask py/tests/expression py/tests/geometry`
- `uv run ty check`
- `uv run python py/examples/ga/expression/project_onto_euclidean_n3.py`
- `uv run python tools/generate-example-docs.py --check`
- `uv run mkdocs build --strict`

## Non-goals

- No symbolic (expression-valued) subspace target — `project_onto` takes a fixed
  `MV` / `BladeMask` only.
- No mask reindexing / grade projection beyond exact blade-id membership.
- No change to the separate geometric `MV.project(blade)` / `MV.reject(blade)`.
- No `TwistBivector` visualization or analysis — it is a mask/creation-only
  operator for now.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
