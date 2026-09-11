# Phase 3 — `Visualizer.show()` / `run()` dead parameters

## Goal

Make `Visualizer(port=…, host=…, open_browser=…)` take effect through the modern
`show()` flow, and confirm the deprecated `run()` shim now forwards them (see
`dev/notes/pytanga-dead-params.md` items #1–#3).

## Files

- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **3.1 — `show()` honours the constructor `host`/`port`**
  - In `show()`, replace
    `self.start_server(host=host or "localhost", port=port)` with
    `self.start_server(host=host or self._host, port=port if port is not None else self._port)`.
  - This makes `Visualizer(port=…, host=…)` work through `show()` (and therefore
    through `run()` and `VisualizerApp.run()`), fixing note items #1 and #3.
- [x] **3.2 — `show()` honours `open_browser=False`**
  - In `show()`, after the Jupyter branch, if `self._open_browser is False`,
    return `True` without calling `open_browser()` (server is running, no tab
    opened). Otherwise keep
    `return self.open_browser(wait_for_browser=wait_for_browser)`.
  - Fixes note item #2.
- [x] **3.3 — Verify `run()` forwards `host`/`port`/`open_browser` implicitly**
  - `run()` already calls `self.show(...)`; after 3.1/3.2 the constructor values
    flow through automatically. No signature change; add a short comment if
    helpful.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- `show()` currently passes `host or "localhost"`; using `host or self._host`
  keeps the `localhost` default while letting an explicit constructor host win
  when `show(host=None)`.
