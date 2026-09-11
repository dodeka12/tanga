# Idempotent `display()`/`show()` in Jupyter + Scene Context Managers

**Created:** 2026-08-22 | **Status:** Implemented

## Goal

Make the Jupyter workflow idempotent: re-running the same notebook cell (or
calling `display()`/`show()` again) must **not** open a second viewer. A
repeated call should just push the latest scene state (`flush()`) into the
already-open inline viewer. In addition, make `Visualizer` and `VizSceneHandle`
usable as context managers so a cell can be written as:

```python
with viz:
    viz.add(Point(1, 2, 3))
```

which clears the scene at the start and shows it at the end.

## Already landed (committed — for context)

- `4fdb111` — `display()` prints a hint (and skips the iframe) in Jupyter when
  the server is not running.
- `c750840` — `show()` gained a tri-state `jupyter` option and delegates to
  `display()` in notebooks; `ruff` pinned to `0.14.0`.

This plan only covers what is **not** yet implemented.

## Background (current behaviour)

- `Visualizer.display()` (`py/pytanga/viz/visualizer.py`) and
  `VizSceneHandle.display()` (`py/pytanga/viz/_scene_handle.py`) build a new
  `IPython.display.IFrame` and call `IPython.display.display(...)` on **every**
  call. Each call = a new `<iframe>` element = a new page load = a new WebSocket
  connection = a new `BrowserSession` on the server. From the server's point of
  view it is indistinguishable from opening a new browser tab.
- `Visualizer.list_browsers()` already returns `[{id, scene, remote_addr,
  viewer_name}]` per connected session (`server.get_browser_sessions()`); the
  `scene` field is populated in the `ready` WebSocket handler
  (`current_session.scene = scene_name`).
- `show(jupyter=...)` already delegates to `display()` in Jupyter, so any
  idempotency added to `display()` is inherited automatically.
- `clear()` exists on `Visualizer` (clears the main scene) and `VizSceneHandle`
  (clears that scene); `flush()` pushes dirty state (including removals) to all
  connected browsers.
- Neither `Visualizer` nor `VizSceneHandle` implements `__enter__`/`__exit__`.
- The `viewer_name` feature exists for targeted `navigate_to("viewer:…")`, but
  we deliberately **do not** use it for idempotency (see Design decisions).

## Design decisions

1. **Identity = the viewer.** Idempotency is keyed on a viewer key, not on the
   scene, so two cells can show the same scene independently. The key is
   resolved as: an explicit `viewer_name`, otherwise the current notebook cell
   id (via the IPython `pre_run_cell` event), otherwise the scene name.
2. **The viewer key doubles as the IPython `display_id`.** The iframe is
   emitted with `display(iframe, display_id=f"tanga-{key}")` so re-running the
   same cell **replaces** the same output instead of stacking new ones.
3. **Per-execution scoping.** The "already shown" state is scoped to the
   current notebook cell execution, tracked via an execution token that
   increments on every `pre_run_cell` event. A fresh execution re-emits the
   iframe (Jupyter destroys the previous one when a cell is re-run); repeated
   calls within one execution only flush.
4. **`display()`/`show()` always `flush()`.** If the viewer is already shown
   this execution, the call becomes *just* a flush (no new iframe). Otherwise
   it emits the iframe and then flushes.
5. **Connect race guard.** A pending flag (set when the iframe is emitted)
   prevents two back-to-back `display()` calls within one execution from
   emitting twice. It is reset at the start of each cell execution.
6. **Context managers reset to defaults.** `__enter__` clears the target scene
   and re-adds the default axes/grid (via `_reset_scene`), then returns the
   object; `__exit__` calls `show()` (always, even on exception) and returns
   `None` so exceptions propagate. No dedicated `show_scene()` function.

## Files

- Add: `py/pytanga/viz/_notebook_cell.py` (`current_cell_id()` via IPython
  `pre_run_cell`)
- Modify: `py/pytanga/viz/visualizer.py` (viewer-key helpers, idempotent
  `display()`, pending state, `viewer_name` on `show()`, `__enter__`/`__exit__`)
- Modify: `py/pytanga/viz/_scene_handle.py` (idempotent `display()`,
  `viewer_name` on `show()`, `__enter__`/`__exit__`)
- Tests: `py/tests/viz/test_display.py`, `py/tests/viz/test_scene_session.py`
- Docs: `docs/py/viz/jupyter.md`, `docs/py/viz/visualizer.md`
- Changelog: append to `docs/changelog/2026-08-22_fix-viz.md`

## Steps

### Step 1 — Cell-id / execution-token helper (`_notebook_cell.py`)

- [x] Add `current_cell_id()` and `execution_token()` backed by an IPython
      `pre_run_cell` listener (registered at import time).

### Step 2 — Viewer-key helpers + idempotent `display()` (visualizer.py + _scene_handle.py)

- [x] Add `_resolve_viewer_key()` (viewer_name → cell id → scene name).
- [x] Add `_display_pending: set[str]` and `_display_execution` to `__init__`.
- [x] Add `_display_live()`: reset pending when `execution_token()` changes,
      then emit-or-flush; `display()` delegates to it with the resolved key.
- [x] Add `viewer_name` to `display()` and `show()` (forwarded through).
- [x] Leave the non-Jupyter branch of `display()` (raw HTML string) unchanged.

### Step 3 — Context managers reset to defaults

- [x] Add `Visualizer._reset_scene(scene_name)` (clear + re-add default axes/grid).
- [x] `Visualizer.__enter__` → `_reset_scene("")`; `__exit__` → `show()`.
- [x] `VizSceneHandle.__enter__` → `self._viz._reset_scene(self._name)`;
      `__exit__` → `show()`.

### Step 4 — Tests

- [x] `display()` called twice → second call emits no new iframe and flushes.
- [x] New execution token → re-emits.
- [x] `display()` with server down → prints hint, no emit.
- [x] caller `viewer_name` and scene-handle `display()` use the right key/display_id.
- [x] `with viz:` / `with viz.scene("name"):` reset the scene and call `show()`.
- [x] `__exit__` propagates exceptions; `_reset_scene` preserves default axes/grid.

### Step 5 — Docs & changelog

- [x] Update `docs/py/viz/jupyter.md` and `docs/py/viz/visualizer.md`.
- [x] Append changelog entries.

## Notes / edge cases

- **"Each cell output = a separate scene using the Jupyter id"**: Jupyter has no
  clean public API to read a stable per-cell id from inside the running cell;
  the only stable id it hands you is the `display_id` you pass to `display()`.
  Therefore the scene key defaults to the scene name (main `""` → `"main"`,
  `viz.scene("name")` → `"name"`). Multiple independent viewers in one notebook
  are achieved by scoping each cell with `with viz.scene("a"):`,
  `with viz.scene("b"):`, etc.
- The pending flag is only a narrow guard for the connect window; the
  scene-keyed `list_browsers()` check is the authoritative "already shown" test.
- `list_browsers()` snapshots sessions mutated on the server's event loop;
  reading it from the notebook thread is acceptable but should be noted as a
  mild thread-safety caveat (a lock can be added if it proves necessary).
- `flush()` must push removals (from `clear()`) as well as additions so the
  context manager's clear-on-enter + show-on-exit produces a correct full update.


