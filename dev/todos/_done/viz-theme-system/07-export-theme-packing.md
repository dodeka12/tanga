# Phase 7 — Export theme packing

## Goal

Pack the active theme's CSS into self-contained HTML exports, symmetric to how
JS renderers are bundled.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/templates/export_viewer.html`
- Edit: `py/pytanga/viz/export/_figure_html.py` (+ animated path)
- Edit: `py/pytanga/viz/visualizer.py` (pass `theme` to renderers)
- Extend: `py/tests/viz/test_export_static.py` / `test_export_renderers.py`

## Steps

- [x] **7.1 — `generate_theme_css(theme_id)` (`_bootstrap/_html.py`)**
  - Read the resolved CSS files (via `theme_css_files`) and return one
    `<style>…</style>` block (concatenated in order). Reuse the registry loader.

- [x] **7.2 — Export templates**
  - Add a `__THEME_CSS__` placeholder to `export_viewer.html`; thread a
    `theme_css` param through `html_fullpage_template` / `html_snippet_template`
    and the animated/figure paths.

- [x] **7.3 — `render_snapshot` / figure / animated `theme` param**
  - Add `theme: str = "dark"` to `render_snapshot`, `render_figure`, and the
    animated renderers; inject the packed CSS.
  - In `visualizer.py`, pass `self.theme` (or an explicit arg) through
    `_render_snapshot_html` and the export call sites.

- [x] **7.4 — Tests**
  - Exported HTML contains the `base.css` rules (e.g. the `--tanga-bg` token and
    the borderless-icon rule); a `light` export contains `light/tokens.css`
    rules/overrides.

## Validation

`uv run pytest py/tests/viz/test_export_static.py py/tests/viz/test_export_renderers.py py/tests/viz/test_themes.py -q`
