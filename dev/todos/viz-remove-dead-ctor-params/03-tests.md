# Phase 3 — Tests

## Goal

Update the pytest suite for the removed constructor params and the new
`VisualizerApp.run(port, host)`.

## Files

- Edit: `py/tests/viz/test_server_lifecycle.py`
- Edit: `py/tests/viz/test_scene_session.py`

## Steps

- [x] **3.1 — Remove tests for the removed constructor params**
  - Delete `test_show_falls_back_to_constructor_port` and
    `test_show_honours_open_browser_false` from `test_server_lifecycle.py`.
  - Delete `test_custom_port_and_host` from `test_scene_session.py`.
- [x] **3.2 — Add replacement coverage**
  - Add `test_constructor_rejects_port_host_open_browser` (asserts
    `Visualizer(port=…)`, `Visualizer(host=…)`, `Visualizer(open_browser=…)`
    each raise `TypeError`).
  - Add `test_visualizerapp_run_forwards_port_host` (monkeypatch
    `app.viz.show`/`stop_server`, set `app._stop_requested`, call
    `app.run(wait_for_browser=False, port=9000, host="127.0.0.1")`, assert
    `show` received `port=9000`, `host="127.0.0.1"`).

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- `test_scene_session.py` still has `start_server(port=...)` tests — those stay
  (the params still exist on `start_server`).
