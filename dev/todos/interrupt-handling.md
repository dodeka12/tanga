# Per-Scene Interrupt Handling for the Visualizer

**Created:** 2026-08-21 | **Status:** Implemented (pending manual browser verification)

## Goal

Allow a running animation loop to be interrupted from the browser side, with
the interrupt scoped to a single scene by default instead of tearing down the
whole server. Preserve today's terminal Ctrl+C / SIGTERM behaviour as a
_global_ interrupt that stops every scene loop and shuts the server down at
process exit.

Specifically:

1. A user can press a configurable key (with optional modifiers) in the browser
   to end the `animate()` loop. Default: **q**, no modifiers.
2. The binding is per scene. The `q` key in scene `A` stops only scene `A`'s
   loop; other scenes keep animating.
3. Terminal Ctrl+C / SIGTERM remains a global interrupt: it stops all scene
   loops and, via the existing `atexit` hook, shuts the server down.
4. `animate()`, `interrupted()`, and `sleep_ms()` all share the same interrupt
   semantics (global OR per-scene).

## Background (current behaviour)

- `Visualizer._shutdown_requested` is a single `threading.Event`, created in
  `_ensure_server_running()` and set only by the SIGINT/SIGTERM handler
  (`py/pytanga/viz/visualizer.py`).
- `animate()` loops `while not shutdown.is_set()` and runs
  `finally: self.stop_server()` — so _any_ loop exit stops the server.
- `interrupted()` and `sleep_ms()` both read that one event.
- `VizSceneHandle` (`py/pytanga/viz/_scene_handle.py`) already exposes
  `animate_to`/`timeline` but **not** `animate`, `interrupted`, or `sleep_ms`.
- The browser talks to the backend over WebSocket. `VizServer._ws_handler`
  (`py/pytanga/viz/server.py`) dispatches `ready`, `scene_synced`,
  `screenshot:data`, `control:*`, and `interaction:*` — no generic key event.
- The frontend already has a precedent for a global keybinding: the Ctrl+S
  screenshot handler in `py/pytanga/viz/templates/viewer.js`.

## Design decisions

1. **Two interrupt layers.**
   - **Global** — the existing `_shutdown_requested` event. Ctrl+C/SIGTERM sets
     it and cascades to every registered per-scene event.
   - **Per scene** — a new `self._interrupt_events: dict[str, threading.Event]`
     keyed by scene name (`""` = main scene). The browser key sets only that
     scene's event.
2. **`interrupted(scene)` = global OR scene** so `animate()`/`sleep_ms()` stay
   one code path while remaining scene-aware.
3. **Default key is `q` with no modifiers** (browsers report `e.key === "q"`;
   no copy/OS shortcut conflict, unlike Ctrl+C).
   Per-scene override via `stop_key`/`stop_modifiers`.
4. **`stop_key=None` disables the browser binding** for that scene (the loop is
   then only interruptible via terminal Ctrl+C).
5. **A general `KeyModifier` string enum** (values `"ctrl"`, `"shift"`,
   `"alt"`, `"meta"`) is the single source of truth for keyboard modifiers
   shared with the frontend. `stop_modifiers` accepts `KeyModifier` members
   (raw strings matching a member value are also accepted for convenience), and
   serialization sends each member's `.value`. It is declared in a general
   module (`_keys.py`) so object-interaction code can reuse the same enum.
6. **Server teardown moves to the existing `atexit` hook.** `animate()` no
   longer calls `stop_server()` in its `finally`; `_ensure_server_running()`
   already registers an idempotent `atexit`-based `stop_server(timeout=2.0)`.
   A browser-scope `q` interrupt therefore never tears the server down, while a script
   that is "just an animation loop" still stops cleanly at interpreter exit.

## Files

- Add: `py/pytanga/viz/_keys.py` (general `KeyModifier` enum)
- Modify: `py/pytanga/viz/server.py`
- Modify: `py/pytanga/viz/visualizer.py`
- Modify: `py/pytanga/viz/_scene_handle.py`
- Modify: `py/pytanga/viz/templates/viewer.js`

## Steps

### Step 1 — General `KeyModifier` enum

- [x] Add `py/pytanga/viz/_keys.py` defining a string-based
      `class KeyModifier(str, Enum)` with members `CTRL = "ctrl"`,
      `SHIFT = "shift"`, `ALT = "alt"`, `META = "meta"`.
- [x] Export/import it where needed so both the animation-stop code and future
      frontend interactions share the same enum (do **not** duplicate the
      modifier set).

### Step 2 — WebSocket plumbing in `server.py`

- [x] Add `animation_stop_callback: Callable[[str], Awaitable[None]] | None` and
      `push_animation_stop: Callable[[str], Awaitable[None]] | None` params to
      `VizServer.start()`; store them on `self`.
