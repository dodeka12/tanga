# Phase 8 — Docs + changelog

## Goal

Document the `add_table` / `TableView` API in the controls reference and record
the feature in the branch changelog.

## Files

- Edit: `docs/py/viz/visualizerapp/controls.md`
- New: `docs/changelog/YYYY-MM-DD_<branch-name>.md` (per
  `dev/workflows/changelog.md`)

## Steps

- [x] **8.1 — Controls reference (`controls.md`)**
  - Add an `## add_table` section (code sample + parameter table) documenting
    `cid`, `label`, `columns`, `rows`, `allow_add_rows`, `allow_add_columns`,
    `tooltip`, `on_cell_change`, `on_row_add`, `on_column_add`, and the handler
    payloads (`TableCellChange` / `TableRowAdd` / `TableColumnAdd`).

- [x] **8.2 — Changelog**
  - Create `docs/changelog/<YYYY-MM-DD>_<branch-name>.md` (branch name with `/`
    → `-`; e.g. `2026-08-30_feat-table-control.md` on `feat/table-control`),
    title `# Changes since version <last-stable-release>` where
    `<last-stable-release>` comes from `uv run python tools/last-release.py`.
  - Add a `## New Features` bullet for the table control.

- [x] **8.3 — Validate**
  - `uv run mkdocs build --strict`.

## Validation

`uv run mkdocs build --strict`

## Notes

- Do not add the `docs/changelog/index.md` entry yet — that happens at PR time
  (after the hash rename), per `dev/workflows/pull-request.md`.
