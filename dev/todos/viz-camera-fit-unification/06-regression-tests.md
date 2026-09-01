# Phase 6 — regression tests

## Goal

Add automated regression tests pinning the unification: no `window` reads in the
camera math, size threaded through `fitCamera`, the export adapters pass the
right expression, and the 3D fit is unchanged.

## Files

- New: `py/tests/viz/test_camera_fit_unification.py`

## Steps

- [x] **6.1 — Add the Python regression test module**
  - Assert `generate_bootstrap_js("")` contains the shared
    `function finiteAspect(` and `function orthoFrustum(` and does **not**
    contain `_finiteAspectExport`/`_orthoFrustum2d`.
  - Assert the bundled `function fitCamera(` signature carries `width, height`
    and the 2D branch contains no `window.innerWidth`/`window.innerHeight`.
  - Assert `js_autofit_camera(..., width_expr=..., height_expr=...)` emits the
    6-arg `fitCamera(...)` call.
  - Assert the snapshot/figure/animated adapters pass the expected expression
    (`window.innerWidth`/`window.innerHeight` full-page;
    `figContainer.clientWidth || window.innerWidth` responsive figure).
  - Assert the bundled 3D `fitCamera` branch contains no `innerWidth`/
    `innerHeight` (guard against future regression).

- [x] **6.2 — Full frontend + JS validation**
  - Re-run the JS syntax checks from Phases 2–4 and the Node unit suite.

## Validation

`uv run pytest py/tests/viz/ -q && node --test 'dev/src/js-tests/*.test.mjs'`

## Notes

- The pure-math aspect behaviour is already covered by the Phase 1 Node test;
  these Python tests gate the source-level contract (no drift between live
  viewer and export).
- The runtime "squash is gone" check remains a manual browser smoke
  (`src/examples/floating_interactive_v3.py`) — no headless-browser harness.
