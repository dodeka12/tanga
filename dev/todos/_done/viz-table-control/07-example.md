# Phase 7 — Example

## Goal

A runnable example demonstrating `add_table` with all three handlers, following
the example-docs conventions, and regenerated docs pages.

## Files

- New: `py/examples/viz/interaction/table_data.py`
- (Generated) docs nav/pages via the example-docs generator

## Steps

- [x] **7.1 — `table_data.py`**
  - License header + module docstring in the
    `<name>.py — …` / `Run with:` / `Keywords:` form (see
    `dev/workflows/example-docs.md`).
  - A `VisualizerApp` subclass that:
    - `add_table("data", columns=["x","y","z"], rows=[["1","2","3"],["4","5","6"]], …)`.
    - `on_cell_change` echoes the edited cell to an annotation;
    - `on_row_add` / `on_column_add` log the added row/column.
  - `Keywords:` e.g. `controls, table, tabular data, add_table, VisualizerApp`.

- [x] **7.2 — Regenerate docs**
  - `uv run python tools/generate-example-docs.py`
  - `uv run python tools/generate-example-docs.py --check`

## Validation

`uv run python tools/generate-example-docs.py --check`

## Notes

- Follow `py/examples/viz/interaction/all_controls.py` for structure/lifecycle.
