# Phase 4 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`).  Final
> phase; if the work changed a documented contract, update the developer docs here.

## Goal

Record the behaviour fix in the developer docs and the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md`
- New: `docs/changelog/2026/10/DD_fix-view-plane-drag-scale.md`

## Steps

- [x] **4.1 — Note the `screenWorldScale` depth semantics.**
  - In `docs/dev/architecture/viz-architecture.md`, on the `CoordinateMapper`
    bullet that references `screenWorldScale`, add that the perspective branch
    uses the point's depth along the view axis (not Euclidean distance).

- [x] **4.2 — Branch changelog.**
  - Follow `dev/workflows/changelog.md`: create
    `docs/changelog/2026/10/DD_fix-view-plane-drag-scale.md` with title
    `# Changes since version 2.19.0` (per `uv run python tools/last-release.py`)
    and a `## Bug Fixes` bullet:
    `- **VIEW_PLANE drags no longer overshoot under perspective cameras** — …`.
  - Do **not** touch `docs/changelog/index.md` yet (that happens at PR time).

## Validation

`uv run mkdocs build --strict`

## Notes

- Changelog rename to the squashed-commit hash and the `index.md` entry happen
  at PR time per `dev/workflows/pull-request.md`.
