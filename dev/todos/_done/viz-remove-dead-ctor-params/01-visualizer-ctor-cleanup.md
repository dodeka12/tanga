# Phase 1 — `Visualizer` constructor cleanup

## Goal

Remove `port`/`host`/`open_browser` from `Visualizer.__init__` and revert the
previous `show()` forwarding.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/server.py`

## Steps

- [x] **1.1 — Drop `port`/`host`/`open_browser` from `Visualizer.__init__`**
  - Remove the three params from the signature and the `DeprecationWarning`
    block.
  - Set `self._host = "localhost"`, `self._port = DEFAULT_PORT`, and
    `self._open_browser = not self._jupyter` (move the `_jupyter` detection
    before `_open_browser`; delete the old `self._open_browser = open_browser`
    line and the `if open_browser is None` block).
- [x] **1.2 — Revert `show()` to pass host/port through directly**
  - Change `start_server(host=host or self._host, port=port if port is not None
    else self._port)` back to `start_server(host=host or "localhost", port=port)`.
  - Remove the `if self._open_browser is False: return True` early-return.
- [x] **1.3 — Update the busy-port message**
  - In `server.py`, change `use Visualizer(port=...)` to
    `use start_server(port=...)` in the `PortInUseError` message.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- `self._host`/`self._port` remain instance state (used by `start_server`,
  `_print_startup_urls`, and the `url` property); only the constructor params go.
