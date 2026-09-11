# Phase 4 — `VisualizerApp` dead parameters

## Goal

Fix `VisualizerApp.run(timeout=…)` (currently unused) and forward
`add_default_axes`/`add_default_grid` (see `dev/notes/pytanga-dead-params.md`
items #4–#6).

## Files

- Edit: `py/pytanga/viz/_app.py`
- Edit: `py/pytanga/viz/visualizer.py` (thread `timeout` through `show()`)

## Steps

- [x] **4.1 — Forward `add_default_axes` / `add_default_grid`**
  - Add `add_default_axes: bool = True` and `add_default_grid: bool = True` to
    `VisualizerApp.__init__` and pass them through to `Visualizer(...)`.
  - Fixes note item #6.
- [x] **4.2 — Thread `timeout` into `Visualizer.show()`**
  - Add `timeout: float | None = None` to `Visualizer.show()` and forward it to
    `open_browser(timeout=timeout)` in the browser branch.
  - Add `timeout: float | None = None` to `open_browser()` and
    `_open_browser_url()`; use `timeout` in the `wait_for_browser(timeout=…)`
    calls, replacing the hardcoded `120.0` / `30.0` (fall back to the current
    defaults when `None`).
- [x] **4.3 — Use `timeout` in `VisualizerApp.run()`**
  - Change `self.viz.show(wait_for_browser=wait_for_browser)` to
    `self.viz.show(wait_for_browser=wait_for_browser, timeout=timeout)`.
  - Fixes note item #4. Note item #5 (`port`/`host`/`open_browser`) is already
    resolved by Phase 3, since `_app.py` forwards those to `Visualizer(...)`.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- `VisualizerApp.run()`'s `timeout` only applies when `wait_for_browser=True`
  (matches its current docstring).
- The `open_browser()`/`_open_browser_url()` timeout plumbing keeps existing
  behaviour when `timeout=None`.
