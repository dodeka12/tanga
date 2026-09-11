# Phase 5 — Docs + changelog

## Goal

Document the `stretch` modes and record the change in the branch changelog.

## Files

- Edit: `docs/changelog/2026-09-05_fix-examples.md` (append)
- Regenerated: `docs/` example gallery pages

## Steps

- [x] **5.1 — Changelog**
  - Append to `docs/changelog/2026-09-05_fix-examples.md` a `## New Features`
    bullet (2D camera `stretch` modes) and a `## Breaking Changes` bullet
    (`uniform` removed in favour of `stretch`). Wrap at ~80 columns.

- [x] **5.2 — Example docs**
  - Run `uv run python tools/generate-example-docs.py` (regenerate) and
    `--check`.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`

## Notes

- Use the existing `# Changes since version 1.17.0 (2.0.0-rc1)` title already in
  the branch changelog; do not create a new file.
