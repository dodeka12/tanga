# Phase 5 — `show(layout=…)` opens the layout URL on the reconnect path

## Goal

Fix `show(layout=…)` so the default `reuse_existing=True, wait_for_browser=True`
path opens the layout URL (`/?view=<name>&token=…`) instead of the plain
`/?token=…` (see `dev/notes/pytanga-layout-url-not-opened.md`).

## Files

- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **5.1 — Add an optional `path` argument to `wait_for_browser()`**
  - Signature: `wait_for_browser(self, timeout: float = 120.0, path: str | None = None)`.
  - In the "user chose to open a new tab" branch, open
    `self._server.open_browser(path)` when `path` is given; otherwise generate
    the token and open `f"/?token={page_token}"` as today.
- [x] **5.2 — Pass the pending URL from `_open_browser_url()`**
  - In the `reuse_existing=True, wait_for_browser=True` branch, replace
    `self.wait_for_browser(timeout=…)` with
    `self.wait_for_browser(timeout=…, path=token_url)` (keep the `timeout`
    plumbing added in Phase 4).
  - This opens the layout URL for `show(layout=…)` and, incidentally, the
    correct named-scene URL for `VizSceneHandle.open_browser()`.
- [x] **5.3 — Print the layout URL in the connect prompt**
  - In `wait_for_browser()`, when `path` is given, show `path` (resolved to a
    full URL) instead of just `self.url` in the connect prompt, so manual
    copy/paste keeps the `?view=` param.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- The frontend already treats a present-but-empty `?view=` as layout mode
  (`viewer.js:52-55`); no JS change is needed — only the opened URL.
- `_open_browser_url` will already carry the `timeout` parameter from Phase 4;
  build on that, don't re-add it.
