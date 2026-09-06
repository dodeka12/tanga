# Phase 5 — Document themeable values

## Goal

Document every value a theme can set: the **design tokens** (CSS custom
properties defined in `base.css`) and the **stable override class contract**
(the semantic class names an `overrides/*.css` may target).

## Files

- Edit: `docs/py/viz/visualizer/theming.md` (new "Theme reference" section)
- Edit: `docs/dev/architecture/viz-theme-system.md` (link/consolidate)

## Steps

- [x] **5.1 — Token reference**
  - Add a "Theme tokens" section to `theming.md` listing all 27 tokens with a
    one-line description and their `base.css` default, grouped:
    - Palette: `--tanga-bg`, `--tanga-fg`, `--tanga-fg-muted`,
      `--tanga-fg-strong`, `--tanga-accent`, `--tanga-accent-soft`,
      `--tanga-danger`.
    - Surfaces: `--tanga-panel-bg`, `--tanga-panel-hover`, `--tanga-surface`,
      `--tanga-surface-strong`, `--tanga-input-bg`.
    - Borders: `--tanga-border`, `--tanga-border-strong`,
      `--tanga-border-subtle`.
    - Scrollbar: `--tanga-scrollbar-thumb`, `--tanga-scrollbar-thumb-hover`,
      `--tanga-scrollbar-track`.
    - Elevation: `--tanga-shadow`.
    - Typography: `--tanga-font`.
    - Status/loading: `--tanga-status-ok`, `--tanga-status-err`,
      `--tanga-loading-bg`, `--tanga-spinner`.
    - Warning banner: `--tanga-warning-bg`, `--tanga-warning-fg`,
      `--tanga-warning-button-bg`, `--tanga-warning-button-fg`.
  - Note that `base.css` is the single source of truth; the table must mirror it.

- [x] **5.2 — Override class contract**
  - Add an "Override targets" section listing the stable classes with a one-line
    description each: `.tanga-action-button`, `.tanga-checkbox-input`,
    `.tanga-range-input`, `.tanga-select-input`, `.tanga-text-input`,
    `.tanga-group` / `.tanga-group-header` / `.tanga-group-title` /
    `.tanga-group-toggle`, `.tanga-menu-trigger`, `.tanga-banner`,
    `.tanga-dialog`, `.tanga-title-overlay`, `.tanga-warning-banner`, etc.
  - Link the deeper explanation in `viz-theme-system.md`.

- [x] **5.3 — Custom-theme walkthrough**
  - Update the "Custom themes" section of `theming.md` to describe the new
    `register_theme` + `copy_theme` flow (replacing the "drop files into
    templates/themes and edit registry.json" instructions).

## Validation

`uv run mkdocs build --strict`
