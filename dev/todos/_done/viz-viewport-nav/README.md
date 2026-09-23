# Viz Viewport Navigation — Overview

**Created:** 2026-09-22 | **Status:** Done | **Branch:** `feat/calib-cam-view`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Add a general per-pane **2D-style viewport navigation** — cursor-anchored wheel
**zoom (dolly)** plus screen-space drag **pan**, with **no orbit** — available to
any pane (2D ortho, 3D perspective, or calibrated pinhole, with or without a
`background_image`). The mouse buttons and an optional lock are settable from
Python, and a `set_viewport()` API sets/resets zoom + pan from Python on both
the `Visualizer` and the scene handle.

For a calibrated pinhole pane this makes the camera image behave like a 2D image
viewer (zoom/pan over the image) while the 3D camera stays fixed.

## Architecture (short)

- **Model** — a `Navigation` enum (`"orbit"` | `"2d"`) and a `ViewportConfig`
  dataclass (`zoom`, `pan`, optional `min_zoom`/`max_zoom`/`pan_xlim`/`pan_ylim`)
  live in `camera.py` next to `CameraAction`/`CameraLock`.
- **Per-pane** — `CameraView`/`SceneView` gain `navigation`, a per-pane
  `controls` button mapping, and a `viewport`; serialized in the existing
  `scene_view` node (`camera_view` field), applied by `ThreeJsView`.
- **Scene default** — `SceneConfig.viewport` (a scene-wide default), pushed on
  the existing `scene_config` message.
- **Runtime set** — `Visualizer.set_viewport(view, …)` sends a per-pane
  `view_viewport` message (the same `push_raw` seam + `viewer.js` dispatcher as
  `view_camera`); `set_viewport(scene_name=…, …)` re-pushes `scene_config`;
  `VizSceneHandle.set_viewport(…)` delegates to the scene-level form.
- **Frontend** — a `"2d"` navigation mode (disable rotate, `zoomToCursor`,
  per-pane button mapping) plus `ThreeJsView.setViewport(...)`; the viewport
  transform folds into `pinhole-framing.js` as a **crop window** so the
  projection and the background image can never diverge.

No new communication channel: per-pane state rides the `view_viewport` message
(mirroring `view_camera`), scene defaults ride `scene_config`, and no new event
registry or binary channel is introduced.

## Decisions (confirmed)

- Zoom = dolly + screen-space pan, **no orbit** (rotate disabled in `"2d"` mode).
- API name `set_viewport()`, available on `Visualizer` and `VizSceneHandle`.
- All frontend traffic uses the established message dispatch only
  (`view_viewport` mirroring `view_camera`, and `scene_config`).
- Zoom is cursor-anchored (`OrbitControls.zoomToCursor`).
- Mouse buttons and lock are settable from Python (per-pane `controls` + `lock`).
- `VizSceneHandle.set_viewport(…)` sets the **scene-wide default**
  (`SceneConfig.viewport`), not a single pane (consistent with
  `VizSceneHandle.set_camera`).
- `set_viewport(zoom=None, pan=None)` is a **partial update** — `None` leaves the
  current value unchanged; passing both values resets the view.
- `SceneView`'s scene parameter is a concrete union
  `str | Scene | VizSceneHandle`.
- `Orientation` becomes the `EOrientation` StrEnum (no backward compatibility).

## Contract (fixed up front)

### `ViewportConfig` (Python) and its JSON shape

```python
@dataclass
class ViewportConfig:
    zoom: float = 1.0
    pan: tuple[float, float] = (0.0, 0.0)
    min_zoom: float | None = None
    max_zoom: float | None = None
    pan_xlim: tuple[float, float] | None = None
    pan_ylim: tuple[float, float] | None = None
```

Serialized (absent fields are `None` and omitted):

```json
{
  "zoom": 1.0, "pan": [0.0, 0.0],
  "min_zoom": 1.0, "max_zoom": 8.0,
  "pan_xlim": [-0.5, 0.5], "pan_ylim": [-0.5, 0.5]
}
```

Semantics: `zoom` is a scale factor (`1.0` = full/fit framing, `>1` zooms in);
`pan` is the view-center offset in the base framing's normalized (NDC) space,
`[0, 0]` = centred.

### `CameraView` / `SceneView` serialized fields

The `camera_view` dict gains:

```json
{
  "camera": {…},
  "navigation": "2d",
  "controls": {"left": "pan", "middle": "dolly", "right": null},
  "lock": ["pan", "zoom"],
  "viewport": { "zoom": 1.0, "pan": [0.0, 0.0] },
  "background_image": {…}
}
```

### Per-pane runtime message

```json
{"type": "view_viewport", "view_id": "sv0", "viewport": {"zoom": 1.0, "pan": [0.0, 0.0]}}
```

`zoom`/`pan` may be omitted (`None`) for a partial update. Handled in `viewer.js`
next to `view_camera`, dispatched to `ThreeJsView.setViewport(msg.viewport)`.

### Scene default

`SceneConfig.to_dict()` gains `"viewport": {"zoom": 1.0, "pan": [0.0, 0.0]}`.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-views-api-type-cleanup.md](./01-views-api-type-cleanup.md) | Concrete `SceneRef` union + `EOrientation` enum in `views.py` |
| 2 | [02-python-viewport-model.md](./02-python-viewport-model.md) | `Navigation` + `ViewportConfig` model; `CameraView`/`SceneView` fields + serialization |
| 3 | [03-scene-viewport-default.md](./03-scene-viewport-default.md) | `SceneConfig.viewport` scene-wide default |
| 4 | [04-server-set-viewport.md](./04-server-set-viewport.md) | `set_viewport` on `Visualizer` + `VizSceneHandle` |
| 5 | [05-frontend-viewport-nav.md](./05-frontend-viewport-nav.md) | `view_viewport` dispatch, `"2d"` nav mode, `ThreeJsView.setViewport` |
| 6 | [06-pinhole-crop-framing.md](./06-pinhole-crop-framing.md) | Crop-window framing in `pinhole-framing.js` + `image-background.js` |
| 7 | [07-examples-docs-changelog.md](./07-examples-docs-changelog.md) | Example, developer docs, changelog |

## Testing as you go

- Python: `uv run pytest py/tests/viz -q`
- Node framing: `uv run pytest py/tests/viz/test_pinhole_math.py -q`
- JS bundle: `uv run python tools/build-viewer-js.py --check`
- Docs: `uv run mkdocs build --strict`
- Full: `uv run pytest -q`

## Non-goals

- No new message channel, event registry, or binary transport.
- No orbit/rotate behaviour in `"2d"` navigation mode.
- No per-entity zoom/pan (this is pane-level viewport navigation only).
- No perspective "fly-through" or camera-path navigation.
