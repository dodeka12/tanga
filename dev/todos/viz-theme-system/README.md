# Viz Theme System — Overview

**Created:** 2026-09-01 | **Status:** Done | **Branch:** `feat/viz-theme-system`

## Goal

Add a **CSS theme system** to the Tanga viewer that mirrors the renderer
architecture: one CSS file per control / UI element, a **base** sheet for global
look & feel (e.g. borderless icons everywhere), a **JSON registry** of themes,
backend theme selection with **runtime switching**, and **self-contained HTML
export** that packs the active theme's CSS into the file. All appearance moves
out of JS (no injected `<style>` blocks, no inline appearance styles); the JS
only assigns stable semantic class names and applies *computed geometry* inline.

## Architecture (short)

- **CSS lives under `py/pytanga/viz/templates/themes/`** (mirrors
  `templates/renderers/`):
  - `base.css` — CSS custom properties (design tokens) + global structural rules.
  - `controls/*.css` / `views/*.css` — one file per control/view, referencing
    `var(--tanga-…)` instead of hardcoded colors.
  - `<theme>/tokens.css` — overrides token *values* per theme.
  - `<theme>/overrides/*.css` — optional full re-definition of a single element.
- **Registry** — `templates/themes/registry.json` is the single source of truth
  (theme id → ordered CSS file list). Python `_themes.py` loads/validates it and
  resolves the ordered file list; the browser never parses JSON (it receives the
  resolved list over the wire).
- **Live viewer** — `VizServer` injects the active theme's `<link>`s into
  `viewer.html` on page load; a new `templates/themes.js` manager swaps
  `<link data-tanga-theme>` tags when a `theme_define` message arrives.
- **Runtime switching** — `Visualizer.set_theme(id)` pushes `theme_define` to all
  clients (reusing the existing `push_raw` + event-loop handoff).
- **Export** — `generate_theme_css(theme_id)` inlines the resolved CSS into a
  single `<style>` block, packed into `render_snapshot` / `render_figure` /
  animated exports (symmetric to how `generate_bootstrap_js` packs `_RENDERER_FILES`).

## Registry contract (fixed up front)

### `templates/themes/registry.json`

```jsonc
{
  "base": ["base.css"],
  "tokens": "tokens.css",
  "components": [
    "controls/button.css",
    "controls/slider.css",
    "controls/checkbox.css",
    "controls/dropdown.css",
    "controls/text-field.css",
    "controls/text-area.css",
    "controls/color-picker.css",
    "controls/value-edit.css",
    "controls/file-chooser.css",
    "controls/table.css",
    "views/group-view.css",
    "views/menu-view.css",
    "views/dialog-view.css",
    "views/banner-view.css",
    "views/overlay-view.css",
    "views/stack-view.css"
  ],
  "themes": {
    "dark": { "label": "Dark", "tokens": "dark/tokens.css", "overrides": {} },
    "light": {
      "label": "Light",
      "tokens": "light/tokens.css",
      "overrides": {
        "button": "light/overrides/button.css",
        "checkbox": "light/overrides/checkbox.css"
      }
    }
  }
}
```

- All paths are relative to `templates/themes/`. Every referenced file must
  exist (validated at load), and every `.css` file on disk under `controls/` /
  `views/` must be referenced by `components` (drift-guard, mirroring
  `test_export_renderers.py`).
- `overrides` is keyed by component id → path; the order of the map is preserved
  in the resolved list.

### Resolved order (later wins at equal specificity)

`base` → `tokens` (default) → theme `tokens` → `components` → theme `overrides`.

### Stable class contract

The JS must assign **stable semantic classes** (`.tanga-button`, `.tanga-slider`,
`.tanga-checkbox`, `.tanga-group-header`, `.tanga-menu-trigger`, `.tanga-dialog`,
…) and never inline appearance; overrides target those classes. Computed geometry
(overlay anchors, banner `transform`, drag `left/top`) stays inline.

### Wire message

```json
{ "type": "theme_define", "theme": "light", "label": "Light",
  "css": ["base.css", "tokens.css", "light/tokens.css", "controls/button.css", "…"] }
```

## Decisions (confirmed)

- **Layered, with full override.** Shared per-element sheets + per-theme token
  sheets are the default; a theme may additionally override a whole element via
  `overrides` (enables different shapes, widget rendering, states, density,
  iconography, accessibility variants, branding).
- **JSON registry** (`registry.json`) as the single source of truth — easiest to
  add/install themes without touching Python. Python loads/validates it.
- **Theme is viewer-global** (`Visualizer.theme`), not per-scene, like `_layouts`.
- **Frontend never reads the JSON** — it receives the resolved `css` list in
  `theme_define`.
- **Export inlines CSS** (single `<style>`), same self-contained model as JS.
- **All injected CSS + inline appearance move to files**; only computed geometry
  remains inline in JS.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-theme-registry-json.md](./01-theme-registry-json.md) | `registry.json` schema + `_themes.py` loader/validator + `list_themes`/`theme_css_files` + tests |
| 2 | [02-extract-base-control-css.md](./02-extract-base-control-css.md) | `base.css` + `controls/*.css` + `views/stack-view.css` extracted from injected JS; de-inline control appearance |
| 3 | [03-example-control-theming.md](./03-example-control-theming.md) | Example: controls render from extracted CSS (borderless icons, tokens) |
| 4 | [04-theme-selection-serving.md](./04-theme-selection-serving.md) | `Visualizer.theme`/`set_theme`; server `theme_callback`; `viewer.html` `<link>` injection; `theme_define` + `themes.js` + routing |
| 5 | [05-runtime-theme-switch.md](./05-runtime-theme-switch.md) | Runtime `set_theme` swaps `<link>`s without reload (loop-safe push) |
| 6 | [06-example-theme-switching.md](./06-example-theme-switching.md) | Example: switch theme at runtime (a control triggers backend `set_theme`) |
| 7 | [07-export-theme-packing.md](./07-export-theme-packing.md) | `generate_theme_css(theme_id)` + export template placeholders + `render_snapshot`/figure/animated `theme` param + tests |
| 8 | [08-full-deinline-appearance.md](./08-full-deinline-appearance.md) | Finish remaining inline appearance: `viewer.html` status/loading, `three-view.js` warning banner, `banner-view.js` |
| 9 | [09-example-custom-theme-override.md](./09-example-custom-theme-override.md) | Example: custom theme with a full button/checkbox override |
| 10 | [10-docs-changelog.md](./10-docs-changelog.md) | Architecture doc + API docs + changelog + full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (targeted per phase; full suite in
  the final phase). New `test_themes.py` guards registry resolution + the
  drift between `registry.json` and the `themes/` directory.
- **JS syntax:** `node --check <module>` on new/edited `templates/**/*.js`.
- **JS DOM smoke:** pages under `dev/src/js-tests/` (mirroring
  `group-view-smoke.html`) that link the extracted CSS directly and assert
  borderless icons / class-based rendering.
- **Examples/docs:** `uv run python tools/generate-example-docs.py --check` after
  any example edit; `uv run mkdocs build --strict` in the final phase.

## Non-goals

- Theming the **3D geometry/entity renderers** (colors there remain style-driven
  via the Python style system) — this plan is UI controls/views only.
- A user-facing theme picker widget in the browser (theme is selected from the
  backend; a picker could be a later control).
- Per-scene or per-pane themes (theme is viewer-global).
- CSS preprocessors/bundlers (plain CSS files + `var()`, consistent with the
  "zero build step" frontend).
