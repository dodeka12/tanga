# HTML export — honor the live scene camera and play per-frame camera changes

**Created:** 2026-08-25 | **Status:** Planned

## Goal

Make the self-contained HTML exports (snapshot, figure, animated figure, animated
full-page) honor the camera configured on the live scene, and — for animated
exports — record and play back camera changes that occur between frames.

Two concrete defects are addressed:

1. The export bootstrap ignores the scene's camera. In particular a 2D
   `View2DConfig`/`CameraConfig2d` rectangle (`xmin/xmax/ymin/ymax`,
   `uniform`, `border_px`) and a 3D `up` vector are dropped, so exported HTML
   shows the default camera instead of the live scene's camera.
2. `AnimationRecording` captures only entity/label state, never the scene
   camera, so a `viz.set_camera(...)` inside an animation loop is lost and the
   exported animation never moves the camera.

## Background / analysis

### Current state

The backend already serializes the camera into the config that feeds the export
renderers: `scene.config.to_dict()` includes `camera`, and it is passed into
`render_snapshot` (`visualizer.py:2375`), `render_figure`
(`visualizer.py:2461-2464`), and `render_export_animated_html`
(`visualizer.py:2366-2371`). The defect is entirely in the export JS generators.

The export bootstrap is assembled in `py/pytanga/viz/export/_bootstrap/_scene.py`
(`js_scene_setup`, `js_autofit_camera`) and the per-adapter glue in
`_html.py`, `_figure_html.py`, and `_animated_figure.py`. The animated playback
engine lives in `_bootstrap/_animation.py`.

### Root cause — camera not honored (Problem 1)

1. **2D rectangle is hardcoded away.** `js_scene_setup`'s 2D branch
   (`_bootstrap/_scene.py:108-119`) emits `const _frustumSize = 20;` and
   `position.set(0, 0, 20); lookAt(0, 0, 0);`. It never reads
   `xmin/xmax/ymin/ymax`, `uniform`, or `border_px`, and ignores the config's
   `position`/`target`.
2. **3D `up` is ignored.** `js_scene_setup` only accepts `cam_fov/cam_pos/
   cam_target/cam_near/cam_far`; `CameraConfig3d.up` is never applied.
3. **Adapters extract only flat fields.** `_html.py:85-90`,
   `_figure_html.py:150-162`, and `_animated_figure.py:350-356` read only
   `position/target/fov/near/far` from `scene_config["camera"]`; the 2D
   rectangle and `up` are never extracted. The static full-page adapter's manual
   post-application (`_html.py:156-166`) re-applies only those five fields.
4. **Animated figure never sees the scene config.** `_build_animated_figure_adapter`
   (`_animated_figure.py:216-332`) hardcodes `cam_fov=50`,
   `cam_pos=(8, 6, 10)`, `cam_target=(0, 0, 0)` and reads
   `space_dim = figure_style.get("space_dim", 3)` — but `FigureStyle` has no
   `space_dim` (`_styles/_overlay_styles.py:110-145`), so **animated figures
   always render as 3D**. `Visualizer._render_figure_html`
   (`visualizer.py:2452-2457`) does not pass `scene.config.to_dict()` into
   `render_export_animated_figure`.

### Root cause — camera changes not recorded/played (Problem 2)

1. **Recording snapshots entities only.** `_animation_recording.py:50-61` —
   `capture_frame()` calls `Scene.full_state()` and never reads
   `self._scene.config.camera`.
2. **Playback reconciles entities only.** `_bootstrap/_animation.py` —
   `js_reconcile_frame` / `_playFrame` iterate `frames[n]` and reconcile entity
   meshes and labels; there is no camera handling. `js_animation_data_init`
   extracts only `frames`/`fps`.

Only **server-side** camera changes (`viz.set_camera(...)`) can be captured;
browser-side orbit/pan/zoom is never sent back to Python and is therefore out of
scope for export data.

## Design decisions

1. **One shared camera applier.** Add a `js_apply_camera(...)` generator that
   emits an `applyCameraConfig(camera, controls, cfg, w, h)` JS function plus a
   `_orthoFrustum2d(...)` helper. It dispatches on `cfg.type`:
   - `"2d"` → compute the ortho frustum from `xmin/xmax/ymin/ymax` +
     `uniform` + `border_px` (mirroring `view_mode.js _orthoFrustum`), set
     `left/right/top/bottom`, `position`, `lookAt`, `controls.target`, and
     `updateProjectionMatrix()`.
   - `"3d"` → set `fov/near/far/position/up/target`, `updateProjectionMatrix()`.
   - legacy/partial config (no `type`) → apply the flat fields
     `position/target/fov/near/far/up`.
   - `null`/`undefined` → no-op (caller falls back to autofit).
