# Phase 2 — Basis-aware `union` / `intersection`

## Goal

Make `BladeMask.union` and `BladeMask.intersection` operate on the named basis
when both operands carry one, with a `discard_basis` flag on `intersection` for
the strict/fallback behavior.

## Files

- Edit: `py/pytanga/blade_mask/_mask.py`
- Edit: `py/tests/blade_mask/test_blade_mask.py`

## Steps

- [x] **2.1 — `union` basis-aware**
  - If both `_basis is not None`: return a mask over the raw-id union whose
    `_basis` is the deduplicated concatenation of both direction sets (by
    `name`+`MV`).  Example: `{e1∧e∞, e2∧e∞, e3∧e∞}` ∪ `{e1∧e₀, e2∧e₀, e3∧e₀}`
    carries all six directions over the same 6 raw blades.
  - Otherwise: raw-id union via the normal constructor (auto display basis may
    re-attach).

- [x] **2.2 — `intersection(other, *, discard_basis=False)`**
  - If both `_basis is not None`: compute the shared directions (present in both,
    by `name`+`MV`); return a mask over the union of those directions' supports
    carrying the shared `Basis` (empty mask if none shared, e.g. `einf ∩ eo`).
  - Else if `discard_basis=True`: return the raw-id intersection via the normal
    constructor (metadata dropped / default auto-names).  `e4 ∩ einf` → raw `{8}`.
  - Else (strict): raise `ValueError` telling the caller to pass
    `discard_basis=True`.

- [x] **2.3 — tests**
  - Union merges two same-support different-name masks into a 6-direction mask.
  - `e4 ∩ einf` raises; with `discard_basis=True` returns raw `{8}`.
  - `einf ∩ einf` returns `{8, 16}` with name `einf`.
  - `einf ∩ eo` (default) returns an empty mask.
  - Cross-algebra union/intersection still assert (unchanged).

## Validation

`uv run pytest py/tests/blade_mask/ -q`

## Notes

- `__eq__` stays raw-id based; a basis-bearing mask equals its raw twin (metadata
  is not identity), so tensor-axis alignment is unaffected.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
