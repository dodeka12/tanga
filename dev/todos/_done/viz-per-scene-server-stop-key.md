# Per-scene browser-triggered server stop key (Ctrl+Q)

**Created:** 2026-08-23 | **Status:** Done

## Goal

Add a second, independently configurable per-scene keyboard binding that, when
pressed in the browser, ends the **whole script** — i.e. sets the global
`_shutdown_requested` event so `Visualizer.wait()` returns and every running
`animate()` loop stops — without tearing the server down from inside the
frontend (teardown still goes through the existing `wait()`/`atexit` path).

Default combo: `q` + `ctrl` (Ctrl+Q), **disabled by default**.

## Background (current behaviour)

Two independent interrupt signals exist today:

| Signal | Set by | Ends |
|---|---|---|
| `_shutdown_requested` (global `threading.Event`) | terminal Ctrl+C / SIGTERM | `wait()` returns **and** every `animate()` loop (via `interrupted()`) |
| `_interrupt_events[scene_name]` (per-scene `threading.Event`) | browser `q` stop key | only that scene's `animate()` loop |

Per-scene `q` binding flow:

1. `Visualizer.animate(..., stop_key="q", stop_modifiers=...)` →
   `_register_animation_stop(scene_name, ...)` stores
   `{enabled, key, modifiers}` in `_scene_interrupt_configs` and pushes
   `animation_stop_config`.
2. Frontend `_stopKeyMatches` / `_handleAnimationStopKey` (`viewer.js`) sends
   `{type:"animation_stop", scene, browser_id}`.
3. `server.py` dispatches to `_on_browser_animation_stop(scene_name)`, which
   only calls `_interrupt_event(scene_name).set()`.

`wait()` loops only on `_shutdown_requested`, so a browser `q` never ends it.

## Design decisions

### 1. Reuse `animation_stop` with a `scope` field

```jsonc
{ "type": "animation_stop", "scene": "", "scope": "scene" }   // per-scene q (default)
{ "type": "animation_stop", "scene": "", "scope": "server" }  // full-server ctrl+q
```

`scope` defaults to `"scene"` so older frontends keep working. The backend
dispatch branch stays single.

### 2. Per-scene server-stop registry

New `_server_stop_configs: dict[str, dict]` (parallel to
`_scene_interrupt_configs`), one entry per scene:
`{enabled, key, modifiers}`.

- `Visualizer.enable_server_stop_key(...)` → main scene `""`.
- `VizSceneHandle.enable_server_stop_key(...)` → that named scene.

Some scenes can end the server and others not, with no extra machinery: a
scene ends the server only if it was explicitly enabled.

### 3. API

```python
# Visualizer
def enable_server_stop_key(
    self,
    enabled: bool = True,
    key: str = "q",
    modifiers: list[KeyModifier] = [KeyModifier.CTRL],
) -> None: ...
```

- Constructor keyword `enable_server_stop_key: bool = False` — when `True`,
  calls `self.enable_server_stop_key()` with defaults for the **main scene
  only**. Named scenes opt in via `viz.scene(name).enable_server_stop_key(...)`.
- `enabled=False` clears/deactivates the binding.

```python
# VizSceneHandle
def enable_server_stop_key(
    self,
    enabled: bool = True,
    key: str = "q",
    modifiers: list[KeyModifier] = [KeyModifier.CTRL],
) -> None: ...
```

### 4. Push: extend `animation_stop_config`

`_push_animation_stop_async(scene)` merges the scene's server-stop config into
the same message:

```jsonc
{
  "type": "animation_stop_config",
  "scene": "",
  "enabled": true, "key": "q", "modifiers": [],
  "server_enabled": false, "server_key": "q", "server_modifiers": ["ctrl"]
}
```

The on-ready path already pushes this message per scene, so the new fields are
delivered on connect/reconnect automatically.

### 5. Frontend: dual bindings

