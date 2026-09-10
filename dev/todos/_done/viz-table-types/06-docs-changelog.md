# Phase 6 — Docs, changelog & example

## Goal

Document the new table model/persistence, demonstrate it in an example, and
record the change in the changelog.

## Files

- Edit: `docs/py/viz/interaction/control-views.md`
- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `py/examples/viz/ui/controls/table_data.py` (and/or a new example)
- Edit: `docs/changelog/2026-09-05_fix-examples.md` (append)

## Steps

- [x] **6.1 — docs**
  - `control-views.md`: extend the `TableView` signature (`column_types`,
    `json_path`, `save`/`load`/`to_csv`/`from_csv`), and describe column types,
    deduction, alignment, and the JSON/CSV formats.
  - `controls.md`: add a short note that cell values are strings on the wire and
    numbers/bools are right/center-aligned via column types.

- [x] **6.2 — example**
  - Update `table_data.py` to use a numeric column, a bool column, and an enum
    column so the new editors/alignment are visible; (optionally) add a small
    auto-save/JSON round-trip to the app. Follow `dev/workflows/example-docs.md`
    (description + `Keywords:` header).

- [x] **6.3 — changelog**
  - Append a `## New Features` bullet to the current branch changelog
    (`docs/changelog/2026-09-05_fix-examples.md`) per
    `dev/workflows/changelog.md` (do not rename to a hash yet — that is PR time).

- [x] **6.4 — build + example-docs gate**
  - Regenerate example docs and build docs.

## Validation

`uv run python tools/generate-example-docs.py --check` and
`uv run mkdocs build --strict`

## Notes

- No `index.md` update until PR time (changelog workflow).
