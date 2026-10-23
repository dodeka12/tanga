# Phase 5 — Shader compile error reporting

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (the `client_log` /
> `sendLog` → `on_client_log` channel) and `py/pytanga/viz/templates/sdf/sdf_viewer.js`
> (`formatShaderError` + `renderer.debug.onShaderError`).  This reuses the
> existing `sendLog` channel; no new wire protocol is introduced.

## Goal

Capture every shader compile/link failure in the **main** viewer, format the
driver log with source context, and send it to the backend as a
`source: "shader"` client-log record; expose `Visualizer.on_shader_error(handler)`
so apps can show a banner.

## Files

- **New** `py/pytanga/viz/templates/renderers/shader-error.js`
- **Edit** `py/pytanga/viz/templates/views/three-view.js`
- **Edit** `py/pytanga/viz/visualizer.py` — `on_shader_error`
- **Edit** `py/pytanga/viz/templates/sdf/sdf_viewer.js` (optional refactor)
- **New** `js/dev/tests/shader-error.test.mjs`
- **Edit** `py/tests/viz/test_client_log.py` (extend, or a small new test)

## Steps

- [x] **5.1 — `renderers/shader-error.js`**
  - Extract `formatShaderError(gl, shader, type)` from `sdf_viewer.js` (driver log + `ERROR: 0:<line>` parse + ±6 lines of context) into a shared module.
  - Add `installShaderErrorHook(renderer, onError)` that sets `renderer.debug.onShaderError = (gl, program, vs, fs) => { const err = formatShaderError(...); onError(err); }` (and returns an uninstall function).
  - Keep the module pure/importable in both the live viewer and (optionally) `sdf_viewer.js`.

- [x] **5.2 — hook the main viewer (`three-view.js`)**
  - After `new THREE.WebGLRenderer(...)` succeeds, call `installShaderErrorHook(this.renderer, (err) => sendLog('error', 'Shader compile failed', { source: 'shader', data: { error: err } }))`.
  - Import `installShaderErrorHook` (and `sendLog`, already imported) into `three-view.js`.  This one hook covers ray / SDF / depth / image / surface shaders.

- [x] **5.3 — `Visualizer.on_shader_error(handler)`**
  - Add `on_shader_error(self, handler)` next to `on_client_log`: store the handler and register a filter that, for a `ClientLogRecord` with `record.source == "shader"`, calls `handler(record, event)`; for other records, delegate to the existing `on_client_log` sink (or the default sink).

- [x] **5.4 — tests**
  - `js/dev/tests/shader-error.test.mjs`: `formatShaderError` with a fake `gl` (`getShaderInfoLog` returning `ERROR: 0:5: ...`, `getShaderSource` returning 10 lines) returns a string containing the `>` marker on line 5 and the surrounding context.
  - Extend `py/tests/viz/test_client_log.py` (or add a focused test): `on_shader_error` fires only for `source == "shader"` records and leaves the default sink for others.

## Validation

```bash
node js/dev/tests/check-syntax.mjs
node --test js/dev/tests/shader-error.test.mjs
uv run pytest py/tests/viz/test_client_log.py -q
uv run python tools/build-viewer-js.py --check
```

## Notes

- `renderer.debug.onShaderError` is the single global hook in three.js r168/r170;
  shader programs compile lazily on first render, so a broken custom surface
  shader is caught when the surface first draws (the banner example in phase 6
  relies on this).
