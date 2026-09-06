# Phase 6 — Example docs + changelog

## Goal

Regenerate the example gallery docs and add a branch changelog entry.

## Files

- Edit: `docs/changelog/2026-09-05_fix-examples.md` (append)
- Regenerated: `docs/` example gallery pages (via `tools/generate-example-docs.py`)

## Steps

- [x] **6.1 — Changelog**
  - Follow `dev/workflows/changelog.md`: run
    `uv run python tools/last-release.py` to get the title's
    since-relative label.
  - Append to the existing branch changelog
    `docs/changelog/2026-09-05_fix-examples.md` (already on this branch): a
    `## New Features` bullet (per-scene `space_dim`, `set_space_dim`,
    `switch_2d_3d` example) and `## Bug Fixes` bullets (`multi_plot.py` panes,
    `fit_view2d` border, 2D→3D perspective switch). Wrap body text at ~80
    columns.

- [x] **6.2 — Example docs**
  - Run `uv run python tools/generate-example-docs.py` to regenerate gallery
    pages/nav for the new/edited examples.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Do **not** predict the release version — use the `tools/last-release.py`
  output verbatim in the title.
- The changelog `index.md` update happens at PR time per
  `dev/workflows/pull-request.md` (not in this phase).
