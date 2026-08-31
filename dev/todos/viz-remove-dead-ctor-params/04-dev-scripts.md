# Phase 4 — `dev/src` smoke scripts

## Goal

Update the dev-only smoke scripts that use the removed constructor params.

## Files

- Edit: `dev/src/test_viz_smoke.py`
- Edit: `dev/src/test_viz_multi_scene.py`

## Steps

- [x] **4.1 — `test_viz_smoke.py`**
  - Replace `Visualizer(open_browser=False)` with `Visualizer()`; where the
    script then called `viz.start()` to serve without opening a browser, use
    `viz.start_server()` instead.
  - Replace `Visualizer(open_browser=False, port=18766, host="127.0.0.1")` with
    `Visualizer()` + `viz.start_server(host="127.0.0.1", port=18766)`.
- [x] **4.2 — `test_viz_multi_scene.py`**
  - Replace `Visualizer(port=8765, title=...)` +
    `viz.start(wait_for_browser=False)` with `Visualizer(title=...)` +
    `viz.start_server(port=8765)`.

## Validation

`uv run ruff check dev/src/test_viz_smoke.py dev/src/test_viz_multi_scene.py`

## Notes

- `test_viz_smoke.py` line 45 already has a pre-existing syntax error
  (`color="#ff4444"style=…`); fix it only if it blocks running, otherwise leave.
- These scripts also use the deprecated `start()`/`stop()`; migrate to
  `start_server()`/`stop_server()` only where needed for the no-browser intent.
