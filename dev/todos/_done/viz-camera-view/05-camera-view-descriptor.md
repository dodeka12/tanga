# Phase 5 — `CameraView` descriptor + remove scattered kwargs

## Goal

Bundle camera + lock + background image into a single `CameraView` descriptor,
accept it on `SceneView(camera_view=…)`, serialize it as one `camera_view` node
field, and remove the scattered `SceneView.lock` / `SceneView.background_image`.

## Files

- Edit: `py/pytanga/viz/views.py`
- Edit: `py/pytanga/viz/__init__.py`
- Edit: `py/pytanga/viz/_layout.py`
- Edit: `py/pytanga/viz/templates/views/build.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`
- Edit: `py/tests/viz/test_views.py`, `py/tests/viz/test_image_background.py`

## Steps

- [x] **5.1 — `CameraView` dataclass**
  - `camera: CameraConfig | PinholeCamera`, `lock: set[str] | None = None`,
    `background_image: ImageData | None = None`; validate/normalize `lock` (reuse
    `_normalize_lock`) and `background_image`.
  - `to_dict()` → `{ "camera": …, "lock": […], "background_image": {…} }`.

- [x] **5.2 — `SceneView(camera_view=…)`**
  - Replace `lock`/`background_image` kwargs with a single `camera_view` kwarg
    (accepting a `CameraView` or a bare `CameraConfig`/`PinholeCamera`).
  - Keep `camera=` for the plain free-orbit case (it builds an implicit
    `CameraView(camera=…)`), or fold `camera=` into `camera_view=` (decide:
    keep `camera=` for back-compat of existing examples).

- [x] **5.3 — serialize + byte collection**
  - Serialize `result["camera_view"] = self.camera_view.to_dict()`.
  - Update `LayoutHost._collect_background_frames` to read
    `scene_view.camera_view.background_image`.

- [x] **5.4 — frontend wiring**
  - In `build.js`, read `node.camera_view` and call
    `setCamera`/`setLock`/`setBackgroundImage` from it (instead of the removed
    `node.lock`/`node.background_image`).

- [x] **5.5 — tests**
  - Update the SceneView/image-background tests to the `camera_view` shape.

## Validation

`uv run pytest py/tests/viz/test_views.py py/tests/viz/test_image_background.py -q && node --check py/pytanga/viz/templates/views/build.js`

## Notes

- `SceneView.hide`/`show` remain on `SceneView` (layout, not camera).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
