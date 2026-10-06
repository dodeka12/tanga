# Phase 5 — Keyboard facility (backend)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the subsystem(s) this work touches, so the new
> code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs (see phase 08).

## Goal

Add the backend of the general per-scene keyboard facility: `KeyEvent`/
`KeyBinding` types, the `SceneConfig.keyboard` wire field, and the
`Visualizer.on_key` / `VizSceneHandle.on_key` / `ImageCanvas.on_key` API, with
`interaction:key` dispatch reading the one `ControlHandlerRegistry`.

## Files

- Edit: `py/pytanga/viz/_interaction.py` (`KeyEvent`, `KeyBinding`, `_parse_key_event`)
- Edit: `py/pytanga/viz/_hosts.py` (`InteractionHost`: key storage + `_dispatch_key`)
- Edit: `py/pytanga/viz/scene.py` (`SceneConfig.keyboard` + `to_dict`)
- Edit: `py/pytanga/viz/visualizer.py` (`on_key`, `_push_scene_config` after register)
- Edit: `py/pytanga/viz/_scene_handle.py` (`on_key`)
- Edit: `py/pytanga/viz/_image_view.py` (`ImageCanvas.on_key` convenience)
- Edit: `py/pytanga/viz/__init__.py` (export `KeyEvent`, `KeyBinding`)
- New: `py/tests/viz/test_keyboard.py`

## Steps

- [x] **5.1 — Types.** In `_interaction.py`, add
  `KeyEvent(ControlEvent)` (`key`, `modifiers`, `scene`) and
  `KeyBinding` (`key`, `modifiers`, `handler`), plus `_parse_key_event(data)`
  (reuse `_parse_modifiers`).
- [x] **5.2 — SceneConfig.keyboard.** Add `keyboard: list[dict] | None = None`
  to `SceneConfig`; in `to_dict()`, emit `"keyboard": [...]` only when non-empty.
- [x] **5.3 — InteractionHost storage + dispatch.**
  - `InteractionHost.on_key(key, handler, modifiers, scene_name)`: store in
    `self._key_bindings[scene_name]` and register a dispatcher in
    `self._registry` under `(f"key:{scene}:{key}", "key")` with
    `origin=INTERACTION`; the dispatcher resolves the most-specific `KeyBinding`.
  - In `_dispatch_interaction_event`, special-case `msg_type == "interaction:key"`
    → build `KeyEvent` via `_parse_key_event` → look up and run the handler
    (bypass `_parse_event`/`_send_drag_anchor`).
- [x] **5.4 — Public API.**
  - `Visualizer.on_key(key, handler, *, modifiers=None, scene_name="")`;
    `VizSceneHandle.on_key(key, handler, *, modifiers=None)`;
    `ImageCanvas.on_key(key, handler, *, modifiers=None)` (delegates to handle).
  - Each calls `self._push_scene_config(scene_name)` after registering so a
    re-pushed `scene_config` carries the updated `keyboard` list.
- [x] **5.5 — Exports.** Add `KeyEvent`, `KeyBinding` to `__init__.py`.
- [x] **5.6 — Tests.** `test_keyboard.py`: `SceneConfig.to_dict()` emits
  `keyboard` only when set; `on_key` registers under the namespaced id; the
  `interaction:key` dispatch path resolves and runs the right handler.

## Validation

```
uv run pytest py/tests/viz/test_keyboard.py py/tests/viz -q
```

## Notes

- Keys are per-scene, so they live on `SceneConfig` (not `InteractionConfig`).
- Namespacing the registry id (`key:{scene}:{key}`) avoids colliding with
  control/object ids.
