# Changes since version 1.14.1

## New Features

- **CSS theme system** — the viewer's UI chrome (controls, panels, banners,
  dialogs, menus) is now themed via plain CSS under
  `py/pytanga/viz/templates/themes/`, with a `registry.json` that resolves a
  theme id (`dark`, `light`, or a custom theme like `pastel`) to an ordered CSS
  file list (`base.css` design tokens → per-theme `tokens.css` →
  per-control/view sheets → full `overrides/*.css`).  All injected `<style>`
  blocks and inline appearance styles moved out of the JS into these files; the
  factories now only assign stable semantic classes and inline computed geometry.
- **Backend theme selection + runtime switching** — `Visualizer.theme` /
  `set_theme(id)` (plus a loop-safe `set_theme_async`) validate against the
  registry and push a `theme_define` message so connected viewers swap their
  theme live without a page reload.  `list_themes()` / `theme_label()` /
  `theme_css_files()` are exported from `pytanga.viz`.
- **Theme-aware exports** — `export_snapshot` / `export_figure` (and scene
  handles) accept `theme=` to pack the resolved CSS into the self-contained
  HTML, symmetric to how renderer JS is bundled.
- **Examples** — new `control_theming.py` (controls styled from the theme CSS),
  `theme_switching.py` (runtime `set_theme` switching), and
  `custom_theme_override.py` (a `pastel` theme with a pill button and a
  switch-style checkbox override).