- [x] In `_ws_handler`, add a `msg_type == "animation_stop"` branch that calls
      `self._animation_stop_callback(data.get("scene", ""))` via
      `asyncio.create_task`.
- [x] In the `ready` branch, alongside the existing `_push_controls_cb` call,
      also call `push_animation_stop(scene_name)` so a fresh/reconnected browser
      receives the correct scene binding.

### Step 3 — Per-scene interrupts in `visualizer.py`

- [x] In `__init__`, add `self._interrupt_events: dict[str, threading.Event] = {}`
      and `self._scene_interrupt_configs: dict[str, dict] = {}`.
- [x] Add `_interrupt_event(scene_name="")` that lazily creates/returns the
      scene's `threading.Event`.
- [x] Extend `_on_sigint` (in `_ensure_server_running`) to also `set()` every
      event in `self._interrupt_events`.
- [x] Add `_on_browser_animation_stop(scene_name)` that sets the scene event;
      wire it into `VizServer.start(animation_stop_callback=...)`.
- [x] Add async + thread-safe `_push_animation_stop`/`_push_animation_stop_async`
      sending `{type:"animation_stop_config", scene, enabled, key, modifiers}`;
      wire `push_animation_stop` into `VizServer.start`.
- [x] Add `_register_animation_stop(scene_name, stop_key, stop_modifiers)` that
      normalizes `stop_modifiers` into `KeyModifier` members (accepting raw
      strings), validates against the enum, and stores + pushes the config.
- [x] Make `interrupted(scene_name="")` return
      `global.is_set() or self._interrupt_event(scene_name).is_set()`.
- [x] Make `sleep_ms(milliseconds, scene_name="")` wait on the scene event and
      return `False` early when `interrupted(scene_name)`.
- [x] Change `animate()` to
      `animate(*, fps=60.0, stop_key="q", stop_modifiers=None, scene_name="")`
      where `stop_modifiers: Sequence[KeyModifier] | None = None`; register the
      binding, loop `while not self.interrupted(scene_name)`.
- [x] Remove `finally: self.stop_server()` from `animate()` and `wait()` (rely
      on the existing `atexit` hook).

### Step 4 — Scene-handle API in `_scene_handle.py`

- [x] Add `animate(*, fps=60.0, stop_key="q", stop_modifiers=None)`
      (with `stop_modifiers: Sequence[KeyModifier] | None`) delegating to
      `self._viz.animate(..., scene_name=self._name)`.
- [x] Add `interrupted()` delegating to `self._viz.interrupted(scene_name=self._name)`.
- [x] Add `sleep_ms(milliseconds)` delegating to
      `self._viz.sleep_ms(milliseconds, scene_name=self._name)`.

### Step 5 — Frontend key handling in `viewer.js`

- [x] Add module state
      `let _animationStopConfig = { enabled: false, key: null, modifiers: [] };`.
- [x] In `handleMessage`, handle `animation_stop_config` with a strict scene
      compare (`(msg.scene ?? '') === _myScene`).
- [x] Add a global `keydown` listener (in `initScene`, outside the WebGL guard)
      that matches the configured key/modifiers (`ctrl` = `ctrlKey || metaKey`;
      `shift`/`alt`/`meta` map to their flags), calls `preventDefault()`, and
      sends `{type:'animation_stop', scene:_myScene, browser_id:_browserId}`.

### Step 6 — Verification

- [x] `uv run pytest py/tests/viz` stays green (backend regression guard).
- [ ] Manual: `for dt in viz.animate(fps=60): ...` — `q` (or `Q`) in the browser stops
      the loop without stopping the server; Ctrl+C in the terminal still stops
      cleanly (server stops at interpreter exit).
- [ ] Manual: two scenes animating concurrently — `q` in one scene stops only
      that scene's loop.

### Step 7 — Docs & changelog (this branch)

- [x] Update the relevant public docstrings/examples as needed
      (e.g. `py/pytanga/viz/visualizer.py`, `py/examples/viz/*`).
- [x] Add one branch changelog `2026-08-21_feat-interrupt-handling.md` under
      `docs/changelog/`, following `dev/workflows/changelog.md`.

## Notes / edge cases

- `stop_modifiers` must be `KeyModifier` members (or matching strings); an
  unknown modifier raises `ValueError`.
- The default `q` binding must not fire while the user is typing in an
  input/textarea/annotation (add an editable-target guard in the keydown
  listener).
- `atexit` runs only on normal interpreter exit (not `os._exit()`/SIGKILL) —
  same guarantee the existing code already has.
- `stop_server()` is idempotent, so an explicit `stop_server()` followed by the
  `atexit` hook is safe.