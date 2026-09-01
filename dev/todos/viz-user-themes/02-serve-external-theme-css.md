# Phase 2 — Serve external theme CSS

## Goal

Make external theme files loadable in the browser. The frontend already requests
`themes/<served_rel>`; the server must map the reserved `themes/user/<id>/`
prefix to the registered theme folder.

## Files

- Edit: `py/pytanga/viz/server.py`
- Edit: `py/pytanga/viz/visualizer.py` (pass the dir map to the server)
- Edit: `py/tests/viz/test_server_layout.py`

## Steps

- [ ] **2.1 — `VizServer` static dirs**
  - Add `theme_static_dirs: dict[str, Path] | None = None` to
    `VizServer.start(...)` and store it (`{"user/<id>": dir}`).
  - In `_build_app()`, for each `(prefix, dir)`, register
    `app.router.add_static(f"/themes/{prefix}", dir, show_index=False)`
    (aiohttp's built-in static route — path-safe, correct MIME). These are more
    specific than the existing `/{name:.*}` catch-all, so they win for
    `themes/user/<id>/…`.

- [ ] **2.2 — Visualizer wiring**
  - In `Visualizer` server startup (near the existing
    `theme_callback=self._theme_define_payload` wiring), pass
    `theme_static_dirs=external_theme_dirs()`.

- [ ] **2.3 — Tests (`test_server_layout.py`)**
  - Build a `VizServer` with a temp theme dir; assert `_build_app()` serves
    `/themes/user/<id>/tokens.css` (and an override) and 404s for an unknown
    path inside the reserved prefix.

## Validation

`uv run pytest py/tests/viz/test_server_layout.py -q`
