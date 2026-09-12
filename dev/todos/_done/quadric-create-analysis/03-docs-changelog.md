# Phase 3 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Update the architecture doc and the branch changelog, then run the full
regression and mark the plan done.

## Files

- Edit: `docs/dev/architecture/geometry-module-layering.md`
- Edit: `docs/changelog/2026-08-29_feat-quadric-space.md`

## Steps

- [x] **3.1 — Update the layering doc**
  - In `geometry-module-layering.md`, expand the `pytanga.quadric` row to list
    creation (`_create.py`), analysis (`_analysis.py`), and point recovery
    (`_pointset.py`) alongside the existing `from_coeffs`/`refine_*`.
  - Note that `geometry` keeps thin re-export shims for `create_q2`/`create_q3`,
    `analysis_q2`/`analysis_q3`, and `two_conic_intersection`.
- [x] **3.2 — Changelog**
  - Add a `## Refactor` bullet: "quadric MV creation + analysis consolidated in
    `pytanga.quadric`; `pytanga.geometry` keeps thin re-export shims."
- [x] **3.3 — Full regression**
  - `uv run pytest -q && uv run mkdocs build --strict`
- [x] **3.4 — Wrap up**
  - Update this README's `Status:` line to `Done`.
  - PR deferred (single PR with the prior quadric work).

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- PR / changelog hash rename deferred until all quadric work is ready (single PR).
