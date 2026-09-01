# Viz User Themes — Overview

**Created:** 2026-09-02 | **Status:** Planned | **Branch:** `feat/viz-theme-system`

## Goal

Let a downstream project (using Tanga as a dependency) ship its own viewer
theme as plain CSS — a `tokens.css` plus optional `overrides/*.css` in a local
folder — and load it in the viewer without editing the bundled
`py/pytanga/viz/templates/themes/`. Adds:

- `register_theme(name, path)` — register an external theme folder (global, one-time).
- `copy_theme(theme_id, dest)` — scaffold a new theme from a built-in one.
- `refresh_theme()` — live-reload the active theme's CSS in a connected browser.
- Documentation of every themeable token and the stable override class contract.

## Architecture (short)

- The bundled `ThemeRegistry` already resolves a theme id → ordered CSS file
  list relative to `templates/themes/`. We extend it so a theme can also be an
  **external folder**: `tokens.css` (required) + `overrides/*.css`
  (auto-discovered, sorted).
- Because external files live *outside* `templates/themes/`, resolution must
  track two paths per file:
  - **served path** — the URL-relative path the browser requests
    (`user/<id>/tokens.css`, `user/<id>/overrides/*.css`);
  - **source path** — the absolute path on disk (for export inlining and the
    `copy_theme` scaffold).
  Resolution order stays: `base → default tokens → theme tokens → components →
  theme overrides`.
- **Serving** — `VizServer` gains a `theme_static_dirs` mapping and adds aiohttp
  static routes under `/themes/user/<id>/`, so the existing frontend
  (`themes.js`, which just prefixes every entry with `themes/`) needs no change
  for loading.
- **Live refresh** — `theme_define` gains a `version` field; `refresh_theme()`
  bumps it and re-pushes. `themes.js` reloads the `<link>`s when `(theme,
  version)` changes, appending `?v=<version>` as a cache-buster.
- **Export** — `generate_theme_css(theme_id)` already reads
  `registry.theme_css_paths(theme_id)`; with the registry returning external
  source paths it inlines external themes unchanged.

## Decisions (confirmed)

- **Global one-time registration** (`register_theme(name, path)` at module
  level) — simplest, and export needs no registry threading.
- External theme folder = `tokens.css` (required) + flat `overrides/*.css`
  (optional, auto-discovered).
- Reserved served namespace `user/<id>/` under `themes/` (no collision with
  bundled `dark/`, `light/`, `pastel/`, `controls/`, `views/`).
- `copy_theme` copies the theme's **own** `tokens.css` + `overrides/` (faithful),
  not the library-owned `base.css`/`components`.
- Live refresh is **manual** (`refresh_theme()`); an auto file-watcher is a
  deferred follow-up (no new dependency).

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-register-external-themes.md](./01-register-external-themes.md) | Registry refactor (`_ResolvedCss`), `register_theme`, served-vs-source resolution, `external_theme_dirs`, exports + tests |
| 2 | [02-serve-external-theme-css.md](./02-serve-external-theme-css.md) | Server static routes for `themes/user/<id>/…`, Visualizer wiring + tests |
| 3 | [03-copy-theme-scaffold.md](./03-copy-theme-scaffold.md) | `copy_theme(theme_id, dest)` scaffold + tests |
| 4 | [04-live-css-refresh.md](./04-live-css-refresh.md) | `refresh_theme()` + `theme_define.version` + `themes.js` cache-bust + tests |
| 5 | [05-document-theme-tokens.md](./05-document-theme-tokens.md) | Document the 27 design tokens + stable override class contract |
| 6 | [06-example-final-validation.md](./06-example-final-validation.md) | End-to-end example, docs generation, full validation |

## Testing as you go

- **Python:** `uv run pytest py/tests/viz/ -q` (targeted per phase; full suite in
  the final phase). Extend `test_themes.py` (registry resolution, served vs
  source, validation), `test_server_layout.py` (external CSS serving),
  `test_export_static.py` (external theme packing).
- **JS syntax:** `node --check py/pytanga/viz/templates/themes.js` after the
  `version` change.
- **Examples/docs:** `uv run python tools/generate-example-docs.py --check`
  after the example edit; `uv run mkdocs build --strict` in the final phase.

## Non-goals

- Auto file-watching / hot-reload daemon (manual `refresh_theme()` only, for now).
- Per-scene or per-pane themes (theme is viewer-global).
- A browser-side theme picker (theme is selected from the backend).
- Theming the 3D geometry/entity renderers (unchanged — UI chrome only).
