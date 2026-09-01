# Phase 2 — `VisualizerApp` constructor cleanup + `run(port, host)`

## Goal

Remove `port`/`host`/`open_browser` from `VisualizerApp.__init__` and add
`port`/`host` to `run()`.

## Files

- Edit: `py/pytanga/viz/_app.py`

## Steps

- [x] **2.1 — Drop `port`/`host`/`open_browser` from `__init__`**
  - Remove the three params from the signature and from the `Visualizer(...)`
    call. Keep `reuse_existing`, `title`, `annotation`, `background_color`,
    `camera`, `space_dim`, `enable_server_stop_key`, `add_default_axes`,
    `add_default_grid`.
- [x] **2.2 — Add `port`/`host` to `run()`**
  - Add `port: int | None = None, host: str | None = None` to `run(...)` and
    forward to `self.viz.show(..., port=port, host=host)`.
  - Update the `run()` docstring to mention the new params.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/_app.py`

## Notes

- `run()` already passes `timeout` to `show()`; add `port`/`host` alongside it.
