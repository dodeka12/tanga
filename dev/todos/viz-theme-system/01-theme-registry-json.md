# Phase 1 — Theme registry JSON + Python loader

## Goal

Define the `registry.json` schema and a Python loader/validator that resolves a
theme id to an ordered CSS file list, exposing `list_themes()` and
`theme_css_files(theme_id)`. This is the single source of truth used later by
both the live server and the export bundler.

## Files

- New: `py/pytanga/viz/templates/themes/registry.json`
- New: `py/pytanga/viz/_themes.py`
- Edit: `py/pytanga/viz/__init__.py` (export `list_themes`, `theme_css_files`)
- New: `py/tests/viz/test_themes.py`

## Steps

- [ ] **1.1 — `registry.json`**
  - Create the manifest per the README contract: `base`, `tokens`, `components`
    (the control/view `.css` files), and `themes` with `dark` (no overrides) and
    `light` (token sheet + `button`/`checkbox` overrides).
  - Add placeholder `base.css`, `tokens.css`, `dark/tokens.css`,
    `light/tokens.css`, `light/overrides/button.css`, `light/overrides/checkbox.css`
    and the listed `controls/*.css` / `views/*.css` (empty or minimal) so every
    referenced path exists.

- [ ] **1.2 — `_themes.py` loader**
  - `ThemeRegistry` that reads `registry.json` (relative to the `themes/` dir),
    validates every referenced file exists, and exposes:
    - `list_themes() -> list[str]`
    - `theme_label(theme_id) -> str`
    - `theme_css_files(theme_id) -> list[str]` (resolved order: `base` → default
      `tokens` → theme `tokens` → `components` → theme `overrides`).
    - `default_theme() -> str` (first entry, `"dark"`).
  - Raise `ValueError`/`KeyError` on unknown theme or missing file.

- [ ] **1.3 — Exports**
  - Export `list_themes` / `theme_css_files` (and the registry object if useful)
    from `py/pytanga/viz/__init__.py` (`__all__`).

- [ ] **1.4 — Tests (`test_themes.py`)**
  - Resolved order for `dark` and `light` (exact list).
  - Unknown theme raises; missing file raises.
  - `list_themes()` returns `["dark", "light"]`.
  - Drift guard: every `.css` under `themes/controls/` and `themes/views/` is
    referenced by `components` (mirror `test_export_renderers.py`).

## Validation

`uv run pytest py/tests/viz/test_themes.py -q`
