# Phase 1 — shared `camera-fit.js` module

## Goal

Create the single pure source of truth for the ortho/aspect math, bundle it into
the export, and lock its behaviour with a Node unit test (it has no `three`
import, so it is Node-testable).

## Files

- New: `py/pytanga/viz/templates/camera-fit.js`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- New: `dev/src/js-tests/camera-fit.test.mjs`

## Steps

- [x] **1.1 — Add `camera-fit.js`**
  - Create the module with exactly two exports and **no** `import` statements:
    - `finiteAspect(width, height)` — returns `width / height` for positive
      finite inputs, else `NaN` (mirror the existing `_finiteAspectExport`).
    - `orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, width, height)` —
      port the current `_orthoFrustum2d` body verbatim (both `uniform === false`
      and uniform branches), computing `aspect`/`safeAspect` internally from
      `width`/`height`.
  - Include the SPDX header and a JSDoc comment on each export.

- [x] **1.2 — Bundle it in the export**
  - In `py/pytanga/viz/export/_bootstrap/_html.py`, insert
    `_TEMPLATES_DIR / "camera-fit.js"` at the head of `_SHARED_JS_FILES`
    (before `fit_camera.js`).

- [x] **1.3 — Node unit test for the pure math**
  - Add `dev/src/js-tests/camera-fit.test.mjs` importing both exports.
  - Assert `finiteAspect(200, 100) === 2`, `finiteAspect(0, 100)` is `NaN`,
    `finiteAspect(NaN, 100)` is `NaN`.
  - Assert the square/uniform case: `orthoFrustum(-10, 10, -5, 5, true, 0, 200, 100)`
    → `{left:-10, right:10, top:5, bottom:-5}`.
  - Assert the narrow-pane regression: a `10×10` world rect in a `200×800`
    pane (aspect `0.25`) yields `left/right = ±5`, `top/bottom = ±20` — i.e. the
    frustum aspect is the **pane** aspect, not the window's.

## Validation

`node --test dev/src/js-tests/camera-fit.test.mjs`

## Notes

- `_strip_imports` turns `export function …` into `function …` in the bundle, so
  the two exported names become top-level functions available to `fit_camera.js`
  and `js_apply_camera` once they are stripped too.
- Name collision guard: the existing
  `test_bootstrap_has_no_duplicate_top_level_declarations` test will catch any
  accidental duplicate declaration once later phases stop declaring the old
  `_finiteAspect`/`_orthoFrustum2d` names.
