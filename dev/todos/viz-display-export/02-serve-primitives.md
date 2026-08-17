# Phase 2 — Serving primitives (`start_server` / `stop_server` / `open_browser`)

**Status:** Planned

## Goal

Make serving an explicit action separate from scene description: move `host`
and `port` out of `Visualizer.__init__` and into a `start_server()` call, add
`stop_server()`, and add `open_browser()` on `Visualizer` (and per-scene on
`VizSceneHandle`) for opening/reconnecting a browser tab.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/_app.py` (constructor passthrough)

## Steps

- [ ] Add `Visualizer.start_server(host="localhost", port=None)`; `port=None`
      auto-picks a free port. Extract the shared boot logic from `start()`
      (~line 884) and `run()` (~line 1259) into a private `_ensure_server()`.
- [ ] Add `Visualizer.stop_server(timeout=5.0)` from the body of `stop()`.
- [ ] Add `Visualizer.open_browser()` delegating to
      `VizServer.open_browser(path)`.
- [ ] Add `VizSceneHandle.open_browser()` → `viz.open_browser(f"/{name}")`.
- [ ] Remove `host`/`port` from `Visualizer.__init__`; store `_host`/`_port`
      lazily in `start_server`. Update `VisualizerApp.__init__` passthrough.
- [ ] Add deprecated aliases `start()` → `start_server()` and `stop()` →
      `stop_server()` with `warnings.warn(..., DeprecationWarning)`.

## Unit tests

- [ ] `py/tests/viz/test_scene_session.py`:
  - [ ] `start_server()` with `port=None` selects a free port.
  - [ ] `start()` emits a `DeprecationWarning` and calls `start_server`.
  - [ ] `stop()` emits a `DeprecationWarning` and calls `stop_server`.

## Verification

- [ ] `uv run pytest py/tests/viz/test_scene_session.py` passes.
- [ ] `uv run python py/examples/viz/demo_animated_export.py` still works with
      `viz.start()` (alias).
