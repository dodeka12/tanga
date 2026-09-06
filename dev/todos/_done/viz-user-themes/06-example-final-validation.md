# Phase 6 — Example + final validation

## Goal

Ship an end-to-end example that registers an external theme folder, switches to
it, live-refreshes it, and packs it into an export — then run the full
validation suite.

## Files

- New: `py/examples/viz/scenes/user_theme.py` (or similar)
- New: `py/examples/viz/scenes/example_theme/tokens.css` +
  `py/examples/viz/scenes/example_theme/overrides/*.css` (theme source)
- (regenerate docs after adding the example)

## Steps

- [ ] **6.1 — Example theme folder**
  - Add a small example theme folder (a `tokens.css` + one override) under
    `py/examples/` that the example script loads via `register_theme`.

- [ ] **6.2 — Example script**
  - Create the example with the required header (one-line description,
    `Run with:`, `Keywords:` — see `dev/workflows/example-docs.md`).
  - Demonstrate: `register_theme(...)` → `set_theme(...)` →
    `viz.show(...)` → `viz.refresh_theme()` → `export_snapshot(..., theme=...)`.
  - Prefer `copy_theme("pastel", ...)` if the example wants to scaffold at
    runtime.

- [ ] **6.3 — Docs generation**
  - Run `uv run python tools/generate-example-docs.py` and confirm the example
    appears under the examples nav.

- [ ] **6.4 — Full validation**
  - `uv run python tools/generate-example-docs.py --check`
  - `uv run ruff check py/pytanga/viz/_themes.py py/pytanga/viz/server.py py/pytanga/viz/visualizer.py py/examples/viz/scenes/user_theme.py`
  - `uv run pytest py/tests/viz/ -q`
  - `node --check py/pytanga/viz/templates/themes.js`
  - `uv run mkdocs build --strict`

## Validation

All commands in 6.4 pass.
