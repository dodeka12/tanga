# Phase 3 — Export bootstrap mirror

## Goal

Make the standalone HTML export apply the same `stretch` modes as the live
viewer.

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`

## Steps

- [x] **3.1 — `js_apply_camera` + initial 2D `_view2d`**
  - In `js_apply_camera`, replace `cfg.uniform !== false` with
    `cfg.stretch || 'fit'` for the `orthoFrustum` call and the stored
    `_view2d.stretch`.
  - In the initial 2D camera block, change `_view2d`'s `uniform: true` to
    `stretch: 'fit'`.

## Validation

`uv run pytest py/tests/viz/test_camera_fit_unification.py py/tests/viz/test_export_camera.py -q && uv run ruff check py/pytanga/viz/export/_bootstrap/_scene.py`

## Notes

- `js_apply_camera`'s `cfg` is the serialized `CameraConfig2d` dict, which now
  carries `stretch`; no other export Python driver changes are needed.
