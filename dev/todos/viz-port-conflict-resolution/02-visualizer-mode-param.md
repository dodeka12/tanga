# Phase 2 — `Visualizer` mode parameter + terminal ask

## Goal

Expose `port_conflict_mode` on the `Visualizer`, resolve the default, provide
the terminal ask function, inject both into the `VizServer`, sync the resolved
port, and re-export the enum.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/__init__.py`

## Steps

- [x] **2.1 — Import the contract**
  - In `visualizer.py`, import `PortConflictMode`, `PortConflictAsk`, and
    `PortOccupant` from `.server` (a top-level import is safe: `server.py` does
    not import `visualizer.py`, so there is no cycle).
- [x] **2.2 — Constructor parameter + default resolution**
  - Add `port_conflict_mode: PortConflictMode | None = None` to
    `Visualizer.__init__` (after `enable_server_stop_key`).
  - Set `self._port_conflict_mode = port_conflict_mode or
    (PortConflictMode.AUTO if self._jupyter else PortConflictMode.ASK)`.
  - Set `self._port_conflict_ask: PortConflictAsk | None = None`.
- [x] **2.3 — Terminal ask function**
  - Add `def _ask_port_conflict(self, port, occupants) -> PortConflictMode`:
    print each occupant (pid/name/cmdline) via `rich` (fallback to `print`),
    then loop `input()` over `k`/`a`/`c` (kill/auto/cancel).  Return `CANCEL`
    when `sys.stdin` is not a tty or on `EOFError`/`StdinNotImplementedError`/
    `KeyboardInterrupt`.
- [x] **2.4 — `start_server(ask=...)` override**
  - Add `ask: PortConflictAsk | None = None` to `start_server`; store it in
    `self._port_conflict_ask` before booting so `_ensure_server_running` uses it.
- [x] **2.5 — Inject into `VizServer` + port sync**
  - In `_ensure_server_running`, construct
    `VizServer(host=..., port=..., port_conflict_mode=self._port_conflict_mode,
    port_conflict_ask=self._port_conflict_ask or self._ask_port_conflict)`.
  - After the boot loop completes (before `_print_startup_urls()`), set
    `self._port = self._server.port` so an `AUTO`-picked port is reflected in
    the URL / `self._port`.
- [x] **2.6 — Re-export from `pytanga.viz`**
  - In `__init__.py`, `from .server import PortConflictMode` (and
    `PortOccupant`) and add them to `__all__`.

## Validation

`uv run pytest py/tests/viz/test_server_lifecycle.py py/tests/viz/test_visualizer_singleton.py -q`

## Notes

- `_ask_port_conflict` is only invoked for `ASK` mode; the default for Jupyter
  (`AUTO`) never calls it, so notebooks stay non-interactive by default.
- The non-tty guard preserves today's behaviour for non-interactive scripts
  (busy port → `PortInUseError` → `SystemExit`, no hang).
