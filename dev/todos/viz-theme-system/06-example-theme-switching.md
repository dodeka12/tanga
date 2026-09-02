# Phase 6 — Example: runtime theme switching

## Goal

Demonstrate backend theme selection changing live: a control triggers
`set_theme("light")` and the viewer restyles without reload.

## Files

- New: `py/examples/viz/scenes/theme_switching.py`
- (regenerate docs after adding the example)

## Steps

- [x] **6.1 — Example script**
  - Create `py/examples/viz/scenes/theme_switching.py` with the required header
    (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Add two `ButtonView`s whose `on_click` call `viz.set_theme("dark")` /
    `viz.set_theme("light")` (and a slider/checkbox so the change is visible
    across controls), plus some scene content.

- [x] **6.2 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/scenes/theme_switching.py`
