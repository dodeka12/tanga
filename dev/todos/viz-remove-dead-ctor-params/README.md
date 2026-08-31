# Viz Remove Dead Constructor Params — Overview

**Created:** 2026-08-31 | **Status:** Done | **Branch:** `fix/scene-alert`

## Goal

Remove the deprecated-but-ignored `port` / `host` / `open_browser` constructor
parameters from `Visualizer` and `VisualizerApp`, moving the runtime port/host
concern to the call sites (`start_server()`, `show()`, and
`VisualizerApp.run()`), and update tests, docs, changelog, and dev smoke
scripts accordingly.

## Background

`dev/notes/pytanga-dead-params.md` documents that `Visualizer(port=…, host=…)`
and `Visualizer(open_browser=…)` are accepted but have no effect through the
modern `show()`/`run()` flow (they were deprecated in favour of
`start_server(host=…, port=…)`).  A previous change wired these params into
`show()` instead of removing them; this plan reverts that and completes the
deprecation by removing the params.  `VisualizerApp` forwards the same params
and is removed in lockstep.

## Architecture (short)

- `Visualizer` keeps `self._host = "localhost"` / `self._port = DEFAULT_PORT`
  as internal state (still used by `start_server`, `_print_startup_urls`, and
  the `url` property), but no longer accepts them in the constructor.
- `self._open_browser = not self._jupyter` stays as internal state (the
  deprecated `start()` still reads it); it is no longer user-settable.
- `show(host=…, port=…)` / `start_server(host=…, port=…)` remain the entry
  points for host/port.
- `VisualizerApp.run()` gains `port`/`host` and forwards them to
  `viz.show(...)`.

## Decisions (confirmed)

- **Remove** `port`, `host`, `open_browser` from `Visualizer.__init__` (and
  `VisualizerApp.__init__`). This is a breaking change (already deprecated).
- **`VisualizerApp.run()` gains `port`/`host`**, forwarded to `show()`.
  `open_browser` is not re-added anywhere (use `start_server()` vs `show()`).
- **Revert** the previous `show()` forwarding (`host or self._host` /
  `port if ... else self._port` and the `open_browser is False` early return)
  back to `start_server(host=host or "localhost", port=port)`.
- **Keep `self._open_browser = not self._jupyter`** as internal state for the
  deprecated `start()` shim.
- **`SdfVisualizer` is untouched** — its constructor `port`/`host`/`open_browser`
  are live (its `start_server()` reads `self._port`/`self._host`).
- **Update the `VizServer.start()` error text** from `Visualizer(port=...)` to
  `start_server(port=...)`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-visualizer-ctor-cleanup.md](./01-visualizer-ctor-cleanup.md) | Remove ctor params from `Visualizer`, revert `show()`, fix server message |
| 2 | [02-visualizerapp-ctor-cleanup.md](./02-visualizerapp-ctor-cleanup.md) | Remove ctor params from `VisualizerApp`, add `run(port, host)` |
| 3 | [03-tests.md](./03-tests.md) | Update pytest suite |
| 4 | [04-dev-scripts.md](./04-dev-scripts.md) | Update `dev/src` smoke scripts |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs + changelog |

## Testing as you go

- `uv run pytest py/tests/viz -q`
- `uv run ruff check py/pytanga/viz/ py/tests/viz/`
- `uv run mkdocs build --strict` (docs/changelog phase)

## Non-goals

- No change to `SdfVisualizer` (its constructor params are live).
- No change to the deprecated `Visualizer.start()` / `run()` shims beyond the
  `_open_browser` internal state staying intact.
- No new host/port behaviour — the params are removed, not re-implemented.