2. **`js_apply_camera` is layered on top of the default camera, then the flat
   path is removed.** Each adapter first calls `js_apply_camera` with the full
   camera config (so the 2D rectangle and 3D `up` are applied; a no-op when the
   camera is absent). Once every adapter relies on it, the now-redundant flat
   `cam_*` parameters are removed from `js_scene_setup` (default camera only).
3. **Recording carries a parallel `cameras` list.** `AnimationRecording`
   snapshots `scene.config.camera.to_dict()` (or `null`) per frame and returns it
   as `cameras` in `to_dict()`. This is additive — `frames`/`frame_count` keep
   their shape, so the existing id-reconciliation engine is unchanged.
4. **Playback applies the camera after entity reconciliation.** `_playFrame(n)`
   reconciles `frames[n]` as today, then calls
   `applyCameraConfig(camera, controls, cameras[n], w, h)` when `cameras[n]` is
   set. The current container size is used so the 2D ortho frustum stays correct.
5. **Animated figure receives the scene config.** `render_export_animated_figure`
   gains a `scene_config` parameter threaded from `_render_figure_html`, so the
   animated figure adapter can use the scene's `space_dim` and camera instead of
   hardcoded 3D defaults.

## Changes

### Step 1 — Record per-frame camera

**File:** `py/pytanga/viz/export/_animation_recording.py`

- [x] Add `self._cameras: list[dict | None] = []` in `__init__`.
- [x] In `capture_frame()`, snapshot the current scene camera:
  `cam = self._scene.config.camera; self._cameras.append(cam.to_dict() if cam is not None else None)`.
- [x] In `to_dict()`, add `"cameras": self._cameras` alongside `frames` and
  `frame_count` (keep the existing keys for backward compatibility).

### Step 2 — Shared camera applier

**File:** `py/pytanga/viz/export/_bootstrap/_scene.py`

- [x] Add `js_apply_camera(...)` generator emitting `_orthoFrustum2d(...)` and
  `applyCameraConfig(camera, controls, cfg, w, h)` per Design decision 1.
- [x] Guard the ortho math against non-finite/zero sizes (fall back to a sane
  default, never write `NaN`/`Infinity` into the frustum).

**File:** `py/pytanga/viz/export/_bootstrap/__init__.py`

- [x] Export `js_apply_camera`.

### Step 3 — Static full-page export applies the scene camera

**File:** `py/pytanga/viz/export/_html.py`

- [x] In `_build_static_fullpage_adapter`, after `js_scene_setup`, emit a
  `js_apply_camera` call with `sceneConfig.camera` and `window.innerWidth` /
  `window.innerHeight` (keep the flat `cam_*` defaults for now; removed in Step 7).
- [x] Keep the existing "autofit when no explicit camera" guard.

### Step 4 — Static figure export applies the scene camera

**File:** `py/pytanga/viz/export/_figure_html.py`

- [x] In the `await figBuildDone` IIFE, call `js_apply_camera` with the scene
  camera and the figure container size expression (`dim_w`/`dim_h`) before
  `js_autofit_camera`.
- [x] Keep `cam_explicit` semantics: autofit only when no explicit camera.

### Step 5 — Animated export uses the scene config + initial camera

**Files:** `py/pytanga/viz/export/_animated_figure.py`, `py/pytanga/viz/visualizer.py`

- [x] `visualizer.py:_render_figure_html` passes
  `scene_config=scene.config.to_dict()` into `render_export_animated_figure`.
- [x] `render_export_animated_figure` accepts `scene_config` and forwards it to
  `_build_animated_figure_adapter`.
- [x] `_build_animated_figure_adapter` uses `scene_config["space_dim"]` and
  `scene_config.get("camera")` instead of the hardcoded 3D defaults.
- [x] `_build_animated_fullpage_adapter` and `_build_animated_figure_adapter`
  both emit `js_apply_camera` for the initial camera before the frame-0 autofit.

### Step 6 — Animated playback applies per-frame camera

**Files:** `py/pytanga/viz/export/_bootstrap/_animation.py`, `py/pytanga/viz/export/_animated_figure.py`

