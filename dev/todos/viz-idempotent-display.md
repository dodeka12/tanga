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
3. **Liveness check reuses `viewer_name`.** A viewer is "already shown" when
   `list_browsers()` contains a session with `viewer_name == key` (empty list
   when the server is `None`).
4. **`display()`/`show()` always `flush()`.** If the scene is already shown the
   call becomes *just* a flush (no new iframe). Otherwise it emits the iframe
   and then flushes.
5. **Connect race guard.** A short-lived per-scene "pending" flag, set when the
   iframe is emitted and cleared on connect/disconnect, prevents two back-to-back
   `display()` calls (before the browser's `ready` lands) from emitting twice.
6. **Reconnect on close.** Clearing the active state on disconnect means a
   manually-closed output re-opens on the next `display()`/`show()`.
7. **Context managers.** `__enter__` clears the target scene and returns the
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

### Step 1 — Scene-keyed idempotency helper (visualizer.py)

- [ ] Add `Visualizer._has_connected_viewer(scene_name: str) -> bool`:
      return `any(s["scene"] == scene_name for s in self.list_browsers())`
      (and `False` when `self._server is None`).
- [ ] Add a per-scene pending guard, e.g. `self._display_pending: set[str]`
      (keyed by scene name), initialised in `__init__`.

### Step 2 — Idempotent `display()` (visualizer.py + _scene_handle.py)

- [ ] In the Jupyter branch of both `display()` methods, before emitting:
      1. Determine `scene = self._name` (`""` for the Visualizer).
      2. If `self._has_connected_viewer(scene)` **and** `scene` is not in the
         pending set → call `self.flush()` and return (no new iframe).
      3. Otherwise mark the scene pending, emit
         `display(iframe, display_id=f"tanga-{scene or 'main'}")`, then
         `self.flush()`.
- [ ] Leave the non-Jupyter branch of `display()` (returns the raw HTML string)
      unchanged.

### Step 3 — Clear pending state on connect/disconnect (visualizer.py)

- [ ] In `_on_client_connect` / `_on_client_disconnect`, clear the pending flag
      for the relevant scene(s). The exact wiring point is the `ready` handler
      where `current_session.scene` is set (`server.py`); if threading a
      per-scene callback through `VizServer.start()` is too invasive, fall back
      to clearing on any connect/disconnect as a short-window guard and rely on
      the scene-keyed `list_browsers()` check as the source of truth.

### Step 4 — `show()` parity (no code change expected)

- [ ] Confirm `show(jupyter=None/True)` in a notebook routes through `display()`
      and therefore inherits idempotency + flush. `show(jupyter=False)` keeps
      its existing browser-open behaviour.

### Step 5 — Context managers (visualizer.py + _scene_handle.py)

- [ ] `Visualizer.__enter__` → `self.clear()` (main scene) → return `self`.
- [ ] `Visualizer.__exit__(exc_type, exc_val, exc_tb)` → `self.show()` → return
      `None` (never suppress exceptions).
- [ ] `VizSceneHandle.__enter__` → `self.clear()` (this scene) → return `self`.
- [ ] `VizSceneHandle.__exit__(...)` → `self.show()` → return `None`.
- [ ] Note in docstrings that `__exit__` uses non-blocking `show()`, so scripts
      should follow the block with `wait()`.

### Step 6 — Tests

- [ ] `display()` called twice → second call emits no new iframe and calls
      `flush()` (monkeypatch `IPython.display.display` and `flush`).
- [ ] `display()` with a connected browser for the scene → no emit, flush only.
- [ ] `display()` with server down → starts server and emits once.
- [ ] disconnect clears active state → next `display()` re-emits.
- [ ] `show(jupyter=None)` with `_jupyter=True` → routes to `display()`;
      `show(jupyter=False)` → opens a browser.
- [ ] `with viz:` clears the main scene and calls `show()` on exit.
- [ ] `with viz.scene("name") as s:` clears/shows that scene.
- [ ] `__exit__` propagates an exception raised inside the `with` body.

### Step 7 — Docs & changelog

- [ ] Update `docs/py/viz/jupyter.md`: idempotent `display()`/`show()` and the
      context-manager usage.
- [ ] Update `docs/py/viz/visualizer.md`: context manager + idempotent display
      notes.
- [ ] Append a changelog entry under **New Features** in
      `docs/changelog/2026-08-22_fix-viz.md`.

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


