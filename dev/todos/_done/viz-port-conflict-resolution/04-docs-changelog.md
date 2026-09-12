# Phase 4 — Changelog

## Goal

Record the new feature in the branch changelog.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `docs/changelog/2026-09-10_feat-jupyter-visualizer.md`

## Steps

- [x] **4.1 — Append a New Features bullet**
  - Under `## New Features` add a bullet: `PortConflictMode` port-conflict
    resolution — `VizServer` now resolves a busy port by `CANCEL`/`AUTO`/
    `KILL`/`ASK` (via `psutil`), and `Visualizer(port_conflict_mode=...)`
    defaults to `AUTO` under Jupyter and `ASK` at the terminal.
- [x] **4.2 — Verify the changelog renders**
  - Ensure the bullet follows the `- **Headline** —` style and wraps at ~80
    columns.

## Validation

`uv run mkdocs build --strict`

## Notes

- Keep the file's existing `# Changes since version 2.1.0` title and sections;
  only append to `## New Features` (see `dev/workflows/changelog.md`).
- The `index.md` entry is added at PR time, not now.
