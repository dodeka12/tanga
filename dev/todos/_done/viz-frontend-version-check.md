# Viz Frontend Version Check — Stale-Cache Detection & Reload Prompt

**Created:** 2026-08-18 | **Status:** Done (pending manual browser smoke test)

## Goal

Stop the recurring "browser is running a cached, out-of-date visualizer" failure
mode. Add a content hash of the frontend assets that the backend computes and
advertises, and have the frontend compare its own embedded hash against it on
every WebSocket connect. On mismatch, show a persistent warning banner with a
**Reload now** button that forces a cache-bypassing full refresh.

The check is deliberately **backward compatible in both directions**, so each
step below can be shipped and verified independently without breaking old or
new clients.

## Background

- `py/pytanga/viz/server.py` (`VizServer`, aiohttp) serves `viewer.html` via
  `_catch_all_handler()` (injecting a `page_token`) and static JS modules
  (`viewer.js`, `renderers/*.js`, …) via `web.FileResponse`. **No
  `Cache-Control` headers are set**, so browsers use heuristic caching and can
  keep stale frontend files after the package is upgraded or files are edited.
- `py/pytanga/viz/templates/viewer.html` + `viewer.js` are the live frontend.
  On WebSocket open, `viewer.js` sends `{"type":"ready", ...}`; the backend
  replies with `{"type":"browser_id", "browser_id": ...}` as the **first**
  message, before any scene data — the ideal hook for the handshake.
- The package version is managed by `hatch-vcs` (git-derived). There is no
  `__version__` constant; `importlib.metadata.version("tanga-py")` works but
  does **not** change when template files are edited in place (dev/editable
  installs), so it is not a reliable signal by itself.

## Guiding decisions

- **Content hash, not semver.** The "version" is a SHA-256 hash over the live
  viewer's template directory (`py/pytanga/viz/templates/`), including each
  file's **relative path** and contents. Path is included because renames
  matter (they break module imports). This detects any change without needing a
  version bump.
- **Single source of truth = the backend.** The backend computes the hash and
  both (a) injects it into the served `viewer.html` and (b) sends it in the
  `browser_id` WS message. The frontend just compares what it was given.
- **Check location = the `browser_id` message** in `viewer.js`, since it is the
  earliest, unconditionally-sent message on every (re)connect. This also covers
  the "long-lived tab reconnects to an upgraded backend" case, which HTTP cache
  headers alone cannot fix.
- **Silent no-op when either side lacks the field** — old frontend + new backend,
  or new frontend + old backend, must keep working. This is what makes the
  steps independently shippable.
- **Reload must bypass cache.** Use `location.replace(url + '?t=' + Date.now())`
  rather than `location.reload(true)` (deprecated/ignored). A query param is
  safe because scene routing is path-based (`_myScene` reads `location.pathname`).

## Files

- Modify: `py/pytanga/viz/server.py`
- Modify: `py/pytanga/viz/templates/viewer.js`
- Add tests: `py/tests/viz/test_frontend_version.py`
- Modify: `docs/changelog/2026-08-18_95486fd.md` (latest, unreleased)
- Modify: `docs/changelog/index.md` (the `## [Since 0.9.2] — 2026-08-18` summary)

## Steps

### Step 1 — Backend: compute & inject the frontend version hash

Pure backend change; the injected JS variable is inert until Step 3, so this is
safe to ship on its own.

- [x] Add `import hashlib` to `server.py`.
- [x] Add a module-level helper:
      ```python
      def compute_frontend_version(static_dir: Path) -> str:
          """Stable content hash over the frontend assets served by this server."""
          h = hashlib.sha256()
          for p in sorted(static_dir.rglob("*")):
              if p.is_file():
                  h.update(str(p.relative_to(static_dir)).encode("utf-8"))
                  h.update(b"\0")
                  h.update(p.read_bytes())
          return h.hexdigest()[:16]
      ```
- [x] In `VizServer.__init__`, store
      `self._frontend_version = compute_frontend_version(self._static_dir)`.
      (`__init__` runs on the caller thread in `_ensure_server_running`, before
      the event loop starts — file I/O there is safe.)
- [x] In `_catch_all_handler`, inject **both** the page token and the version
      (replace the existing single `token_script` injection):
      ```python
      inject = (
          f'<script>window.__tanga_page_token = "{page_token}";</script>\n'
          f'<script>window.__tanga_frontend_version = "{self._frontend_version}";</script>'
      )
      if "</head>" in html:
          html = html.replace("</head>", f"{inject}\n</head>")
      else:
          html = inject + "\n" + html
      ```

**Tests (Step 1):**
- [x] New `py/tests/viz/test_frontend_version.py`:
  - [x] Returns a 16-char hex string for a temp dir.
  - [x] Deterministic: hashing the same dir twice gives the same result.
  - [x] Content-sensitive: editing a file changes the hash.
  - [x] Structure-sensitive: adding a file changes the hash.
  - [x] (Optional) Path-sensitive: renaming a file changes the hash even if
        content is identical.

