# Phase 9 — Example: custom theme with a full override

## Goal

Demonstrate the layered + override capability: a custom theme whose tokens
re-theme the palette and whose `overrides` fully re-style a control (e.g. a
switch-style checkbox or pill button), plus a themed export.

## Files

- New: `py/examples/viz/scenes/custom_theme_override.py`
- New: `py/pytanga/viz/templates/themes/<custom>/tokens.css` +
  `py/pytanga/viz/templates/themes/<custom>/overrides/*.css`
- Edit: `py/pytanga/viz/templates/themes/registry.json` (add the theme)
- (regenerate docs after adding the example)

## Steps

- [ ] **9.1 — Custom theme files**
  - Add a `custom` (or `pastel`) theme to `registry.json` with a token sheet and
    a full `button` and/or `checkbox` override; implement the override CSS
    targeting the stable classes (e.g. switch-style checkbox via `::before`).

- [ ] **9.2 — Example script**
  - Create `py/examples/viz/scenes/custom_theme_override.py` with the required
    header (one-line description, `Run with:`, `Keywords:` — see
    `dev/workflows/example-docs.md`).
  - Show `set_theme("custom")` applying the override, and call
    `export_snapshot(..., theme="custom")` (or equivalent) so the override is
    visible in a packed export.

- [ ] **9.3 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

## Validation

`uv run python tools/generate-example-docs.py --check && uv run ruff check py/examples/viz/scenes/custom_theme_override.py && uv run pytest py/tests/viz/test_themes.py -q`
