# Phase 2 — `Expression` / `AffineExpression.project_onto`

## Goal

Restrict an expression's output axis to a blade subspace, mirroring
`MV.project_onto`.

## Files

- Edit: `py/pytanga/expression/_expression.py`
- Edit: `py/tests/expression/test_expression.py`
- Edit: `py/tests/expression/test_affine.py`

## Steps

- [x] **2.1 — `_restrict_output` helper**
  - Add next to `_reindex_output`: select the rows of `expr.tensor.data` whose
    blade id is in `keep`, producing a new output mask
    `BladeMask(expr.algebra, keep_ids)`; return
    `Expression(expr.algebra.multivector({}))` when nothing is kept.

- [x] **2.2 — `Expression.project_onto`**
  - Add in the "Involutions" section: accept `MV | BladeMask`, resolve to a
    `BladeMask`, guard type + algebra, delegate to `_restrict_output`.

- [x] **2.3 — `AffineExpression.project_onto`**
  - Map over terms, drop terms whose result has an empty output mask, and return
    `AffineExpression([zero_constant])` if every term is annihilated.

- [x] **2.4 — Tests**
  - Expression: `BladeMask` path, `MV` path, disjoint→zero, wrong type, wrong
    algebra, and multi-variable structure preserved.
  - Affine: distribution, annihilated-term dropping, and the all-annihilated
    single-zero-term case.

## Validation

`uv run pytest py/tests/expression/ -q`

## Notes

- `_restrict_output` computes the kept ids by explicit membership (`bid in keep`),
  deliberately avoiding `BladeMask.intersection` (whose empty case is the Phase 1
  bug).

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
