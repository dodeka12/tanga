# Phase 2 — `Visualizer.set_scene_lighting`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (scene config + the
> `scene_config` push path) and follow the existing `Visualizer.set_camera` /
> `set_cursor` pattern so the new setter is consistent.  This phase reuses the
> existing `scene_config` message; no new protocol.

## Goal

Expose a runtime API to set a scene's lighting and re-push `scene_config`, so the
frontend (phases 4–5) can re-light everything without a scene rebuild.

## Files

- **Edit** `py/pytanga/viz/visualizer.py` — add `set_scene_lighting`.
- **Edit** `py/tests/viz/test_scene_lighting.py` (or a new integration test).

## Steps

- [x] 2.1 Add `set_scene_lighting(lighting, *, scene_name="")` to `Visualizer`,
  placed near `set_camera`/`set_cursor`.  It:
  - resolves `scene = self._layout.scenes[scene_name]`,
  - sets `scene.config.lighting = lighting` (accept `SceneLighting | None`;
    `None` → back to the frontend default),
  - calls `self._push_scene_config(scene_name)`.
  - Mirrors the docstring style of `set_camera` (Args + note that it pushes
    `scene_config`).
- [x] 2.2 Add a test that `set_scene_lighting(...)` writes `scene.config.lighting`
  and that `_scene_config_for(name)["lighting"]` reflects it (or, where the
  existing tests assert on pushed config, extend them).  Include a `None` case
  that clears the field and omits the key.

## Validation

```bash
uv run pytest py/tests/viz/test_scene_lighting.py -q
```
