# Viz Port-Conflict Resolution — Overview

**Created:** 2026-09-10 | **Status:** Done | **Branch:** `feat/jupyter-visualizer`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

When `VizServer` cannot bind its port because another process already holds it,
stop hard-failing with `PortInUseError` → `SystemExit`.  Instead resolve the
conflict according to a `PortConflictMode`: `CANCEL` (today's standard error),
`AUTO` (silently pick a free port), `KILL` (terminate the blocking process and
rebind), or `ASK` (delegate to an injected interaction function).  The
`Visualizer` gains a `port_conflict_mode` constructor parameter (default `AUTO`
under Jupyter, `ASK` elsewhere) and hands it down to the `VizServer`, which
applies it on the real `EADDRINUSE` path.

## Background

The motivating failure — a kernel "Restart" in VSCode leaving the old kernel
(and its port) alive — was traced to the server's signal handlers swallowing
`SIGTERM`.  That root cause is fixed separately (approach (a)): `SIGTERM` now
tears the server down and re-raises, so the process terminates and the OS
releases the port.  This plan covers the remaining convenience: resolving a
still-busy port by policy instead of hard-failing.

## Architecture (short)

- The conflict check stays where it already is: `VizServer.start()` binds via
  `web.TCPSite` and raises `OSError` on `EADDRINUSE` (`server.py:307-348`).  We
  key off that real error (not a pre-bind probe) so `SO_REUSEADDR`, IPv4/IPv6,
  and non-"in use" `OSError`s behave exactly as today.
- `psutil` (now a direct dependency, `pyproject.toml`) is used only on the
  conflict path to find the blocking process (`find_port_occupants`).
- A fixed contract (below) is the seam between `Visualizer` and `VizServer`: the
  `Visualizer` passes a `PortConflictMode` plus an optional ask function; the
  `VizServer` owns the retry loop and the kill/auto/cancel actions.
- No change to the documented ownership hierarchy, data flows, or wire protocol
  (`docs/dev/architecture/viz-architecture.md`); the server lifecycle is not
  documented there, so no architecture doc edit is required.

## Decisions (confirmed) — fixed contract

- **`PortConflictMode`** (`str, Enum`), values `"cancel" | "auto" | "kill" |
  "ask"`; defined in `server.py`, re-exported from `pytanga.viz`.
- **`PortOccupant`** frozen dataclass: `pid: int`, `name: str`,
  `cmdline: tuple[str, ...] | None`.
- **`PortConflictAsk = Callable[[int, list[PortOccupant]], PortConflictMode]`** —
  the interaction function, used only for `ASK`.  It returns one of
  `CANCEL`/`AUTO`/`KILL`; an `ASK` (or any other) return is treated as `CANCEL`.
- **`VizServer.__init__`** gains `port_conflict_mode: PortConflictMode = CANCEL`
  and `port_conflict_ask: PortConflictAsk | None = None` (default ask =
  `default_port_conflict_ask` → `CANCEL`).
- **Resolution** — on `EADDRINUSE`: `find_port_occupants(port)` →
  `action = mode if mode != ASK else ask(port, occupants)` →
  `KILL`: `_terminate_port_occupants` + retry same port · `AUTO`:
  `self._port = _find_free_port(host)` + retry · else: `raise PortInUseError`
  (existing message).
- **`VizServer.port`** read-only property so the `Visualizer` can read back an
  `AUTO`-picked port.
- **`Visualizer.__init__`** gains `port_conflict_mode: PortConflictMode | None =
  None`; `None` → `AUTO` if `self._jupyter` else `ASK`.
- **`Visualizer._ask_port_conflict(port, occupants)`** — terminal prompt (rich
  print + `input()` loop over `k`/`a`/`c`); returns `CANCEL` on
  `EOFError`/`StdinNotImplementedError`/non-tty stdin.
- **`Visualizer.start_server`** gains `ask: PortConflictAsk | None = None` to
  override the interaction function for `ASK`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-server-port-conflict-mode.md](./01-server-port-conflict-mode.md) | `PortConflictMode`/`PortOccupant`/`PortConflictAsk` + psutil helpers + `VizServer` resolution loop |
| 2 | [02-visualizer-mode-param.md](./02-visualizer-mode-param.md) | `Visualizer(port_conflict_mode=...)`, terminal ask, inject + port sync, re-export |
| 3 | [03-tests.md](./03-tests.md) | Unit + integration tests for server, visualizer, and defaults |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Changelog (per `changelog.md`) |

## Testing as you go

- `uv run pytest py/tests/viz/test_server_lifecycle.py -q` (phases 1–3)
- `uv run pytest py/tests/viz -q` (phase 3, full viz regression)
- `uv run ruff check py/pytanga/viz/ py/tests/viz/` (phase 3)
- `uv run mkdocs build --strict` (phase 4)

## Non-goals

- No pre-bind port probe (the bind attempt stays the source of truth).
- No `port_conflict_mode` parameter on `SdfVisualizer` (it keeps the default
  `CANCEL`; only the SIGTERM fix was applied there).
- No notebook-native prompt dependency (e.g. ipywidgets).
- No orphaned-kernel detection / `RECLAIM` mode — the SIGTERM fix (approach (a),
  already applied to both `Visualizer` and `SdfVisualizer`) resolved the
  kernel-restart root cause, so auto-reaping is deferred.
- No change to the `VizServer` wire protocol or the JS frontend.
