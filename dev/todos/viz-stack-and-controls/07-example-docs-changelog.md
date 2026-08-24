# Phase 7 — Example, docs, changelog, full validation

## Goal

Demonstrate the new composition model end-to-end and document it.

## Steps

- [x] **7.1 — `py/examples/viz/demo_split_view.py`**
  - Rewrite to compose views directly (no `viz.add_slider` for the sidebar):
    - `GroupView("Actions", [ButtonView("btn_reset", "Reset view"), ButtonView("btn_fit", "Fit camera")])`
      as the left `SplitView` pane;
    - a `StackView`/`GroupView` overlay child on `SceneView("")` to show overlay
      anchoring;
    - keep the vertical 70/30 + two detail scenes.
  - Ensure the buttons are visible and clickable (events route to handlers).

- [x] **7.2 — Docs**
  - `docs/py/viz/visualizer/split-views.md`: add `StackView`/`GroupView`/control
    views + `SceneView` overlay; update the example and the class table.
  - `mkdocs.yml` nav unchanged unless a new page is added.

- [x] **7.3 — Changelog**
  - `docs/changelog/2026-08-24_feat-multi-view.md`: add a New Features bullet for
    `StackView` + control views + `GroupView` + scene overlay (and the fixed
    splitter line).

- [x] **7.4 — Full validation**
  - `uv run pytest py/tests/viz/ -q` (all green, including new tests).
  - `node --test 'dev/src/js-tests/*.test.mjs'` + JS syntax check.
  - `uv run ruff check` on touched Python files.
  - `uv run mkdocs build --strict`.
  - `uv run python py/examples/viz/demo_split_view.py` (manual) — buttons visible,
    splitters correct, fixed splitter shows a thin line.

## Validation

`uv run pytest py/tests/viz/ -q` + `node --test 'dev/src/js-tests/*.test.mjs'` +
`uv run mkdocs build --strict` + manual example run.
