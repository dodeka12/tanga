# Phase 4 — Docs + changelog + regression

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Document the new `update*` convention and backend-driven extent, update the
changelog, and run the full regression.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md` (note the per-kind `update*`
  convention under "New entity kind", if not already implied)
- Edit: `docs/changelog/2026-08-29_feat-quadric-space.md` (or the current branch
  changelog per `dev/workflows/changelog.md`)
- Edit: any renderer/style docstrings touched by earlier phases

## Steps

- [x] **4.1 — Developer docs.**
  - In `viz-architecture.md` "New entity kind" recipe, add step 5: "Export an
    `update<Kind>(mesh, ent, prev)` (return `false` to rebuild) for kinds whose
    geometry derives from content fields."
- [x] **4.2 — Changelog.**
  - Add a bullet under `## Bug Fixes` for the conic-curve update + branch +
    line-pair-centering fixes, and (if applicable) a `## Refactor` bullet for
    the OO rebuild split.
- [x] **4.3 — Full regression.**
  - Run the full Python + JS + docs validation below.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- PR/changelog hash rename deferred until after `entity-layering` (single PR).
