# Phase 4 — `set_viewport` server API

## Goal

Expose `set_viewport()` on `Visualizer` (per-pane and scene-level) and on
`VizSceneHandle`, using only the established message dispatch: a per-pane
`view_viewport` message (mirroring `view_camera`) and the existing
`scene_config` push for the scene default.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/visualizer.py`
- Edit: `py/pytanga/viz/_scene_handle.py`
- Edit: `py/tests/viz/test_viewport.py` (or `test_layout_api.py`)

## Steps

- [x] **4.1 — `Visualizer.set_viewport(view, …)` (per-pane)**
  - Signature `set_viewport(view: SceneView, *, zoom: float | None = None,
    pan: tuple[float, float] | None = None) -> None`.
  - Validate `view` is a `SceneView`; build the `viewport` dict with only the
    provided (non-`None`) keys, and push
    `json.dumps({"type": "view_viewport", "view_id": view.id, "viewport": {…}})`
    via `self._server.push_raw(…)` exactly as `set_view_camera` does.
  - No-op (return) when no server/loop is present (mirror `set_view_camera`).
- [x] **4.2 — `Visualizer.set_viewport(scene_name=…, …)` (scene default)**
  - Overload/keyword `scene_name: str = ""`; when given, update
    `self._layout.scenes[scene_name].config.viewport` and call
    `_push_scene_config(scene_name)` (partial update: merge into the existing
    `ViewportConfig`, keeping limits intact).
- [x] **4.3 — `VizSceneHandle.set_viewport(…)`**
  - Add `def set_viewport(self, *, zoom=…, pan=…)` delegating to
    `self._viz.set_viewport(scene_name=self._name, zoom=…, pan=…)`.
- [x] **4.4 — tests**
  - Per-pane: `set_viewport(view, zoom=2.0, pan=(0.1, 0.0))` pushes a
    `view_viewport` JSON with the right `view_id` and only the given keys.
  - Scene: `set_viewport(scene_name="s", zoom=2.0)` updates
    `SceneConfig.viewport` and re-pushes `scene_config`.
  - Handle: `scene.set_viewport(...)` delegates to the scene-level form.

## Validation

```
uv run pytest py/tests/viz/test_viewport.py -q
```

## Notes

- `view_viewport` is a new *message type* but the same *channel* as
  `view_camera`; it is added to the `viewer.js` dispatcher in Phase 5.
- Do not mutate `SceneConfig.viewport` for the per-pane form — per-pane state is
  frontend-owned; only the scene default writes through `scene_config`.
