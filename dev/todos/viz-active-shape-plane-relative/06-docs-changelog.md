# Phase 6 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  No developer/architecture doc changes are
> expected (no new interaction model); update only the user-facing active-element
> docs.

## Goal

Document the new `normal` parameter and view-plane handle behaviour, and record
the change in a branch changelog per `dev/workflows/changelog.md`.

## Files

- Edit: `docs/py/viz/entities/active-elements/act-rectangle2d.md`
- Edit: `docs/py/viz/entities/active-elements/act-ellipse.md`
- Edit: `docs/py/viz/entities/active-elements/act-circle.md`
- Edit: `docs/py/viz/entities/active-elements/index.md`
- New: `docs/changelog/<YYYY>/<MM>/DD_<branch-name>.md` (per changelog workflow)

## Steps

- [x] **6.1 — Active-element docs.**
  - Add `normal` to the constructor tables of `act-rectangle2d.md`,
    `act-ellipse.md`, `act-circle.md` (type `Direction | None`, default `+z`),
    and note the rectangle/ellipse `angle` is measured within that plane.
  - In `index.md`, update the per-shape "Interaction" summaries and the
    "Standard drag triggers" row to say handles edit in the view plane.

- [x] **6.2 — Changelog.**
  - Run `uv run python tools/last-release.py`; create the branch changelog file
    named `DD_<branch-name>.md` under `docs/changelog/<year>/<month>/`, titled
    `# Changes since version <last-stable> (<last-rc>)`, with a `## Bug Fixes`
    bullet: **Active shapes (`ActRectangle2D`/`ActEllipse`/`ActCircle`) now honor
    an explicit `normal` plane and all composite handles edit in the view plane**,
    so shapes no longer silently flatten to world-XY on a tilted
    `CalibratedSurface`.

- [x] **6.3 — Build.**
  - `uv run mkdocs build --strict` to confirm docs link cleanly.

## Validation

`uv run mkdocs build --strict`

## Notes

- Changelog naming/renaming (branch name → squashed-hash) is finalised at PR time
  per `dev/workflows/pull-request.md`; this phase only creates the branch file.
- Follow `dev/workflows/example-docs.md` only if an example's docstring changes;
  the two labelling apps' docstrings already describe the calibrated workflow and
  need no `Keywords:` change.
