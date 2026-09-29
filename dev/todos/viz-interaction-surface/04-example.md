# Phase 4 — Rebuild the calibrated labeling example on the surface

## Goal

Rework `calibrated_labeling_app.py` to use the new surface: a `_CalibratedLabeler`
driven by the calibrated surface (image pane = labeling, world pane = read-only),
removing the failed `Plane` hit-surface hack.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_calibrated_labeling_example.py`
- Regenerate: `docs/py/examples/…` (via `generate-example-docs.py`)

## Steps

- [ ] **4.1 — Surface-backed labeler**
  - Replace `_CalibratedLabeler`'s `Plane` hit-surface + `ActImagePlane` with an
    `InteractionSurface(CalibratedPlaneMapper(...))`; keep the toolbar +
    `DragPreview` pattern.
- [ ] **4.2 — Two panes**
  - Left: `SceneView("world", camera_view=CameraView(cam, navigation="2d",
    background_image=…), surface=surface)`; right: `SceneView("world", read_only=True,
    camera_view=CameraView(overview_cam))`.
- [ ] **4.3 — Point style size**
  - Give the loaded `ActPoint` marker a screen-space (or smaller) style so it is
    not oversized in the calibrated scene.
- [ ] **4.4 — Tests + docs**
  - Keep the data-validation/import tests green; regenerate example docs.

## Validation

```
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py && uv run python tools/generate-example-docs.py --check
```

## Notes

- Manual smoke (browser, not CI): the image pane pans/zooms and draws shapes that
  appear in both panes; the world pane orbits but does not draw/edit.