- Track both `_animationStopConfig` (per-scene `q`) and `_serverStopConfig`.
- Parameterize `_stopKeyMatches(event, config)`.
- In `_handleAnimationStopKey`, check the per-scene binding first, then the
  server binding; on a server match send `scope:"server"`.

### 6. Server handler

Widen `animation_stop_callback` to `Callable[[str, str], Awaitable[None]]` and
forward `data.get("scope", "scene")`.

`_on_browser_animation_stop(scene_name, scope="scene")`:

```python
if scope == "server":
    shutdown = getattr(self, "_shutdown_requested", None)
    if shutdown is not None:
        shutdown.set()
    for event in self._interrupt_events.values():
        event.set()
else:
    self._interrupt_event(scene_name).set()
```

This mirrors the existing SIGINT handler and leaves actual teardown to
`wait()`/`atexit`.

## Files

- Modify: `py/pytanga/viz/visualizer.py` — `_server_stop_configs` registry,
  `enable_server_stop_key`, constructor flag, `_push_animation_stop_async`
  merge, `_on_browser_animation_stop(scene_name, scope)`.
- Modify: `py/pytanga/viz/_scene_handle.py` — `enable_server_stop_key`
  passthrough.
- Modify: `py/pytanga/viz/server.py` — callback signature + scope pass-through.
- Modify: `py/pytanga/viz/templates/viewer.js` — dual bindings + `scope`.
- Tests: `py/tests/viz/` (extend `test_scene_session.py` or a new file).
- Modify docs: `docs/py/viz/animation.md`, changelog
  `docs/changelog/2026-08-22_fix-viz.md`.

## Steps

### Phase 1 — Python plumbing

- [x] Add `_server_stop_configs: dict[str, dict]` to `Visualizer.__init__`.
- [x] Add `Visualizer.enable_server_stop_key(enabled, key, modifiers)` that
      normalizes modifiers, stores the config, and pushes it.
- [x] Add `VizSceneHandle.enable_server_stop_key(...)` passthrough.
- [x] Add `enable_server_stop_key: bool = False` constructor keyword; when
      `True`, call `self.enable_server_stop_key()` after the registry exists.
- [x] Merge `server_enabled`/`server_key`/`server_modifiers` into
      `_push_animation_stop_async`.

### Phase 2 — Server + frontend

- [x] Widen `server.py` `animation_stop_callback` to `(scene, scope)` and pass
      `data.get("scope", "scene")`.
- [x] Change `_on_browser_animation_stop(scene_name, scope="scene")` to set the
      global shutdown + all per-scene events for `scope="server"`.
- [x] Update `viewer.js`: parameterize `_stopKeyMatches`, track both bindings,
      send `scope:"server"` for the server binding, and populate both bindings
      from `animation_stop_config`.

### Phase 3 — Tests

- [x] `_on_browser_animation_stop("", scope="server")` sets `_shutdown_requested`
      and every `_interrupt_events` entry.
- [x] `_on_browser_animation_stop("detail", scope="scene")` sets only `detail`.
- [x] `enable_server_stop_key()` stores/pushes `server_*` fields; `enabled=False`
      deactivates.
- [x] Constructor `enable_server_stop_key=True` calls the method with defaults.

### Phase 4 — Docs & changelog

- [x] Document the new binding in `docs/py/viz/animation.md` (and that it now
      ends `wait()`).
- [x] Append a New Features bullet to `docs/changelog/2026-08-22_fix-viz.md`.

## Notes / edge cases

- **Default is opt-in** (`enabled=False` for every scene) so a stray Ctrl+Q
  cannot terminate existing scripts.
- **Main-scene only constructor flag** — named scenes must opt in explicitly.
- **No server teardown from the frontend** — the server-stop key only sets
  `_shutdown_requested`; `wait()`/`atexit` performs the actual stop.
- **Optional hardening** — validate `_server_stop_configs[scene]["enabled"]`
  server-side before honoring `scope:"server"`; recommended but not strictly
  required.