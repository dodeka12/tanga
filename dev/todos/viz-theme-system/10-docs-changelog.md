# Phase 10 — Docs, architecture description, changelog, full validation

## Goal

Document the theme system (registry, layers, stable-class contract, export
packing), add API docs, write the changelog, and run the full suite.

## Files

- Edit: `docs/dev/architecture/viz-controls-and-interactions.md` (or new
  `viz-theme-system.md` sibling)
- Edit: `docs/py/viz/visualizer/visualizer.md` (+ theme docs page)
- Edit: `docs/changelog/<branch>.md` (new, per `dev/workflows/changelog.md`)

## Steps

- [ ] **10.1 — Architecture doc**
  - Document: theme layers (base → tokens → components → overrides), the
    `registry.json` schema + resolved order, the **stable class-name contract**,
    the `theme_define` wire message, runtime switching, and export packing.
  - Note that the JS assigns semantic classes and only inline computed geometry.

- [ ] **10.2 — API docs**
  - Document `Visualizer.set_theme` / `theme` property, `list_themes` /
    `theme_css_files`, and the `theme=` export parameter; link the three new
    examples (control theming, theme switching, custom override).

- [ ] **10.3 — Changelog**
  - Create `docs/changelog/YYYY-MM-DD_<branch>.md` per `dev/workflows/changelog.md`
    (title via `uv run python tools/last-release.py`); add a New Features bullet
    for the theme system.

- [ ] **10.4 — Full validation**
  - `uv run pytest -q`, `uv run ruff check py/pytanga/viz/`, `node --check` on all
    touched JS, `uv run python tools/generate-example-docs.py --check`,
    `uv run mkdocs build --strict`.

## Validation

`uv run pytest -q && uv run ruff check py/pytanga/viz/ && uv run python tools/generate-example-docs.py --check && uv run mkdocs build --strict`
