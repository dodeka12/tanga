# Phase 9 — Docs, changelog, and full validation

## Goal

Document the hard-coded type-mask mechanism, update the developer architecture
note, extend the branch changelog, and run the full gate.

## Files

- Edit: `docs/dev/architecture/geometry-module-layering.md` (replace the
  `basis_for` note with the `mask_for_<type>` hard-coded contract)
- Edit: `docs/py/ga/blade-mask/usage.md` (note hard-coded type masks)
- New: `docs/changelog/2026/09/18_feat-expression-matrix.md` (append bullet)
- Edit: `docs/changelog/index.md` (PR time only)

## Steps

- [x] **9.1 — developer docs**
  - Update `geometry-module-layering.md`: `mask_for` dispatches to per-algebra
    `mask_for_<type>(basis)` functions with hard-coded ids; no instance template.

- [x] **9.2 — changelog**
  - Append a New Features/Bug Fix bullet: `mask_for` now returns hard-coded full
    type masks (fixes partial-mask derivation).

- [x] **9.3 — full validation**
  - `uv run pytest -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Validation

`uv run pytest -q && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

## Notes

- This is a breaking change to `mask_for(alg, Type)` (masks may gain blades that
  the old template accidentally dropped); callers relying on the old partial
  masks will now get the full type mask.

---

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
