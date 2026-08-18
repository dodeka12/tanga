# Phase 2 — Serving primitives (`start_server` / `stop_server` / `open_browser`)

**Status:** Done

## Goal

Make serving an explicit action separate from scene description: add
`start_server()` (serve only), `stop_server()`, and `open_browser()` on
`Visualizer` (and per-scene on `VizSceneHandle`).  `host`/`port` stay on the
constructor as deprecated kwargs for backward compatibility.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] Add `Visualizer.start_server(host="localhost", port=None)`; `port=None`
      auto-picks a free port. Extract the shared boot logic into a private
      `_ensure_server_running()`.
- [x] Add `Visualizer.stop_server(timeout=5.0)` from the body of `stop()`.
- [x] Add `Visualizer.open_browser()` + `_open_scene_browser(name)` (moves the
      token/reconnect logic out of `start()`).
- [x] Add `VizSceneHandle.open_browser()` → `viz._open_scene_browser(name)`.
- [x] Keep `host`/`port` as deprecated kwargs on `Visualizer.__init__` (emit
      `DeprecationWarning`); `start_server(host, port)` is the new way.
- [x] Add deprecated aliases `start()` → `start_server()` + `open_browser()`
      (preserving old behavior) and `stop()` → `stop_server()`, with
      `warnings.warn(..., DeprecationWarning)`.
- [x] Update `animate()` to call `start_server()`/`open_browser()`/`stop_server()`
      internally (no deprecation warnings).

## Unit tests

- [x] `py/tests/viz/test_scene_session.py`:
  - [x] `start_server()` with `port=None` selects a free port.
  - [x] `start()` emits a `DeprecationWarning` and calls `start_server`.
  - [x] `stop()` emits a `DeprecationWarning` and calls `stop_server`.

## Verification

- [x] `uv run pytest py/tests/viz/` passes (423 tests).
- [x] `start()`/`stop()` aliases preserve old behavior (verified via deprecation
      routing tests; `demo_animated_export.py` uses `viz.start()` unchanged).
