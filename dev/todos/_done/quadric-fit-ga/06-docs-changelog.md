# Phase 6 — Docs + changelog

## Goal

Update the developer docs for the changed subsystems and write the branch changelog.

## Files

- Edit: `docs/dev/architecture/quadric-module.md` (module map + "numpy-only" note → expression-system dependency)
- Edit: `docs/dev/architecture/geometry-module-layering.md` (tolerance threaded through `Geometry`)
- Edit: `dev/theory/quadric-point-tuples.md` (coplanar-degeneracy warning)
- New: `dev/theory/quadric-cone-lift-derivation.md` (Q2→Q3 blade-map derivation)
- New: `docs/changelog/2026/09/22_feat-quadric-solve.md`

## Steps

- [x] **6.1 — architecture docs**
  - Update `quadric-module.md` (the `_build.py` row and the "numpy-only" intro, since
    `_build.py` now depends on `pytanga.expression`/`pytanga.blade_mask`) and
    `geometry-module-layering.md` (tolerance threaded through `Geometry`).
- [x] **6.2 — theory notes**
  - Extend `quadric-point-tuples.md` with the coplanar-point degeneracy warning; add
    `quadric-cone-lift-derivation.md` (mirror `quadric-plane-pair-derivation.md` style).
- [x] **6.3 — changelog**
  - Per `dev/workflows/changelog.md`: title from `uv run python tools/last-release.py`;
    `## New Features` bullets for the solver fix, GA-native fit, cone lift, and tolerant
    analysis.

## Validation

`uv run pytest -rs && uv run ruff check . && uv run ty check && uv run mkdocs build --strict`

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
