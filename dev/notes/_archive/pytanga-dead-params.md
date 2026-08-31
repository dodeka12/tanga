# pytanga `Visualizer`/`VisualizerApp` dead parameters — note

**Created:** 2026-08-31 | **Status:** Reference note | **Branch:** `seating-plan-app`

A reference note documenting constructor/`run()` parameters in pytanga that are
accepted but have no effect through the modern `show()`/`run()` flow. Use this
as the starting point to fix them upstream in pytanga.

**Version observed:** `tanga-py` 1.11.0 (source under
`.venv/lib/python3.12/site-packages/pytanga/viz/`).

## 1. `Visualizer(port=…)` and `Visualizer(host=…)` — deprecated + ignored

- Where: `visualizer.py` `__init__` (starts ~line 108); stored at `self._port` /
  `self._host` (lines 152–153) after emitting a `DeprecationWarning`
  ("use `start_server(host=..., port=...)` instead").
- Why dead: `show()` (line 1977) — the entry point used by `run()` and every
  app — calls `start_server(host=host or "localhost", port=port)` with its
  *own* `host`/`port` args (default `None`). `start_server(port=None)`
  (line 1427; `port = DEFAULT_PORT` at line 1441, `DEFAULT_PORT = 8765` at
  line 67) overwrites `self._port`, so the constructor value never takes
  effect.
- Suggested fix: in `show()`, fall back to `self._host`/`self._port` when its
  own `host`/`port` are `None` (i.e. `start_server(host=host or self._host,
  port=port if port is not None else self._port)`), or drop the constructor
  `port`/`host` params and require `show(port=…)`/`start_server(port=…)`.

## 2. `Visualizer(open_browser=…)` — only read by deprecated `start()`

- Where: `visualizer.py` `__init__`, stored at `self._open_browser` (line 154).
- Why dead: `self._open_browser` is read only in the deprecated `start()`
  (line 1597; the read is at line 1612). `show()` decides inline-vs-browser via
  `jupyter`/`self._jupyter` and `reuse_existing`, never `_open_browser`.
- Suggested fix: remove the param, or wire it into `show()` so it actually
  suppresses/forces the browser open.

## 3. `Visualizer.run()` — deprecated shim

- Where: line 2045.
- What: warns "use `show()` then `wait()`". It calls `show()` without
  `host`/`port`, so it also discards the constructor port/host.
- Suggested fix: keep as a compat shim but forward `host`/`port` through to
  `show()` (or remove it).

## 4. `VisualizerApp.run(*, wait_for_browser=True, timeout=30.0)` — `timeout` unused

- Where: `_app.py` line 134.
- Why dead: the body never uses `timeout` (it is not passed to `show()` or
  `wait_for_browser()`). The effective wait timeout is hardcoded inside
  `_open_browser_url` / `wait_for_browser` (120 s reuse path, 30 s fresh-tab
  path).
- Suggested fix: thread `timeout` into `show()` → `wait_for_browser(timeout=…)`,
  or drop the parameter.

## 5. `VisualizerApp(port=…, host=…, open_browser=…)` — dead by transitivity

- Where: `_app.py` `__init__` (lines 52–88) forwards `port`, `host`,
  `open_browser` to `Visualizer(...)`.
- Why dead: they map onto #1 and #2.
- Suggested fix: same as #1/#2; additionally, `VisualizerApp.run()` should pass
  the port through to `viz.show(port=…)`.

## 6. (Related) `VisualizerApp` does not forward `add_default_axes`/`add_default_grid`

- Where: `_app.py` `__init__` (lines 73–84) forwards `title`, `camera`,
  `space_dim`, etc. but not `add_default_axes`/`add_default_grid`.
- Effect: `Visualizer.__init__` accepts those flags, but apps deriving from
  `VisualizerApp` cannot disable the default axes/grid (they have to call
  `viz.clear()` in `init()` instead).
- Suggested fix: add the two params and forward them.

## Local workaround (this repo)

- `SeatingPlanApp.run()` now passes `port=self._port` to
  `viz.show(layout=…, port=self._port, …)` instead of relying on the
  (dead) constructor port, and `SeatingPlanApp.__init__(port=…)` stores the
  port rather than forwarding it to `Visualizer(...)`. See
  `src/seating_plan/app.py`.

## Status

- [x] Documented here; worked around locally in `seating-plan-app`.
- [ ] Fix upstream in pytanga (this note is the starting point).
