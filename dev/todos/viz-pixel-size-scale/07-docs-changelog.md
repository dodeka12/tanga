# Phase 7 — Docs + changelog

## Goal

Finalize the developer docs (architecture) and add the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-architecture.md` (if not done in Phase 1)
- New: `docs/changelog/2026/09/<DD>_<branch-name>.md` (per
  `dev/workflows/changelog.md`)
- Edit: `docs/changelog/index.md` (only at PR time — note, don't do now)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **7.1 — Confirm `viz-architecture.md` documents `world_units_per_pixel()`**
  - The `CoordinateMapper` bullet now mentions the method and the
    camera-pixel vs screen-pixel distinction.
- [x] **7.2 — Write the branch changelog**
  - `docs/changelog/2026/09/30_feat-calibrated-pane-interaction.md` with
    `Bug Fixes`, `New Features`, and `Refactor` bullets (title from
    `tools/last-release.py` → `2.12.1`).
- [x] **7.3 — Full validation**
  - `uv run pytest -q` (3706 passed) and `uv run mkdocs build --strict` (ok).

## Validation

`uv run pytest -q && uv run mkdocs build --strict`

## Notes

- The `docs/changelog/index.md` entry is added at PR time (after the hash
  rename), not now.