- [x] `js_animation_data_init` emits `const cameras = animData.cameras || [];`.
- [x] Extend `js_reconcile_frame` to accept `camera_var`, `controls_var`, and a
  container-size expression; in `_playFrame(n)`, after `_reconcileFrame(frames[n])`,
  call `applyCameraConfig(camera, controls, cameras[n], w, h)` when `cameras[n]`
  is set.
- [x] Pass the camera/controls variables and size expressions from both animated
  adapters (`figCamera`/`figControls`, `window.*` for full-page, `figContainer.*`
  for figure).

### Step 7 — Default-only `js_scene_setup`

**File:** `py/pytanga/viz/export/_bootstrap/_scene.py`

- [x] Remove `cam_fov/cam_pos/cam_target/cam_near/cam_far` from `js_scene_setup`;
  emit the default camera only (3D `PerspectiveCamera(50, …, 0.1, 1000)` at
  `(8, 6, 10)` looking at `(0, 0, 0)`; 2D 20-unit `OrthographicCamera` at
  `(0, 0, 20)` looking at `(0, 0, 0)`).
- [x] Update the four adapters (`_html.py`, `_figure_html.py`,
  `_animated_figure.py`) to stop passing the now-redundant flat `cam_*` args.

### Step 8 — Tests

**File:** `py/tests/viz/test_export_static.py` (or a new
`py/tests/viz/test_export_camera.py`)

- [x] `render_snapshot` with a `CameraConfig2d` embeds the 2D rectangle values
  and `applyCameraConfig`.
- [x] `render_snapshot` with a `CameraConfig3d` carrying `up` embeds the `up`
  values.
- [x] `render_export_animated_figure` with a `space_dim=2` scene embeds
  `space_dim`/camera and no longer forces 3D defaults.
- [x] `AnimationRecording.to_dict()` contains a `cameras` list whose entries
  track per-frame `set_camera` changes (including a `null` entry when no camera
  is set).
- [x] `uv run pytest py/tests/viz` stays green.

### Step 9 — Example: 2D fit-camera non-distortion demo

**File:** `py/examples/viz/demo_camera_fit_2d.py`

- [x] Add a 2D example (`space_dim=2`, default camera) with an object at
  `(-20, 0)` and one at `(5, 0)`, then `flush(fit_camera=True)`.
- [x] The annotation/text explains that the fit recenters the camera without
  distorting the default axes and grid (orthographic projection keeps them
  aligned and at equal scale).

### Step 10 — Changelog

**File:** branch changelog per `dev/workflows/changelog.md`

- [x] Add a Bug Fixes bullet for the export camera being ignored, and a New
  Features bullet for per-frame camera playback in animated exports.

## Verification

- [x] `uv run pytest py/tests/viz -q` and `uv run pytest -q` green.
- [x] `uv run ruff check` / `uv run ruff format --check` on touched files.
- [x] `node --check` on any generated JS (or the existing
  `py/tests/viz/test_export_renderers.py` guard).
- [ ] Manual: `Visualizer(space_dim=2, camera=View2DConfig(...))` →
  `export_snapshot` / `export_figure` show the requested rectangle and center.
- [ ] Manual: an animated recording with `viz.set_camera(...)` between frames
  plays the camera movement in `export_snapshot(..., animation=rec)` and
  `export_figure(animation=rec)`.

## Notes / edge cases

- **Only server-side camera changes are recordable.** Browser orbit/pan/zoom is
  never sent back to Python, so it cannot appear in an export.
- **2D frustum math must mirror `view_mode.js`.** Reuse the `_orthoFrustum`
  letterbox/stretch/border logic so the export matches the live viewer exactly
  (uniform letterbox by default, stretch when `uniform=false`, `border_px`
  applied in pixels).
- **Guard sizes.** `Math.max(NaN, x)` returns `NaN`; never let a non-finite
  width/height reach the ortho frustum.
- **Backward compatibility.** `cameras` is an additive key on the recording
  JSON; `js_animation_data_init` falls back to `[]` so old recordings still play.
- **`type` discriminator.** `CameraConfig.to_dict()` always emits `type`
  (`"2d"`/`"3d"`); `applyCameraConfig` dispatches on it, with a legacy/partial
  fallback for any config lacking `type`.

## Non-goals / follow-ups

- Capturing browser-side camera interaction (orbit/pan/zoom) into exports.
- Camera animation in glTF/GLB export (glTF uses a static camera; animated glTF
  is a separate feature).
- Multi-scene / split-view per-pane camera in export (export is single-scene
  today; `view_layout` is server/WebSocket-only).
- `set_camera` on a `SceneView` (per-pane) rather than the scene itself.



