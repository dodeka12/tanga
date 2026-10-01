# Phase 3 — Calibrated background-image surface

## Goal

Add the calibrated backing: an `InteractionSurface` bound to a `SceneView` whose
`CameraView` carries `navigation="2d"` + `background_image`, using a
`CalibratedPlaneMapper`.  The surface plane is the ⟂-optical-axis plane at
`depth`; the image is the background (visual only).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/_surface.py` (if a convenience constructor is added)
- Edit: `py/pytanga/viz/camera.py` (no change expected — reuse `CalibratedPlaneMapper`)
- New/Edit: `py/tests/viz/test_background_surface.py`

## Steps

- [x] **3.1 — `CalibratedSurface` helper**
  - `InteractionSurface(mapper=CalibratedPlaneMapper(camera, depth))` plus a
    convenience `CalibratedSurface(camera, depth, on_drag=…)`.
- [x] **3.2 — Bind to a `CameraView` pane**
  - `SceneView("world", camera_view=CameraView(cam, navigation="2d",
    background_image=…), surface=surface)` — the background image is the visual;
    the surface is the ⟂-optical-axis plane at `depth`.
- [x] **3.3 — `read_only` world pane**
  - The world pane is `SceneView("world", read_only=True)` so it orbits/zooms but
    neither labels nor edits `Act` shapes.
- [x] **3.4 — Tests**
  - Unit: the surface serializes the mapper plane; `read_only` serializes into
    the `scene_view` node.

## Validation

```
uv run pytest py/tests/viz/test_background_surface.py -q && uv run ruff check . && uv run ty check
```

## Notes

- The screen→world resolution uses `camera.pixel_ray` + `mapper.plane()`; verify
  the screen↔image-pixel mapping against the pinhole framing in the browser
  smoke test (drag a shape in the image pane and confirm it lands under the
  cursor in the calibrated view).
