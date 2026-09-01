# Phase 3 — Example: control theming

## Goal

Add a runnable example showing controls (group + individual views) rendered from
the extracted CSS, with borderless icon buttons and token-driven colors.

## Files

- New: `py/examples/viz/scenes/control_theming.py`
- (regenerate docs after adding the example)

## Steps

- [ ] **3.1 — Example script**
  - Create `py/examples/viz/scenes/control_theming.py` with the required header
    (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Build a `Visualizer` with a `ControlGroup`/`GroupView` and individual
    `ButtonView`/`CheckboxView`/`SliderView` (incl. an `icon_only` button) to
    exercise the themed, borderless-icon look.
  - Note in the docstring that styling now comes from the theme CSS files.

- [ ] **3.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/scenes/control_theming.py`
