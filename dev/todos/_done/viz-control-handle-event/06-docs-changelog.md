# Phase 6 — Docs + changelog

## Goal

Document the `Control.handle_event` seam and the `Table.on_change` handler, and
record the change in the branch changelog.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`
- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `docs/py/viz/interaction/control-views.md`
- Edit: `docs/changelog/2026-09-03_feat-view-architecture.md` (append)
- (optional) Edit: `py/examples/viz/ui/controls/table_editing.py`

## Steps

- [x] **6.1 — Architecture doc**
  - Update "Adding a new control kind" / "Fixed contract" to mention
    `Control.handle_event` as the dispatch seam (control kinds own their event
    handling; `Visualizer` resolves → delegates → pushes → fires).

- [x] **6.2 — `controls.md`**
  - Document `Table.on_change` (payload = full `{columns, rows}`, fires on
    undo/redo) alongside `on_cell_change`/`on_row_add`/etc.

- [x] **6.3 — `control-views.md`**
  - Document `TableView(on_change=...)` and `add_table(on_change=...)`.

- [x] **6.4 — Example (optional)**
  - Extend `table_editing.py` to register `on_change` and annotate the undo/redo
    result; regenerate example docs with `uv run python tools/generate-example-docs.py`.

- [x] **6.5 — Changelog**
  - Append a `## Refactor` bullet for the `handle_event` extraction and a
    `## New Features` bullet for `Table.on_change` to the existing branch
    changelog, per `dev/workflows/changelog.md` (title already
    `# Changes since version 1.17.0`; re-check with `uv run python tools/last-release.py`).

## Validation

`uv run mkdocs build --strict && uv run pytest py/tests/viz -q`

## Notes

- Final phase per `dev/workflows/create-plan.md`: docs + changelog last.
- No `docs/changelog/index.md` update at plan time — that happens at PR time
  (`dev/workflows/pull-request.md`).
