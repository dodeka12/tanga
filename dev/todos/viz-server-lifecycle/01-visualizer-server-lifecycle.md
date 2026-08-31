# Phase 1 — `Visualizer` server lifecycle fix

## Goal

Make `Visualizer` start/stop restore global state, surface the real boot error,
and report a busy port as a clean message (no traceback).

## Files

- Edit: `py/pytanga/viz/server.py` (add `PortInUseError`)
- Edit: `py/pytanga/viz/visualizer.py`

## Steps

- [x] **1.1 — Add `PortInUseError` and raise it from `VizServer.start()`**
  - In `server.py`, define `class PortInUseError(RuntimeError): ...` near the
    other module-level names.
  - In `VizServer.start()`'s `except OSError` branch (`server.py:277-287`),
    replace `raise RuntimeError(...)` with `raise PortInUseError(...)`, keeping
    the existing message text exactly.
- [x] **1.2 — Stop clobbering the caller's event loop**
  - Remove `asyncio.set_event_loop(self._loop)` in `_ensure_server_running`
    (`visualizer.py:1481`).
- [x] **1.3 — Surface the real boot error and clean up a failed boot**
  - Keep a reference to the `_boot` task (`boot_task = self._loop.create_task(_boot())`).
  - On `_boot_done.wait(timeout=5.0)` returning `False`: if `boot_task.done()`
    and `boot_task.exception()` is not `None`, re-raise that exception; else
    raise the generic `RuntimeError("Server failed to start within 5s")`.
  - Before re-raising, tear down the half-started server: best-effort
    `await self._server.stop()` on the loop, `self._loop.call_soon_threadsafe(self._loop.stop)`,
    `self._thread.join(timeout=3.0)`, then null `self._server`/`self._loop`/`self._thread`.
- [x] **1.4 — Save and restore signal handlers**
  - Add `self._saved_signal_handlers: dict[int, Any] | None = None` in `__init__`.
  - In `_ensure_server_running`, before `signal.signal(SIGINT/SIGTERM, _on_sigint)`,
    store `signal.getsignal(signal.SIGINT)` and `signal.getsignal(signal.SIGTERM)`.
  - Add a private `_restore_signal_handlers()` that restores each saved handler
    via `signal.signal` and resets the field to `None` (idempotent).
- [x] **1.5 — Restore handlers in `stop_server()` (idempotent)**
  - Call `_restore_signal_handlers()` at the top of `stop_server()`, before the
    `if self._server is None: return` guard, so restoration happens even on a
    failed or repeated stop.
- [x] **1.6 — Report a busy port without a traceback**
  - In `start_server()`, wrap the `self._ensure_server_running()` call in
    `try/except PortInUseError`: print a single clear line to stderr (the
    exception's message) and `raise SystemExit(1)`. Let all other exceptions
    propagate unchanged.
  - Add `from .server import PortInUseError` (alongside the existing
    `from .server import VizServer` import in `_ensure_server_running`).

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- `signal` is already imported at the top of `visualizer.py`; `sys` is **not** —
  use `raise SystemExit(1)` so no new import is needed.
- `PortInUseError` stays a `RuntimeError` subclass so existing
  `except RuntimeError` handling keeps working.
- `SystemExit` is not a `Exception` subclass, so Python prints no traceback —
  this is what produces the "clear message only" behaviour.
