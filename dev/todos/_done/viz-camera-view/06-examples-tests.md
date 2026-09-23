# Phase 6 — Fix examples + regenerate docs + tests

## Goal

Fix the two examples (origin-centred content, camera looking at the origin, using
`CameraView`), regenerate their docs, and close out the regression tests.

## Files

- Edit: `py/examples/viz/camera/pinhole_overlay.py`
- Edit: `py/examples/viz/camera/pinhole_camera.py`
- Regenerate: `docs/py/examples/` (via `tools/generate-example-docs.py`)
- Edit: `py/tests/viz/test_export_renderers.py` (if a renderer list changed)

## Steps

- [x] **6.1 — origin-centred content**
  - Place world objects near the origin and point the camera at the origin
    (e.g. `t = [0, 0, 6]`, camera at `z=-6` looking toward `+z`), so both the
    camera pane and the default overview pane frame the same content.

- [x] **6.2 — use `CameraView`**
  - `pinhole_overlay.py`: `CameraView(pinhole_camera(...), lock={…},
    background_image=…)` on the left pane; default `SceneView` on the right
    (frustum shown). `pinhole_camera.py`: free-orbit `CameraView` (no lock/image)
    + default overview + frustum.

- [x] **6.3 — regenerate docs + full suite**
  - `uv run python tools/generate-example-docs.py`; run the full viz test suite
    and the bundle check.

## Validation

`uv run python tools/generate-example-docs.py && uv run pytest py/tests/viz -q && uv run python tools/build-viewer-js.py --check`

## Notes

- Keep the left pane sized to the image aspect note in the docstring.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
