# Phase 3 — `show()` and `wait()`

**Status:** Planned

## Goal

Provide the friendly two-call pattern for "look at the scene":
`show()` = `start_server()` + `open_browser()`; `wait()` blocks until Ctrl+C
then stops the server. Deprecate `run()`.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`

## Steps

- [ ] Add `Visualizer.show()` → `start_server()` + `open_browser()`.
- [ ] Add `Visualizer.wait()` — synchronous block on `self._shutdown_requested`
      (poll with `time.sleep`), then `stop_server()` on return. Windows-safe
      (thread-based, not `loop.add_signal_handler`).
- [ ] Add `VizSceneHandle.show()` → `viz.start_server()` (if needed) +
      `self.open_browser()`.
- [ ] Deprecate `run()` as `show(); wait()` (alias with `DeprecationWarning`).
- [ ] Ensure `animate()` (unchanged) now relies on `start_server()` internally.

## Unit tests

- [ ] `py/tests/viz/test_scene_session.py`:
  - [ ] `run()` emits `DeprecationWarning` (patch `show`/`wait`).
  - [ ] `wait()` returns after `_shutdown_requested` is set and calls
        `stop_server` (patch it).

## Verification

- [ ] `uv run pytest py/tests/viz/test_scene_session.py` passes.
