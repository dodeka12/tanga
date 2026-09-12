# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Update the layering doc, add the changelog entry, and run the full regression.

## Files

- Edit: `docs/dev/architecture/geometry-module-layering.md`
- New: `docs/changelog/2026/09/<DD>_<branch>.md` (per `changelog.md`)
- Edit: `docs/changelog/index.md` (only if finalizing; else defer per workflow)

## Steps

- [x] **5.1 — Layering doc**
  - In `geometry-module-layering.md`, note that `quadric/_create.py` now owns the
    Q2 **and** Q3 rotation rotor and `quadric/_analysis.py` owns the rotor
    analysis (returning `geometry.operators.Rotor`, imported lazily); the
    `geometry` shims / `analyze_operator` dispatcher route to `quadric`.
- [x] **5.2 — Changelog**
  - `uv run python tools/last-release.py` for the title; add a `## New Features`
    bullet for the Q3 rotor + rotor analysis + `quadric3d_demo`.
- [x] **5.3 — Full regression**
  - `uv run pytest -q` and `uv run mkdocs build --strict`.
  - `uv run python tools/generate-example-docs.py --check`.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- Changelog hash-rename + `index.md` entry happen at PR time (`pull-request.md`);
  deferred here to keep the combined quadric PR intact.
