# Phase 1 — `VizServer` port-conflict resolution

## Goal

Add the port-conflict contract and helpers to `server.py` and make `VizServer`
resolve a busy port via `PortConflictMode` instead of unconditionally raising
`PortInUseError`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/server.py`

## Steps

- [x] **1.1 — Add the contract types + helpers**
  - Import `psutil` and `from enum import Enum` at the top of `server.py`.
  - Define `class PortConflictMode(str, Enum)` with `CANCEL = "cancel"`,
    `AUTO = "auto"`, `KILL = "kill"`, `ASK = "ask"`.
  - Define `@dataclass(frozen=True) class PortOccupant` with `pid: int`,
    `name: str`, `cmdline: tuple[str, ...] | None = None`.
  - Define `PortConflictAsk = Callable[[int, list[PortOccupant]],
    PortConflictMode]`.
- [x] **1.2 — `find_port_occupants(port)`**
  - Iterate `psutil.net_connections(kind="tcp")`, keep `status == "LISTEN"`
    and `laddr.port == port`; for each `pid`, build a `PortOccupant` via
    `psutil.Process(pid)` (`name()`, `cmdline()`), tolerating
    `NoSuchProcess`/`AccessDenied` (fall back to `name="?"`, `cmdline=None`).
  - Deduplicate by `pid` (a listener can appear on IPv4 + IPv6) and return the
    list.
- [x] **1.3 — `_find_free_port(host)` + `_terminate_port_occupants(occupants)`**
  - `_find_free_port`: bind a socket to `127.0.0.1` for `localhost`/`127.0.0.1`,
    else `host`, on port `0`, return the assigned port (mirror of
    `visualizer.py:_find_free_port`).
  - `_terminate_port_occupants`: for each `pid`, `psutil.Process(pid).terminate()`,
    `wait(timeout=2)`, then `.kill()` if still alive; swallow
    `NoSuchProcess`/`AccessDenied`.
- [x] **1.4 — `default_port_conflict_ask`**
  - `def default_port_conflict_ask(port, occupants) -> PortConflictMode:`
    returning `PortConflictMode.CANCEL` (documented as "no interaction
    available").
- [x] **1.5 — `VizServer.__init__` params + `port` property**
  - Add `port_conflict_mode: PortConflictMode = PortConflictMode.CANCEL` and
    `port_conflict_ask: PortConflictAsk | None = None`; store
    `self._port_conflict_mode` and `self._port_conflict_ask =
    port_conflict_ask or default_port_conflict_ask`.
  - Add `@property def port(self) -> int: return self._port`.
- [x] **1.6 — Extract the bind into `_bind_sites` and wrap in a retry loop**
  - Move the current bind block out of `start()` (the `bind_hosts`/`TCPSite`
    loop + "Server listening" log) into `async def _bind_sites(self)` unchanged
    (still raising `OSError` when the primary bind fails).
  - Add `async def _bind_with_resolution(self)` implementing the `while True`
    loop from the README contract; call it from `start()` in place of the old
    block.  Keep the `PortInUseError` (existing message text) for the
    `CANCEL`/fallback case.

## Validation

`uv run pytest py/tests/viz/test_server_lifecycle.py -q`

## Notes

- `_is_port_in_use_error` (already in `server.py`) stays the gate; the new
  logic only runs after it returns `True`.
- Keep the `psutil` import at module top (it is now a declared dependency in
  `pyproject.toml`).
- The `PortInUseError` message text is preserved so the existing
  `test_start_server_busy_port_reports_clear_message` assertion
  (`"already in use"`) still passes.
