# Viz theme system architecture

How the viewer's UI look & feel is themed — the CSS layout under
`py/pytanga/viz/templates/themes/`, the JSON registry that resolves a theme id to
an ordered CSS file list, backend theme selection + runtime switching, and how
the active theme is packed into self-contained HTML exports.

## Layers (resolved order)

A theme is an **ordered list of CSS files** resolved from
`templates/themes/registry.json`.  Later files win at equal specificity:

1. `base` — `base.css`: design tokens (`:root { --tanga-*: … }`), global reset /
   shell, the borderless-icon contract, and shared control chrome.
2. default `tokens` — `tokens.css`: the shared default token layer.
3. theme `tokens` — `<theme>/tokens.css`: overrides token *values* per theme
   (e.g. `light/tokens.css` re-themes the palette).
4. `components` — `controls/*.css` + `views/*.css`: one sheet per control/view,
   referencing `var(--tanga-…)` instead of hardcoded colors.
5. theme `overrides` — `<theme>/overrides/*.css`: an optional full re-definition
   of a single element (e.g. a pill button or a switch-style checkbox).

`registry.json` is the single source of truth; the Python loader
(`py/pytanga/viz/_themes.py`) reads and validates it and exposes
`list_themes()`, `theme_label()`, `theme_css_files()` (the resolved order), and
`default_theme()`.  The browser never parses the JSON — it receives the resolved
`css` list over the wire.

## Stable class-name contract

The JS assigns **stable semantic classes** (`.tanga-action-button`,
`.tanga-range-input`, `.tanga-checkbox`, `.tanga-banner`, `.tanga-dialog`,
`.tanga-menu-trigger`, `.tanga-warning-banner`, …) and **never inlines
appearance**.  Only *computed geometry* (overlay anchors, banner/dialog
`transform: translate(-x%,-y%)`, drag `left/top`) stays inline.  Overrides and
themes target those stable classes.

## Wire message

```json
{ "type": "theme_define", "theme": "light", "label": "Light",
  "css": ["base.css", "tokens.css", "light/tokens.css", "controls/button.css", "…"] }
```

## Live viewer

- `Visualizer.theme` / `set_theme(theme_id)` store the active theme id
  (viewer-global, default `"dark"`).  `set_theme` validates via `theme_css_files`
  and pushes `theme_define` to all connected clients
  (`run_coroutine_threadsafe(push_raw, loop)`); `set_theme_async` is the
  loop-safe variant.
- On page load, `VizServer` calls an optional `theme_callback` (wired to
  `Visualizer._theme_define_payload`) and injects one
  `<link rel="stylesheet" data-tanga-theme href="themes/…">` per resolved file
  into `viewer.html`'s `<head>` (after the page-token injection).  `base.css` is
  also linked statically in `viewer.html` for no-FOUC.
- `templates/themes.js::handleThemeDefine(msg)` swaps the `[data-tanga-theme]`
  links (idempotent per theme) and marks `data-tanga-theme-name` on `<html>`;
  `viewer.js` routes `theme_define` to it.

## Export packing

`generate_theme_css(theme_id)` (in `export/_bootstrap/_html.py`) reads the
resolved CSS files and returns one inlined `<style>` block — symmetric to how
`generate_bootstrap_js` packs the renderer modules.  It is threaded through
`render_snapshot` / `render_figure` / the animated renderers via a `theme: str =
"dark"` parameter (and `__THEME_CSS__` in `export_viewer.html`), and
`Visualizer.export_snapshot` / `export_figure` accept `theme=` (defaulting to
`self.theme`).

## Non-goals

- 3D geometry/entity renderer colors remain style-driven via the Python style
  system — this system themes **UI controls/views only**.
- No user-facing theme picker widget (theme is selected from the backend).
- No CSS preprocessors/bundlers — plain CSS files + `var()`, consistent with the
  zero-build-step frontend.
