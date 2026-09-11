# Phase 8 — Docs + changelog

## Goal

Update the docs that describe the table as "backed by Tabulator" and document the
new flags, active cell, deletion, and sorting. Add a branch changelog.

## Files

- Edit: docs mentioning Tabulator / the table control (`docs/py/...`, example docs)
- New: `docs/changelog/2026-09-05_fix-examples.md`
- Edit: `docs/changelog/index.md`

## Steps

- [x] **8.1 — Docs sweep**
  - `grep -rni 'tabulator' docs/` and rewrite the table docs to describe the native
    grid (no CDN), and document `show_column_titles` / `show_row_numbers` /
    `allow_delete_columns`, the active cell + cursor-key movement, row/column
    deletion, and header-click sorting on `TableView`.

- [x] **8.2 — Example docs**
  - Update `table_editing.md`, `table_data.md`, `table_split.md` (follow
    `dev/workflows/example-docs.md` if generated) to mention sorting, the active
    cell, and the title/row-number flags.

- [x] **8.3 — Changelog**
  - Create `docs/changelog/2026-09-05_fix-examples.md` using the title from
    `uv run python tools/last-release.py`, with `## New Features` (native table,
    titles/row numbers, active cell, column delete, sorting) and `## Bug Fixes`
    (last column/row edit).
  - Add a matching entry at the top of `docs/changelog/index.md`.

## Validation

`uv run mkdocs build --strict`

## Notes

- Follow `dev/workflows/changelog.md` for the title + index format.
