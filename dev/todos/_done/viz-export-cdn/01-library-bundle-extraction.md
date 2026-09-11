# Phase 1 — Library bundle extraction (`window.__tanga` bridge)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Goal

Split `generate_bootstrap_js` into a reusable **library** layer
(`generate_library_js`) and the scene-specific **adapter**, exposing the
library's runtime + API through a `window.__tanga` bridge so the adapter can run
against either an inlined library or a CDN-served one.  No public API change;
the inline HTML output must keep working (existing tests stay green).

## Files

- Edit: `py/pytanga/viz/export/_bootstrap/_scene.py`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- Edit: `py/pytanga/viz/export/_bootstrap/__init__.py`
- Edit: `py/pytanga/viz/export/_html.py`
- Edit: `py/pytanga/viz/export/_figure_html.py`
- Edit: `py/pytanga/viz/export/_animated_figure.py`

## Steps

- [x] **1.1 — Runtime import + bridge helpers in `_scene.py`**
  - Add `js_runtime_imports()` that prepends `import * as THREE from 'three';`
    to the existing addons imports (the body of today's `js_imports()`).
  - Add `js_tanga_destructure()` returning the
    `const { THREE, OrbitControls, CSS2DRenderer, CSS2DObject, Line2,
    LineSegments2, LineMaterial, LineGeometry, LineSegmentsGeometry,
    buildSceneObject, buildOverlay, fitCamera, orthoFrustum, finiteAspect }
    = window.__tanga;` line.
  - Add `js_tanga_bridge()` returning the matching `window.__tanga = { … };`
    assignment (same symbol list).
- [x] **1.2 — Source-file list + `generate_library_js()` in `_html.py`**
  - Extract the SDF shader paths from `_sdf_shader_injection()` into a
    `_SDF_SHADER_FILES` constant (the 4 `.glsl` files).
  - Add `library_source_files()` returning the ordered, deduplicated list
    `_RENDERER_FILES + _SHARED_JS_FILES + _SDF_SHADER_FILES` (single source of
    truth for both the bundle and the phase-2 fingerprinting script).
  - Add `generate_library_js()` that concatenates, in order:
    `js_runtime_imports()`, `_sdf_shader_injection()`, a no-op
    `function sendLog() {}` / `function sendEvent() {}` stub, then the JS
    modules `_RENDERER_FILES + _SHARED_JS_FILES` (`_strip_imports`-ed as
    today), then `js_tanga_bridge()`.  The GLSL shaders stay in
    `_sdf_shader_injection()` (JSON), not concatenated as JS.
  - Keep `_strip_imports` unchanged.
- [x] **1.3 — Adapters destructure instead of importing**
  - In `_html.py::_build_static_fullpage_adapter`,
    `_figure_html.py::_build_static_figure_adapter`, and both
    `_animated_figure.py` adapter builders, replace the `js_imports()` call with
    `js_tanga_destructure()`.
  - Remove the now-unused `js_imports` from those modules' imports.
- [x] **1.4 — `generate_bootstrap_js` becomes composition**
  - Change `generate_bootstrap_js(adapter_js)` to return
    `generate_library_js() + "\n\n" + adapter_js`.
- [x] **1.5 — Re-export new helpers**
  - Export `generate_library_js`, `library_source_files`, `js_runtime_imports`,
    `js_tanga_destructure`, `js_tanga_bridge` from `_bootstrap/__init__.py`
    (keep `js_imports` for any remaining callers until phase 4 removes them).

## Validation

`uv run pytest py/tests/viz/test_export_static.py py/tests/viz/test_export_renderers.py py/tests/viz/test_camera_fit_unification.py -q && uv run ruff check py/pytanga/viz/export`

## Notes

- The no-op `sendLog`/`sendEvent` stub fixes the dangling
  `import { sendLog } from '../events.js'` that `_strip_imports` removes today
  (error paths in `factory.js`/`utils.js`/`scene-builder.js` would otherwise
  call an undefined function).
- The adapter becomes byte-identical regardless of how the library is delivered
  (inline vs CDN), which is the point of the bridge.
