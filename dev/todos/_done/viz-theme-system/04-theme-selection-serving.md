# Phase 4 — Theme selection + serving

## Goal

Add `Visualizer.theme` / `set_theme`, inject the active theme's `<link>`s into
`viewer.html`, and add a frontend `themes.js` manager that applies a
`theme_define` message.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/templates/viewer.html`
- New: `py/pytanga/viz/templates/themes.js`
- Edit: `py/pytanga/viz/templates/viewer.js`
- Extend: `py/tests/viz/test_server_layout.py` / new `test_themes_serving.py`

## Steps

- [x] **4.1 — `Visualizer.theme` / `set_theme` (`visualizer.py`)**
  - Store `self._theme` (default `"dark"`); add `theme` property and
    `set_theme(theme_id)` that validates via `theme_css_files` and records the id
    (push happens in Phase 5; this phase sets initial state).

- [x] **4.2 — Server `theme_callback` (`server.py`)**
  - Add optional `theme_callback: Callable[[], dict]` to `VizServer.start(...)`;
    when serving `viewer.html`, call it to build `<link rel="stylesheet"
    data-tanga-theme href="themes/…">` tags and inject them into `<head>` (after
    the existing page-token injection). Wire it in `visualizer.py`'s
    `_boot`/`start` to return the current theme's resolved files.

- [x] **4.3 — `viewer.html`**
  - Ensure `base.css` is linked statically (no-FOUC) and remove the old inline
    shell styles that moved to CSS (status/loading can stay until Phase 8).

- [x] **4.4 — `themes.js` manager**
  - `handleThemeDefine(msg)`: remove existing `[data-tanga-theme]` links and add
    one per `msg.css` path (in order). Idempotent per theme.

- [x] **4.5 — `viewer.js` routing**
  - Import `handleThemeDefine`; in the message switch, route `theme_define`.

- [x] **4.6 — Tests**
  - Server injects the theme `<link>`s for the default theme when
    `theme_callback` is set; omits them when unset (mirror `test_server_layout.py`).

## Validation

`uv run pytest py/tests/viz/test_server_layout.py py/tests/viz/test_themes.py -q && node --check py/pytanga/viz/templates/themes.js && node --check py/pytanga/viz/templates/viewer.js`
