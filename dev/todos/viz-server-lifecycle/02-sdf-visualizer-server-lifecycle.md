# Phase 2 — `SdfVisualizer` server lifecycle fix

## Goal

Apply the same lifecycle fixes to `SdfVisualizer`
(`py/pytanga/viz/sdf/visualizer.py`), which duplicates the buggy pattern.

## Files

- Edit: `py/pytanga/viz/sdf/visualizer.py`

## Steps

- [x] **2.1 — Stop clobbering the caller's event loop**
  - Remove `asyncio.set_event_loop(self._loop)` (`sdf/visualizer.py:411`).
- [x] **2.2 — Surface the real boot error and clean up a failed boot**
  - Keep a reference to the `_boot` task; on `_boot_done.wait(timeout=5.0)`
    timeout re-raise `boot_task.exception()` when done (else the generic
    `"SDF server failed to start within 5s"`).
  - Tear down the half-started server before re-raising (stop the loop, join
    the thread, null `self._server`/`self._loop`/`self._thread`).
- [x] **2.3 — Save and restore signal handlers**
  - Add `self._saved_signal_handlers: dict[int, Any] | None = None` in the SDF
    `__init__`.
  - Before the `signal.signal(SIGINT/SIGTERM, ...)` calls (`sdf/visualizer.py:433-434`),
    save the prior handlers; add an idempotent `_restore_signal_handlers()`.
- [x] **2.4 — Restore handlers in `stop_server()` (idempotent)**
  - Call `_restore_signal_handlers()` at the top of `stop_server()`, before the
    `if self._server is None: return` guard.
- [x] **2.5 — Report a busy port without a traceback**
  - In `start_server()`, catch `PortInUseError` from the boot; print a clear
    message to stderr and `raise SystemExit(1)`. Other exceptions propagate.
  - Import `PortInUseError` from `pytanga.viz.server`.

## Validation

`uv run pytest py/tests/viz -q && uv run ruff check py/pytanga/viz/`

## Notes

- `sdf/visualizer.py` imports `signal` locally (inside `start_server`); either
  keep that local import or hoist it to the module top — the `getsignal` calls
  need it.
- `sys` is not imported; use `raise SystemExit(1)` as in Phase 1.
