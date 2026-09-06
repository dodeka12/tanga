# Phase 5 — Regression tests

## Goal

Pin the 2D resize fix in the Python test suite.

## Files

- Edit: `py/tests/viz/test_camera_fit_unification.py`

## Steps

- [x] **5.1 — Assert the bundled helper exists**
  - Extend `test_bootstrap_bundles_single_camera_fit_module` to assert
    `"function applyOrthoFrustum(" in b`.
- [x] **5.2 — Assert snapshot resize emits the 2D recompute**
  - Render `render_snapshot([], {"space_dim": 2})` and assert the resize handler
    contains `applyOrthoFrustum(adapterCamera, rw, rh)`.
- [x] **5.3 — Assert responsive figure resize emits the 2D recompute**
  - Render `render_figure([], {"space_dim": 2}, {"responsive": True}, {})` and
    assert the resize handler contains `applyOrthoFrustum(figCamera, rw, rh)`.

## Validation

`uv run pytest py/tests/viz/test_camera_fit_unification.py -q`

## Notes

- The non-conditional (snapshot) branch defines `const rw = window.innerWidth;`
  and `const rh = window.innerHeight;`; the conditional (responsive figure)
  branch reads the container. Both then call
  `applyOrthoFrustum(camera, rw, rh)` under `if (camera.isOrthographicCamera)`.
