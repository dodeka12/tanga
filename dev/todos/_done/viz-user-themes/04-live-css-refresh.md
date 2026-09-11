# Phase 4 — Live CSS refresh

## Goal

Let a user edit a theme's CSS on disk and see the change in a connected browser
without reloading the page, via `viz.refresh_theme()`.

## Files

- Edit: `py/pytanga/viz/visualizer.py` (`refresh_theme`, `version`)
- Edit: `py/pytanga/viz/templates/themes.js` (version + cache-bust)
- Edit: `py/pytanga/viz/templates/viewer.js` (no-op; verify background hook re-runs)
- Edit: `py/tests/viz/test_themes.py`

## Steps

- [x] **4.1 — Backend `version` + `refresh_theme()`**
  - Add `self._theme_version = 0` on `Visualizer`; bump it in `set_theme` and
    `refresh_theme` (and the async variants).
  - Add `refresh_theme()` that re-pushes `theme_define` for the **current**
    theme (no id change) with the bumped version; add loop-safe
    `refresh_theme_async()`.
  - Include `"version": self._theme_version` in `_theme_define_payload()`.

- [x] **4.2 — Frontend idempotency + cache-bust (`themes.js`)**
  - Track `_activeVersion`; make the idempotency key `(theme, version)`.
  - When re-applying, append `?v=<version>` to each `href` so the browser
    re-fetches (the server already serves `Cache-Control: no-cache`).
  - Keep the existing `Promise`/`onload` behavior so `viewer.js`'s
    `applyThemeBackgrounds()` still runs after the swap (this refreshes
    `--tanga-bg` too).

- [x] **4.3 — Tests (`test_themes.py`)**
  - `set_theme` emits `version`; `refresh_theme` emits a `theme_define` with the
    same `theme` but a bumped `version`.
  - `_theme_define_payload` contains `version`.

- [x] **4.4 — Auto-reload (`visualizer.py`)**
  - `enable_theme_auto_reload(poll_interval=1.0)` — a daemon thread polls
    the active theme's `tokens.css` + `overrides/*.css` (via
    `theme_source_files`) and calls `refresh_theme()` on change.
  - `disable_theme_auto_reload()` — stops the watcher.

- [x] **4.5 — Auto-reload + custom-theme docs**
  - New `docs/py/viz/visualizer/custom-themes.md` (create / load /
    auto-reload walkthrough + token reference), wired into `mkdocs.yml` and
    linked from `theming.md`.

## Validation

`node --check py/pytanga/viz/templates/themes.js && uv run pytest py/tests/viz/test_themes.py -q`
