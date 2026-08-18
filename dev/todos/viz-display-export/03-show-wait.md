# Phase 3 — `show()` and `wait()`

**Status:** Done

## Goal

Provide the friendly two-call pattern for "look at the scene":
`show()` = `start_server()` + `open_browser()`; `wait()` blocks until Ctrl+C
then stops the server. Deprecate `run()`.

## Files

- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`

## Steps

- [x] Add `Visualizer.show()` → `start_server()` + `open_browser()`.
- [x] Add `Visualizer.wait()` — synchronous block on `self._shutdown_requested`
      (poll with `time.sleep`), then `stop_server()` on return. Windows-safe
      (thread-based, not `loop.add_signal_handler`).
- [x] Add `VizSceneHandle.show()` → `viz.start_server()` (if needed) +
      `self.open_browser()`.
- [x] Deprecate `run()` as `show(); wait()` (alias with `DeprecationWarning`).
- [x] Ensure `animate()` (unchanged) now relies on `start_server()` internally.

## Unit tests

- [x] `py/tests/viz/test_scene_session.py`:
  - [x] `show()` serves and opens the browser.
  - [x] `run()` emits `DeprecationWarning` (patch `show`/`wait`).
  - [x] `wait()` returns after `_shutdown_requested` is set and calls
        `stop_server` (patch it).

## Verification

- [x] `uv run pytest py/tests/viz/` passes (426 tests).