### Step 2 — Backend: advertise the version over WebSocket

Independent of Step 3 because old frontends ignore unknown fields.

- [x] In `_ws_handler`, extend the `browser_id` payload:
      ```python
      bid_payload = json.dumps({
          "type": "browser_id",
          "browser_id": browser_id,
          "frontend_version": self._frontend_version,
      })
      ```
- [x] (Optional) Update `_ws_msg_brief` for `browser_id` to also log the
      version for diagnostics, e.g. `browser_id id=… v=<hash>`.

**Verification (Step 2):** manual — start a server (`dev/src/test_viz_smoke.py`
or a small script), open DevTools → Network/WS, and confirm the first WS frame
includes `frontend_version`.

### Step 3 — Frontend: detect mismatch & show the warning banner

This is where the feature becomes visible. Independent of Steps 1–2 because the
comparison no-ops when `msg.frontend_version` or `window.__tanga_frontend_version`
is absent.

- [x] In `viewer.js`, near the module state (top), capture the injected value:
      ```js
      const _frontendVersion =
          (typeof window !== 'undefined' && window.__tanga_frontend_version) || null;
      ```
- [x] In `handleMessage`, extend the existing `browser_id` branch:
      ```js
      if (msg.type === 'browser_id') {
          _browserId = msg.browser_id;
          _log('init', 'browser_id=' + msg.browser_id);
          if (msg.frontend_version && _frontendVersion
              && msg.frontend_version !== _frontendVersion) {
              showVersionMismatchBanner(msg.frontend_version, _frontendVersion);
          }
          return;
      }
      ```
- [x] Add `showVersionMismatchBanner(serverVersion, clientVersion)`:
      - Persistent, full-width, top-of-page banner at `z-index > 100000`
        (above `#tanga-loading`).
      - Text: "The visualizer is out of date — backend expects version `<server>`
        but this page is running `<client>`. Please hard-reload."
      - A **Reload now** button that calls a cache-bypassing reload:
        ```js
        function hardReload() {
            const url = new URL(window.location.href);
            url.searchParams.set('t', Date.now().toString());
            window.location.replace(url.toString());
        }
        ```
      - Style it to match the existing slow-connection/error banners in
        `viewer.html` (sans-serif, dark/amber theme). Implement in JS (consistent
        with the other dynamic overlays in `viewer.js`) rather than adding HTML
        markup — keeps this step to one file.

**Verification (Step 3):** manual — with the dev tools, temporarily force a
mismatch (e.g. edit a template file after the page is open, restart the server,
then let the tab auto-reconnect) and confirm the banner appears and the button
reloads the page fresh.

### Step 4 (optional) — Cache-Control hardening at the source

Complementary fix that reduces how often the warning is needed. Ship separately
so any regression is easy to bisect.

- [x] In `_catch_all_handler`, pass `headers={"Cache-Control": "no-cache"}` to
      the `web.FileResponse` for static modules.
- [x] Add `"Cache-Control": "no-cache"` to the `viewer.html` `StreamResponse`
      headers.
- Note: aiohttp `FileResponse` already handles `ETag`/`Last-Modified`
      conditional revalidation, so unchanged files still return `304` (cheap).

### Step 5 — Changelog (latest, unreleased)

The current branch has not been released; update the existing changelog rather
than creating a new one.

- [x] `docs/changelog/2026-08-18_95486fd.md`: add a **New Features** section at
      the top (before `## Breaking Changes`) with a bullet like:
      `- **Frontend version check** — the viewer now verifies it matches the
      backend's frontend on every connect and prompts for a hard reload when a
      cached/out-of-date copy is detected.`
- [x] `docs/changelog/index.md`: extend the `## [Since 0.9.2] — 2026-08-18`
      summary bullet to mention the frontend version check.

## Verification (end-to-end)

- [x] `uv run pytest py/tests/viz/` passes (including the new
      `test_frontend_version.py`).
- [ ] Manual smoke: fresh server + fresh browser tab shows **no** banner; a tab
      left open across a template edit + server restart shows the banner and
      the Reload button clears it.

## Non-goals / optional follow-ups

- Surfacing the human-readable `tanga-py` version string in the banner
  (`importlib.metadata.version("tanga-py")`) for nicer diagnostics. Not required;
  keep the hash-only message unless it proves confusing.
- Version checking for the self-contained **export/snapshot** HTML path
  (`export_viewer.html`, `display_snapshot`/`display_static`). Those are static
  serverless documents with no WebSocket, so they are out of scope here.
- Auto-reload instead of prompting. Deliberately not done — a silent reload
  could lose in-flight user state; the explicit prompt is the safe default.


