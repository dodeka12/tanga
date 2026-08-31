# Viz Server Lifecycle & Start/Show Flow — Overview

**Created:** 2026-08-31 | **Status:** Done | **Branch:** `fix/scene-alert`

## Goal

1. Fix `Visualizer` / `SdfVisualizer` so starting and stopping the viewer server
   no longer corrupts process-global state (the caller's event loop and the
   `SIGINT`/`SIGTERM` handlers), and a "port already in use" failure is reported
   as a single clear message instead of a traceback or a misleading 5 s timeout.
2. Fix the accepted-but-ignored `Visualizer` / `VisualizerApp` constructor and
   `run()` parameters (`port`, `host`, `open_browser`, `timeout`,
   `add_default_axes`, `add_default_grid`) so they take effect through the
   modern `show()`/`run()` flow.
3. Fix `show(layout=…)` so the default `reuse_existing=True,
   wait_for_browser=True` path actually opens the layout URL
   (`/?view=<name>&token=…`) instead of the plain `/?token=…`.

## Background

Three reference notes:

- `dev/notes/viz_server_lifecycle_2026-08-31.md` — server start/stop corrupts
  global state: `asyncio.set_event_loop(...)` on the caller's thread, replaced
  `SIGINT`/`SIGTERM` handlers never restored, a swallowed boot error (busy port →
  misleading 5 s timeout), and a `stop_server()` that can't clean up a failed
  start.
- `dev/notes/pytanga-dead-params.md` — `Visualizer(port=…, host=…,
  open_browser=…)` and `VisualizerApp(timeout=…, add_default_axes=…,
  add_default_grid=…)` are accepted but ignored.
- `dev/notes/pytanga-layout-url-not-opened.md` — `show(layout=…)` builds the
  layout URL but the reconnect/Enter path discards it and opens `/?token=…`, so
  the frontend never sees `?view=` and renders a blank single scene.

## Architecture (short)

The server loop already runs in a dedicated background thread
(`self._loop.run_forever()`), and every cross-thread call already targets
`self._loop` explicitly. So the lifecycle fix is: stop calling `set_event_loop`,
save/restore the signal handlers, surface the real boot error, and report a busy
port cleanly. The start/show-flow fixes are: make `show()` fall back to the
constructor `host`/`port` and honour `open_browser`; thread
`VisualizerApp.run(timeout=…)` down to `wait_for_browser(timeout=…)`; forward
`add_default_axes`/`add_default_grid`; and pass the already-built URL through
`_open_browser_url()` → `wait_for_browser(path=…)` so the layout (and named
scene) URL is what actually opens.

## Decisions (confirmed)

- **No `set_event_loop`.** Remove the call; nothing relies on the loop being
  current (verified: no `asyncio.get_event_loop()` in `py/pytanga/viz/`).
- **Signal handlers: save + restore.** `signal.getsignal` before install,
  `signal.signal` to restore in `stop_server()`, stored on
  `self._saved_signal_handlers`. Not `loop.add_signal_handler` (background
  thread).
- **Dedicated `PortInUseError(RuntimeError)`** raised by `VizServer.start()`.
- **No traceback for a busy port.** `start_server()` (both classes) catches
  `PortInUseError`, prints a clear message to stderr, and `raise SystemExit(1)`.
- **Failed boot is cleaned up.** Stop loop, join thread, null
  `self._server`/`self._loop`/`self._thread` before re-raising.
- **Constructor `port`/`host` become effective** via `show()` falling back to
  `self._host`/`self._port` when its own args are `None` (non-breaking; the
  existing `DeprecationWarning` stays).
- **`open_browser=False` becomes effective** in `show()` (skip `open_browser()`
  in the non-Jupyter branch, return `True`).
- **`VisualizerApp.run(timeout=…)` becomes effective** by threading `timeout`
  through `show()` → `open_browser()` → `wait_for_browser(timeout=…)`.
- **`add_default_axes`/`add_default_grid` are forwarded** by
  `VisualizerApp.__init__`.
- **Layout URL is opened on the reconnect path.** Give `wait_for_browser()` an
  optional `path` argument and pass the already-built `token_url` from
  `_open_browser_url()` in the `reuse_existing=True, wait_for_browser=True`
  branch (the "pass the URL through" option — not "open before waiting", which
  would defeat `reuse_existing`). This also fixes the latent named-scene bug
  where the Enter path always opened the main-scene URL.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-visualizer-server-lifecycle.md](./01-visualizer-server-lifecycle.md) | Fix `Visualizer` lifecycle (loop, signals, boot error, port message) |
| 2 | [02-sdf-visualizer-server-lifecycle.md](./02-sdf-visualizer-server-lifecycle.md) | Apply the same fixes to `SdfVisualizer` |
| 3 | [03-visualizer-dead-params.md](./03-visualizer-dead-params.md) | `show()` honours constructor `host`/`port`/`open_browser` |
| 4 | [04-visualizerapp-dead-params.md](./04-visualizerapp-dead-params.md) | `VisualizerApp` `timeout` + `add_default_axes`/`add_default_grid` |
| 5 | [05-layout-url-not-opened.md](./05-layout-url-not-opened.md) | `show(layout=…)` opens the layout URL on the reconnect path |
| 6 | [06-server-lifecycle-tests.md](./06-server-lifecycle-tests.md) | Regression tests (lifecycle + dead params + layout URL) |
| 7 | [07-docs-changelog.md](./07-docs-changelog.md) | Changelog entry |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check py/pytanga/viz/ py/tests/viz/`
- `uv run mkdocs build --strict` (changelog phase only)

## Non-goals

- No change to the `VizServer` wire protocol or the JS frontend (the frontend
  already treats a present `?view=` as layout mode).
- No change to the IPv6 best-effort bind behaviour.
- No removal of the deprecated constructor `port`/`host`/`run()` (kept as
  working compat shims).
- No change to the `reuse_existing` reconnect semantics themselves — only the
  URL that is opened when the user opts to open a new tab.
- No public re-export of `PortInUseError`.
