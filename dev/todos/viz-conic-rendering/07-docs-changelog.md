# Phase 7 — Docs + changelog + full regression

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Update documentation and the branch changelog, and run the full regression.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md` (only if a contract changed)
- Edit: `docs/py/examples/ga/quadric/conic_demo.md` (and the example if it changes)
- Edit: `docs/changelog/<hash>.md` per `dev/workflows/changelog.md`
- Edit: any entity/style docstrings touched by earlier phases

## Steps

- [x] **7.1 — Update developer docs.**
  - If `_resolve_scene_entity`'s refine behavior or the style dispatch is a new
    documented contract, note it in `docs/dev/architecture/viz-architecture.md`.
- [x] **7.2 — Update example docs.**
  - Refresh `conic_demo` docs to reflect that `viz.add(raw_conic)` now works
    (auto-refine) and that conics render as 2D lines. Follow
    `dev/workflows/example-docs.md` if the example source changes.
- [x] **7.3 — Changelog.**
  - Write the branch changelog per `dev/workflows/changelog.md`; finalize the
    hash rename + PR per `dev/workflows/pull-request.md`.
- [x] **7.4 — Full regression.**
  - Run the full Python + JS + docs validation below.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- This is the final phase; mark the plan `Done` only after the changelog hash
  rename and PR open.
