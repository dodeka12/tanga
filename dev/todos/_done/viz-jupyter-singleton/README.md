# Viz Jupyter-Scoped Singleton & Re-run Reset — Overview

**Created:** 2026-09-10 | **Status:** Done | **Branch:** `feat/jupyter-visualizer`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Make `Visualizer()` a **Jupyter-scoped** singleton with **re-run reset**
semantics, so re-running a notebook cell that re-creates the viewer no longer
tries to bind the already-used port (today this raises `PortInUseError` →
`SystemExit`) and instead reuses the one server + scene host.  On a re-run the
constructor clears the default scene and re-adds axes/grid per the constructor
flags; a named scene created via `scene(name)` is created on first call and
cleared on a re-run of the same cell.  Non-Jupyter code (scripts,
`VisualizerApp`, pytest) is unchanged.

## Architecture (short)

- The server is a stateless HTTP/WebSocket relay wired to **one** `Visualizer`'s
  scenes via callbacks (`server.py: start(...)`); scene content lives in the
  `Visualizer`'s `LayoutHost.scenes` (`scene.py`).  "One server" therefore
  means "one `Visualizer` per process" in a notebook.
- The singleton is a construction-time guard only: `__new__` returns a cached
  instance when `_is_jupyter()` is `True`; `__init__` is guarded by
  `_initialized`.  The ownership hierarchy (`Visualizer` → `Transport` →
  `LayoutHost` → `Scene`, per `docs/dev/architecture/viz-architecture.md`) is
  unchanged.
- Re-run reset reuses the existing `_reset_scene()` helper (already used by the
  `with viz:` context manager).
- Scene re-run clear keys each named scene by `(current_cell_id(),
  execution_token())` from `_notebook_cell.py` (both already imported in
  `visualizer.py`).

## Decisions (confirmed)

- **Scope = Jupyter only.**  The singleton (and re-run semantics) apply only
  when `_is_jupyter()` is `True`.  Outside notebooks, `Visualizer()` keeps
  constructing independent instances — no change to scripts, `VisualizerApp`,
  or the ~313 independent test constructions.
- **Singleton mechanism.**  `Visualizer.__new__` caches the instance when
  `_is_jupyter()` is `True`; `__init__` is guarded by `_initialized`.
- **Constructor re-run reset.**  On a subsequent `Visualizer(...)` call, update
  `add_default_axes` / `add_default_grid` from the **current** call's args, then
  `self._reset_scene("")` (clear main scene + re-add axes/grid).  All other
  constructor params (`camera`, `title`, `space_dim`, `background_color`,
  `annotation`, `reuse_existing`, `enable_server_stop_key`) remain
  **first-call-wins** (not re-applied).
- **Scene re-run clear.**  `scene(name)` clears an existing scene only when the
  **same** notebook cell is re-run (stored `(cell_id, token)` has a matching
  `cell_id` and a different `token`).  A different cell, or a second call in the
  same execution, returns the handle without clearing.  Outside notebooks
  (`cell_id is None`, token constant `0`) behaviour is unchanged
  (get-or-create).  `scene("")` returns the main-scene handle without clearing
  (the main scene is managed by the constructor reset).
- **`Visualizer.reset()`.**  A classmethod that stops the server (if running)
  and clears the cached instance, so a genuinely fresh `Visualizer()` can be
  obtained (tests/tooling).
- **No architecture change.**  This does not alter the documented ownership
  hierarchy, data flows, or wire protocol; no `docs/dev/architecture/` edit is
  required.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-visualizer-singleton.md](./01-visualizer-singleton.md) | Jupyter-scoped `__new__` singleton + `_initialized` guard + `reset()` |
| 2 | [02-constructor-rerun-reset.md](./02-constructor-rerun-reset.md) | Constructor re-run clears the default scene and re-adds axes/grid |
| 3 | [03-scene-rerun-clear.md](./03-scene-rerun-clear.md) | `scene(name)` clears on same-cell re-run |
| 4 | [04-tests.md](./04-tests.md) | Regression + integration tests across the viz suite |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Docs + changelog (per `changelog.md` / `pull-request.md`) |

## Testing as you go

- `uv run pytest py/tests/viz/test_visualizer_singleton.py -q` (phases 1–3)
- `uv run pytest py/tests/viz -q` (phase 4, full viz regression)
- `uv run ruff check py/pytanga/viz/ py/tests/viz/` (phase 4)
- `uv run mkdocs build --strict` (phase 5, docs only)

## Non-goals

- No change to `SdfVisualizer` (a separate class with its own server lifecycle).
- No change to `Visualizer.add_scene()` (still strict: raises if the name is
  taken).
- No process-wide singleton — scripts/apps/tests keep independent instances.
- No change to the `VizServer` wire protocol or the JS frontend.
- No cell-id-keyed *scene stack* / `new_scene(keep_previous=...)` / scene-copy
  machinery (out of scope from the earlier `dev/src/dev_jupyter_viz.ipynb`
  brainstorm).
