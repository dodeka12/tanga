# Phase 6 — Example, docs, changelog

## Goal

Demonstrate undo/redo in the table example, document the new API and keyboard
shortcuts, and add the branch changelog.

## Files

- Edit: `py/examples/viz/interaction/table_editing.py`
- (Generated) `docs/py/examples/viz/interaction/table_editing.md` via the
  example-docs generator
- Edit: `docs/py/viz/interaction/controls.md`
- Edit: `docs/py/viz/interaction/control-views.md`
- New: `docs/changelog/2026-09-01_fix-tabular.md` (name per
  `dev/workflows/changelog.md`)

## Steps

- [x] **6.1 — Example (`table_editing.py`)**
  - Add `max_history=100` (or a smaller value to make it visible) to the
    `add_table` call.
  - Update the annotation to mention Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y.
  - Add two backend-driven buttons ("Undo" / "Redo") via `add_button` whose
    `on_click` calls `self.viz.undo_table("data")` / `self.viz.redo_table("data")`
    (demonstrates the programmatic trigger; buttons live in the panel, not the
    grid). Update the module docstring `Keywords:` line to include `undo, redo`.

- [x] **6.2 — Regenerate example docs**
  - `uv run python tools/generate-example-docs.py` then `--check` (see
    `dev/workflows/example-docs.md`).

- [x] **6.3 — `controls.md` (`add_table`)**
  - Add a `max_history` row to the `add_table` parameter table and a short
    "Undo / redo" paragraph: keyboard shortcuts + `undo_table` / `redo_table` /
    `clear_table_history` methods.
  - (While here) confirm `allow_delete_rows` / `on_row_delete` are listed;
    add them if missing for accuracy.

- [x] **6.4 — `control-views.md` (`TableView`)**
  - Add `max_history=100` to the `TableView` signature block and note the
    `undo()` / `redo()` / `can_undo` / `can_redo` conveniences.

- [x] **6.5 — Changelog**
  - Create the branch changelog per `dev/workflows/changelog.md` (title
    `# Changes since version <last-stable-release>`, determined by
    `uv run python tools/last-release.py`). Add a **New Features** bullet for
    table undo/redo (keyboard + backend API + `max_history`).

- [x] **6.6 — Full validation**
  - `uv run pytest py/tests/viz/ -q`
  - `node --test dev/src/js-tests/*.test.mjs`
  - `uv run mkdocs build --strict`

## Validation

`uv run pytest py/tests/viz/ -q && node --test dev/src/js-tests/*.test.mjs && uv run mkdocs build --strict`

## Notes

- The example-docs generator must run after editing `table_editing.py`; the
  generated `docs/py/examples/viz/interaction/table_editing.md` is committed.
- Do **not** predict the release version in the changelog title (see
  `dev/workflows/changelog.md`).
