# Phase 5 — Docs + changelog + example + full regression

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md` and `viz-architecture.md`) for the subsystem(s)
> this work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Document the feature (changelog + example), regenerate example docs, and run the
full regression.

## Files

- Edit: `docs/changelog/2026-08-29_feat-quadric-space.md`
- New: `py/examples/ga/quadric/quadric_intersection_demo.py`
- Edit: `docs/dev/architecture/geometry-module-layering.md` (if the new module
  changes the documented layering — otherwise just confirm it still holds)

## Steps

- [x] **5.1 — Changelog** (per `dev/workflows/changelog.md`)
  - Append a `## New Features` bullet to the branch changelog:
    "**Two-quadric intersection** — `intersect_quadrics(Q1, Q2)` and the deferred
    IPNS grade-2 `analyze()` path recover the intersection curve via the pencil's
    degenerate members: a `PlaneConicPair` (plane-pair member) or a sampled
    `Curve` (cone member); the smooth-elliptic case raises for now."
- [x] **5.2 — Example** (per `dev/workflows/example-docs.md`)
  - `quadric_intersection_demo.py`: build two quadrics (e.g. a sphere and an
    offset ellipsoid, plus the cube `x²−y²` / `y²−z²` plane-pair case),
    `viz.new(intersect_quadrics(Q1, Q2))` for each, and print the refined result.
    Header docstring with description, `Run with:`, and `Keywords:`.
- [x] **5.3 — Regenerate docs + full regression**
  - `uv run python tools/generate-example-docs.py` and `--check`.
  - `uv run pytest -q` and `uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The changelog is the branch file (append, don't create a new one); the PR-time
  hash rename is deferred to the combined quadric PR (see
  `dev/workflows/pull-request.md`).
- Update `geometry-module-layering.md` only if the new `_intersection.py` module
  warrants a mention; the DAG itself (quadric below entities, lazy entity import)
  must remain unchanged.
