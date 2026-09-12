# Phase 6 — General analytic "ray" renderer framework

## Goal

A *general* style-selected analytic renderer, structurally a sibling of the existing
SDF proxy: a `RayStyle` marker routes an entity to `kind:"ray"`, the frontend builds
a bounding-box proxy mesh with an analytic fragment shader writing `gl_FragDepth`
(depth-composites with meshes and SDF proxies).

## Files

- New: `py/pytanga/viz/_styles/_ray_style.py` (`RayStyle`)
- Modify: `py/pytanga/viz/_styles/__init__.py`
- Modify: `py/pytanga/viz/serializer.py` (`_is_ray_styled` + ray branch)
- New: `py/pytanga/viz/templates/renderers/ray.js` (`createRayProxy`, `updateRayProxy`)
- New: `py/pytanga/viz/templates/renderers/ray/intersect.glsl` (analytic entry point)
- Modify: `py/pytanga/viz/templates/renderers/factory.js` (`case 'ray'`)
- Modify: `py/pytanga/viz/export/_bootstrap/_html.py` (`_RENDERER_FILES`)
- New: `py/tests/viz/test_ray_styles.py`, `py/tests/viz/test_ray_renderer.py`

## Steps

- [x] **6.1 — `RayStyle`** — `RayStyle(VizStyle)` marker with `color`, `opacity`
  (both `None`) + `bound_padding`; `to_dict()` → `{"style_type": "RayStyle", …}`.
  Export from `pytanga.viz`.

- [x] **6.2 — `_is_ray_styled` + dispatch** — mirror `_is_sdf_styled`
  (per-entity `RayStyle` in `props` OR per-kind `RayStyle` in `styles_map`); add a
  ray branch in `_dispatch_entity` **before** the SDF/mesh branches.

- [x] **6.3 — `ray.js` proxy** — `createRayProxy(ent)` builds a BoxGeometry +
  `ShaderMaterial` (like `sdf.js`), a generic `intersect` function dispatcher, and
  writes `gl_FragDepth`; `updateRayProxy` applies transform/style in place.

- [x] **6.4 — capability map** — a Python-side table mapping entity kind → supported
  renderer kinds (`mesh`/`sdf`/`ray`); the serializer checks it so an unsupported
  combination raises a clear error.

- [x] **6.5 — factory + export** — `factory.js` `case 'ray': createRayProxy` +
  `updateEntityMesh` branch; register `ray.js` + `ray/intersect.glsl` in
  `_RENDERER_FILES`.

- [x] **6.6 — Tests**
  - `RayStyle.to_dict()` and `_is_ray_styled` resolution (per-entity and per-kind).
  - Capability map: `Quadric3D` supports `ray` only; unsupported combo raises.
  - `node --input-type=module --check` on `ray.js`, `factory.js`.
  - `uv run pytest py/tests/viz/test_export_renderers.py -q`.

- [x] **6.7 — Validate** — `uv run pytest py/tests/viz/test_ray_styles.py
  py/tests/viz/test_ray_renderer.py py/tests/viz/test_export_renderers.py -q`.

## Validation

`uv run pytest py/tests/viz/test_ray_styles.py py/tests/viz/test_ray_renderer.py py/tests/viz/test_export_renderers.py -q`

## Notes

- The ray proxy is generic; per-object analytic intersect functions (quadric now,
  others later) plug into the `intersect` dispatcher.
- `RayStyle` is the base marker; `RayQuadricStyle` arrives in Phase 7.
