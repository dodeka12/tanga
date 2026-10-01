# Phase 3 — Drag-to-draw in the calibrated labeling example

## Goal

Wire the calibrated labeling example to draw shapes by dragging on the calibrated
pane (the `CalibratedPlaneMapper` plane), reusing `DragPreview` + the `Act*`
shape classes.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py`

## Steps

- [x] **3.1 — Hit plane**
  - Add a transparent raycastable `Plane` geometry at the annotation `depth` as
    the calibrated drag surface's entity (the `CameraView.background_image`
    remains the visual).
- [x] **3.2 — Drag surface**
  - Construct the mapper-aware `ActImagePlane` (no `ImageView`, `mapper=
    CalibratedPlaneMapper(...)`, `entity=<hit plane>`) and register it with the
    world scene.
- [x] **3.3 — Toolbar + DragPreview**
  - Reuse the `ImageLabeler` toolbar/`DragPreview` pattern, driving `begin`/
    `update`/`finalize` from the plane's drag events (`on_drag_start`/`on_drag`/
    `on_drag_end`), with shapes added to the shared `"world"` scene.
- [x] **3.4 — Test**
  - `test_calibrated_labeling_example.py`: assert the app still loads labels and
    builds the two-pane layout; assert the hit plane sits at the mapper's `depth`
    on the optical axis.

## Validation

```
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py && uv run python tools/generate-example-docs.py --check
```

## Notes

- Manual smoke (browser, not CI): `uv run python
  py/examples/apps/calibrated_labeling_app.py` — drag in the left (calibrated)
  pane draws a shape that also appears in the right (world) pane.
