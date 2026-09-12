# Phase 3 — Tests

## Goal

Cover the new resolution paths (server modes, visualizer defaults, terminal ask
degradation) with focused unit/integration tests.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/tests/viz/test_server_lifecycle.py`

## Steps

- [x] **3.1 — `find_port_occupants` detects a local listener**
  - Bind + listen a socket in-process, assert `find_port_occupants(port)`
    returns a `PortOccupant` with `pid == os.getpid()` and a `name`.
- [x] **3.2 — Server mode tests**
  - `CANCEL` (default): busy port → `PortInUseError`.
  - `AUTO`: busy port → server binds a different port (`server.port != original`)
    and accepts a connection.
  - `KILL`: spawn a subprocess that binds the port, mode `KILL` → subprocess is
    terminated and the server binds.
  - `ASK` without an ask fn → `PortInUseError` (fallback to cancel).
  - `ASK` with a monkeypatched ask fn → the returned action is honoured
    (e.g. return `AUTO` → new port).
- [x] **3.3 — Visualizer default resolution**
  - `_jupyter=True`, `port_conflict_mode=None` → `_port_conflict_mode == AUTO`.
  - `_jupyter=False`, `port_conflict_mode=None` → `_port_conflict_mode == ASK`.
  - Explicit `port_conflict_mode=CANCEL` is preserved regardless of `_jupyter`.
- [x] **3.4 — Visualizer terminal ask + port sync**
  - Monkeypatch `builtins.input` to return `"a"`; start on a busy port with
    `port_conflict_mode=ASK`; assert the server ends up on a free port and
    `viz._port == viz._server.port`.
  - Monkeypatch `sys.stdin` to a non-tty (or `input` to raise `EOFError`);
    assert it falls back to `PortInUseError`/`SystemExit`.

## Validation

`uv run pytest py/tests/viz/test_server_lifecycle.py -q`

## Notes

- Reuse the existing busy-port helper pattern
  (`socket` bind/listen on `127.0.0.1`, port `0`) from
  `test_start_server_busy_port_reports_clear_message`.
- Use `subprocess.Popen([sys.executable, "-c", ...])` for the `KILL` case and
  `p.wait()` to assert termination.
