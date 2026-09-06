# Phase 5 — Docs, example & changelog

## Goal

Document the four new capabilities, extend the `table_editing.py` example to
exercise them (format string, editable titles, a custom type-change handler that
shows a warning banner), and record the feature in the branch changelog.

## Files

- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `docs/py/viz/interaction/control-views.md`
- Edit: `py/examples/viz/ui/controls/table_editing.py`
- Edit: `docs/changelog/2026-09-05_fix-examples.md` (branch changelog)

## Steps

- [x] **5.1 — API docs**
  - `controls.md`: document `TableView(editable_titles=…)`,
    `on_column_title_change` / `on_column_type_change`, `set_column_format`,
    `convert_column`, the `format` field of the number column type, and the
    payloads `TableColumnTitleChange` / `TableColumnTypeChange`.
  - `control-views.md`: add the new `TableView` parameters to the signature
    block and the "also exposes" list.

- [x] **5.2 — Example**
  - Give the example a `number` column with a `format` (e.g. `"{:.2f}"` or
    `"{:.1f} m"`) set via `set_column_format`, confirm editable titles, and
    register an `on_column_type_change` handler that calls
    `table.convert_column(...)` (the base) and shows a warning banner via the
    existing banner mechanism when it returns `False`.
  - Regenerate example docs: `uv run python tools/generate-example-docs.py`.

- [x] **5.3 — Changelog**
  - Append a `## New Features` bullet to the branch changelog per
    `dev/workflows/changelog.md` (do not predict a version).

## Validation

```
uv run pytest py/tests/viz/ -q
node --test 'dev/src/js-tests/*.test.mjs'
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- This phase is the final one; the `README.md` `Status:` moves to `Done` once
  it and the full validation gate pass.
