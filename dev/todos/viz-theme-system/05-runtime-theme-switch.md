# Phase 5 — Runtime theme switching

## Goal

Make `set_theme` change the theme live: push a `theme_define` message to all
connected clients so `themes.js` swaps the `<link>`s without a page reload.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/templates/themes.js`
- New/extend: `py/tests/viz/test_themes.py` (or `test_server_layout.py`)

## Steps

- [ ] **5.1 — Push on `set_theme` (`visualizer.py`)**
  - `set_theme(theme_id)` validates, stores `self._theme`, and pushes
    `theme_define { theme, label, css: theme_css_files(theme_id) }` to all clients
    via `asyncio.run_coroutine_threadsafe(self._server.push_raw(...), self._loop)`.
  - Add `set_theme_async` (loop-safe, mirroring `_push_controls_async`).

- [ ] **5.2 — Frontend swap (`themes.js`)**
  - `handleThemeDefine` replaces `[data-tanga-theme]` links and updates a
    `data-tanga-theme-name` marker on `<html>`/`<body>` (for any theme-scoped
    selectors); no reload.

- [ ] **5.3 — Tests**
  - `set_theme` emits exactly one `theme_define` with the resolved `css` list and
    the new `theme`/`label` (fake server / captured push).

## Validation

`uv run pytest py/tests/viz/test_themes.py -q && node --check py/pytanga/viz/templates/themes.js`
