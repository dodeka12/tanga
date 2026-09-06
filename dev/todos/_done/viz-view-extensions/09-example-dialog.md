# Phase 9 — Example: dialog

## Goal

Demonstrate the dialog: a title + a container of view-based controls, closed
either by the built-in ✕ or by a user control inside the dialog.

## Files

- New: `py/examples/viz/dialogs/dialog_demo.py`
- (regenerate docs after adding the example)

## Steps

- [x] **9.1 — Example script**
  - Create `py/examples/viz/dialogs/dialog_demo.py` with the required header
    (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Build a `Visualizer` + `set_layout` (or `SceneView` overlay) that opens a
    `show_dialog(...)` whose `content` is a `StackView` of control views
    (e.g. a `SliderView` + a `ButtonView` labelled "Close").
  - Wire the "Close" button's `on_click` to `remove_dialog(id)`; also exercise
    the `on_close` callback and the ✕ close path.

- [x] **9.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/dialogs/dialog_demo.py`
