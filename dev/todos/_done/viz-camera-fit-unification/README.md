# Camera-fit unification (2D/3D) — Overview

**Created:** 2026-09-01 | **Status:** Done | **Branch:** `fix/2d-camera-fit`

## Goal

Collapse the ortho-camera math from three hand-synced copies into one shared,
pure module, and thread the pane's measured `(width, height)` through every
camera function so no helper reads `window`. This kills the copy-and-drift bug
class that has repeatedly produced 2D-vs-3D camera regressions, and fixes the
reported bug (`fit_camera=True` fitting to the window instead of the pane) as a
direct consequence.

## Architecture (short)

Today the ortho frustum math exists in three places that have already drifted
apart (this is the root of the reported bug):

| Location | Function | Size source |
|----------|----------|-------------|
| `templates/view_mode.js` | `_orthoFrustum()` | reads `window` ❌ |
| `templates/fit_camera.js` | inline 2D aspect math | reads `window` ❌ |
| `export/_bootstrap/_scene.py` | `_orthoFrustum2d()` (Python string) | takes `(w,h)` ✅ |

Plus `finiteAspect` is also triplicated (`_finiteAspect`, `_finiteAspect` in
`fit_camera.js`, `_finiteAspectExport`). The fix extracts **one** pure module
`templates/camera-fit.js` (no `three` import) exporting `finiteAspect` and
`orthoFrustum`, bundles it into the export (`_SHARED_JS_FILES`), and makes the
live viewer, the auto-fit, and the export all call it. Because it is pure, it
is finally unit-testable in Node (the repo has no `three` in Node).

## Decisions (confirmed)

- **One source of truth.** `camera-fit.js` `finiteAspect(width, height)` and
  `orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, width, height)` are
  the only implementations of this math. They are pure: no `window`, no `three`.
- **Canonical size.** `(width, height)` in CSS px is threaded into every camera
  entry point. Entry points may fall back to `window.innerWidth/innerHeight`
  only when the caller omitted the size (legacy/`sdf_viewer.js`); the pure
  helpers never do.
- **`fitCamera` 2D becomes a true contain-fit.** It computes the content
  bounding box (with a 10% margin, preserving the current `1.2` factor), stores
  that **raw** rect in `camera.userData._view2d`, and sets the frustum via
  `orthoFrustum(...)`. This replaces the current "fit the max extent to the
  height, derive width from `aspect`" framing, which is aspect-baked (fragile on
  resize) and clips wide content in narrow panes. **Deliberate behavior change**
  — for square-ish, centered content the frame is visually identical; for
  non-square content it now correctly contains the box on both axes.
- **3D unchanged.** The perspective fit (`fitCamera` 3D branch) and
  `CameraConfig3d` are aspect-independent (radius/fov or explicit placement) and
  are not modified; a regression test pins that.
- **`switchToCamera` drops `viewAspect`** in favour of `viewWidth`/`viewHeight`
  (aspect is derived internally via `finiteAspect`), which is the only caller
  change; `sdf_viewer.js`'s 4-arg call keeps working via defaults.

### Fixed contract

```js
// templates/camera-fit.js  (pure, no `three`)
finiteAspect(width, height);                              // -> number | NaN
orthoFrustum(xmin, xmax, ymin, ymax, uniform, borderPx, width, height);
                                                          // -> {left,right,top,bottom}

// templates/fit_camera.js
fitCamera(sceneObjects, camera, controls, spaceDim, width, height);

// templates/view_mode.js
_applyOrthoFrustum(camera, width, height);
handleResize(camera, renderer, labelRenderer, spaceDim, width, height); // unchanged
switchToCamera(camera, controls, spaceDim, cameraConfig, viewWidth = null, viewHeight = null);
```

```python
# export/_bootstrap/_scene.py
js_autofit_camera(registry_var=..., camera_var=..., controls_var=...,
                  cam_explicit=..., space_dim=..., width_expr=..., height_expr=...)
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-shared-camera-fit-module.md](./01-shared-camera-fit-module.md) | Create pure `camera-fit.js`, bundle it, add a Node unit test. |
| 2 | [02-view-mode-uses-shared-module.md](./02-view-mode-uses-shared-module.md) | `view_mode.js` uses the shared helpers and threads `(width, height)`. |
| 3 | [03-fit-camera-uses-shared-module.md](./03-fit-camera-uses-shared-module.md) | `fit_camera.js` contain-fit via `orthoFrustum`, stores raw rect. |
| 4 | [04-three-view-threads-size.md](./04-three-view-threads-size.md) | `three-view.js` passes the pane size. |
| 5 | [05-export-consolidation.md](./05-export-consolidation.md) | Export `js_apply_camera`/`js_autofit_camera` use the shared module. |
| 6 | [06-regression-tests.md](./06-regression-tests.md) | Automated regression tests pinning the fix. |
| 7 | [07-changelog.md](./07-changelog.md) | Branch changelog (docs last). |

## Testing as you go

- Python: `uv run pytest py/tests/viz/ -q`
- JS unit: `node --test 'dev/src/js-tests/*.test.mjs'`
- JS syntax: `node --input-type=module --check <edited file>`
- Lint: `uv run ruff check py/pytanga/viz/export/`

## Non-goals

- No public Python API changes (`flush(fit_camera=True)` unchanged).
- No change to the 3D perspective fit path or `CameraConfig3d`.
- No collapse of `space_dim` vs `camera.type` (rendering-semantics vs camera
  taxonomy); that is a larger, separate refactor and out of scope here.
- No headless-browser harness; the runtime "squash is gone" check stays a manual
  browser smoke (`src/examples/floating_interactive_v3.py`).
