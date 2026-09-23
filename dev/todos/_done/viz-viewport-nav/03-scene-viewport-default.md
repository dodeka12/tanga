# Phase 3 — Scene-wide viewport default

## Goal

Add a scene-wide viewport default to `SceneConfig`, pushed on the existing
`scene_config` message, so `VizSceneHandle.set_viewport()` (Phase 4) has a
place to write and so a scene can prescribe a default zoom/pan for all its
panes.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/scene.py`
- Edit: `py/tests/viz/test_viewport.py` (or a scene test)

## Steps

- [x] **3.1 — `SceneConfig.viewport` field**
  - Add `viewport: ViewportConfig | None = None` to `SceneConfig` (import
    `ViewportConfig` from `camera.py`).
- [x] **3.2 — `to_dict()` emits `viewport`**
  - When `viewport` is not `None`, emit `result["viewport"] =
    self.viewport.to_dict()` (the README contract shape).
- [x] **3.3 — tests**
  - `SceneConfig(viewport=ViewportConfig(zoom=2.0, pan=(0.1, 0.0))).to_dict()`
    includes the `viewport` key; `None` omits it.

## Validation

```
uv run pytest py/tests/viz/test_viewport.py -q
```

## Notes

- Do not touch the frontend `scene_config` handling yet — that is Phase 5.
- `ViewportConfig.to_dict()` must already be stable from Phase 2.
