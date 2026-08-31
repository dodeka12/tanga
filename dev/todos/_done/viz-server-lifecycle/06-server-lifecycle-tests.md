# Phase 6 — Server lifecycle, dead-parameter & layout-URL tests

## Goal

Add regression tests covering the lifecycle fixes, the dead-parameter fixes, and
the layout-URL fix.

## Files

- New: `py/tests/viz/test_server_lifecycle.py`

## Steps

- [x] **6.1 — Test that `start_server()` does not call `set_event_loop`**
  - Monkeypatch `asyncio.set_event_loop` to a recording spy; run a real
    `viz.start_server(port=0)` + `viz.stop_server()`; assert `set_event_loop`
    was never called.
- [x] **6.2 — Test signal handlers are restored on stop**
  - Record `signal.getsignal(SIGINT)` / `signal.getsignal(SIGTERM)`; run
    `start_server(port=0)` + `stop_server()`; assert both are restored.
- [x] **6.3 — Test a busy port surfaces a clear message, not a traceback**
  - Bind a socket to a free port and `listen()`; call
    `viz.start_server(port=that_port)`; assert `SystemExit` (code 1), stderr
    contains "already in use" and no traceback (`capsys`), and
    `_server`/`_loop`/`_thread` are `None`.
- [x] **6.4 — Test `_ensure_server_running` re-raises the real boot error**
  - Monkeypatch `VizServer.start` to raise `PortInUseError`; call
    `viz._ensure_server_running()`; assert `PortInUseError` is raised (not the
    generic 5 s timeout) and the loop/thread/server fields are cleaned up.
- [x] **6.5 — Test `stop_server()` restores handlers when the server is `None`**
  - Seed `viz._saved_signal_handlers` and set `viz._server = None`; call
    `stop_server()`; assert the prior handlers are restored.
- [x] **6.6 — Test `show()` falls back to the constructor `host`/`port`**
  - Build `Visualizer(port=9000, host="127.0.0.1")`; monkeypatch
    `start_server`/`open_browser`/`display`; call `show()`; assert
    `start_server` received `host="127.0.0.1"`, `port=9000`.
- [x] **6.7 — Test `show()` honours `open_browser=False`**
  - Build `Visualizer(open_browser=False)` (non-Jupyter); monkeypatch
    `start_server` (no-op) and `open_browser` (record); call `show()`; assert it
    returns `True` and `open_browser` was not called.
- [x] **6.8 — Test `VisualizerApp` forwards `add_default_axes`/`add_default_grid`**
  - Build `VisualizerApp(add_default_axes=False, add_default_grid=False)`; assert
    `app.viz._add_default_axes is False` and `app.viz._add_default_grid is False`.
- [x] **6.9 — Test `VisualizerApp.run()` threads `timeout` into `show()`**
  - Set `app._stop_requested.set()`; monkeypatch `app.viz.show` (record kwargs,
    return `True`) and `app.viz.stop_server` (no-op); call
    `app.run(wait_for_browser=False, timeout=7.5)`; assert `show` was called
    with `timeout=7.5`.
- [x] **6.10 — Test the layout URL is passed through and opened**
  - Monkeypatch `viz.wait_for_browser` to record kwargs (return `True`); call
    `viz._open_browser_url("/?view=main&token=abc", wait_for_browser=True)` with
    `reuse_existing=True`; assert `wait_for_browser` received
    `path="/?view=main&token=abc"`.
  - Separately, monkeypatch `builtins.input` (simulate Enter) and
    `viz._server.open_browser` (record) with a fake server exposing
    `_any_ws_ready_thread`/`_clear_ws_ready_events`; call
    `viz.wait_for_browser(path="/?view=main&token=abc")`; assert `open_browser`
    was called with that path.

## Validation

`uv run pytest py/tests/viz/test_server_lifecycle.py -q`

## Notes

- Real boots use `port=0` (ephemeral) and `add_default_axes=False,
  add_default_grid=False` to stay fast; `Visualizer` binds `127.0.0.1` + `::1`
  with best-effort IPv6 (already handled in `VizServer.start`).
- The port-in-use test binds only `127.0.0.1`; `SO_REUSEADDR` does not allow a
  second bind while the first socket is actively `listen()`ing, so the bind
  still fails with `EADDRINUSE`.
