# Phase 6 — Calibrated labeling example app

## Goal

A new example app: calibrated `CameraView` (left) + world `SceneView` (right),
both showing the same `"world"` scene, with editable labelme shapes mapped to 3D
via `CalibratedPlaneMapper`.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- New: `py/examples/apps/calibrated_labeling_app.py`
- New: `py/tests/viz/test_calibrated_labeling_example.py`
- Reuse: `py/examples/viz/camera/data/tless/` (image + calibration)

## Steps

- [ ] **6.1 — Calibration + mapper setup**
  - Load the bundled T-LESS `calibration.json`/`image.png` (as in
    `pinhole_calibrated.py`), build `CameraCalibration`, then
    `CalibratedPlaneMapper(calib, depth=…)` and `LabelMeStore(mapper=…)`.
- [ ] **6.2 — Layout**
  - Left: `SceneView("world", camera_view=CameraView(cam, navigation="2d",
    background_image=…), hide={frustum.id})`.
  - Right: `SceneView("world", camera_view=CameraView(overview_cam))` showing the
    `Frustum` + shapes in 3D.
  - `SplitView("horizontal", [left, right])`.
- [ ] **6.3 — Editable shapes (3D)**
  - Reuse the toolbar/`DragPreview`/`Act*` machinery from `ImageLabeler`, but add
    shapes to the shared `"world"` scene through `LabelMeStore` (points mapped to
    world by `CalibratedPlaneMapper`).
  - Draw/select/delete rect/ellipse/circle/line/polygon/point; load/save labelme
    JSON.
- [ ] **6.4 — Header + docs**
  - Module docstring per `dev/workflows/example-docs.md` (first line, `Run with:`,
    `Keywords:`); regenerate example docs.
- [ ] **6.5 — Data-validation test**
  - `test_calibrated_labeling_example.py` loads the calibration and asserts the
    mapper round-trips the principal point + a known world point; asserts the app's
    module imports and constructs a layout without error.

## Validation

```
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py && uv run python tools/generate-example-docs.py --check
```

## Notes

- Manual smoke (browser, not CI): `uv run python
  py/examples/apps/calibrated_labeling_app.py` — left pane shows the photo with
  editable shapes projected on it; right pane shows the frustum + the same shapes
  in 3D.
