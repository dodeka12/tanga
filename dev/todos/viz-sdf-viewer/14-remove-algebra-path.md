# Phase 14 — Remove the algebra (`mv_sdf`) rendering path; restore & optimize the analytic path

**Status:** Planned

## Goal

Remove the algebra (raw-MV / `mv_sdf`) rendering path added in Phases 7–13, and
restore the SDF viewer to a single, fast, proper-SDF rendering path for the
standard geometric objects (entities, operators, `SdfNode`, `Composed`).

The algebra path turned every raw MV into its own per-object shader "renderer"
(a `dist_mv_<i>` leaf doing `evalPoint → M·a → distOf` plus, since Phase 13, a
closed-form gradient `Mᵀg`/Jacobian) and widened the shared raymarcher to a
`vec3 map()` with a `d / max(|∇d|, 1)` step rule and a volumetric
`mapDensity`/Beer–Lambert path. That machinery compiles and runs even when it is
not needed, and — as observed — it is slow and does not work in general. This
phase deletes all of it and returns the viewer to the Phase 6 analytic baseline:
one composed, inlined `map()`, plain IQ sphere-tracing (`t += d`), and no
per-object matrix/function/uniforms.

## Decisions (locked)

1. **Raw MVs route through `geometry.analyze()`** (the standard viewer's
   behaviour). A raw MV that `analyze()` recognises renders through the analytic
   path as a geometric entity/operator; an unrecognisable MV raises a clear
   `TypeError`/`ValueError`. No `M·a` matrix evaluation remains.
2. **Remove the opacity transfer axis** (`step`/`linear`/`sigmoid`) along with
   the algebra path. Keep the per-object `opacity` (alpha) already carried by the
   material table (`materialColor().a`); the `linear`/`sigmoid` soft-edge
   semantics were defined around the algebra distance field and are not needed
   for hard geometric surfaces.
3. **Keep** everything the analytic path already shares: `color`, `opacity`
   (alpha), `size`, `thickness`, `style`, `combine`/`polarity`, `smoothness`,
   `SdfNode`, `Composed`, lights, overlays, and the composed-material table.

## Background — why it is slow

- `templates/sdf/algebra/eval.js` emits one `dist_mv_<i>(vec3 p)` function per
  `mv_sdf` object, plus per-result-mask `distOf*` functions, plus a flat
  `u_M[]` uniform and a `u_ObjectParams[]` uniform.
- Each leaf does a point embedding, a matrix-vector multiply, a distance
  function, and (Phase 13) an analytical gradient `g[k] = ∂D/∂r[k]`,
  `h = Mᵀg`, and a per-algebra point Jacobian.
- `composeObjects` was widened to `vec3 map()` returning `(d, materialId,
  gradientNorm)`, and `raymarch.glsl` steps `d / max(m.z, 1.0)` and integrates a
  volumetric density (`mapDensity`, `transmittance`, halo) driven by
  `u_ObjectParams`.
- None of this exists for the analytic path, whose objects are inlined into one
  `map()` expression returning `vec2(d, materialId)`.


## Files

### Delete — backend

- `py/pytanga/viz/sdf/algebra_embedding.py` (Phase 7 backend)
- `py/pytanga/viz/sdf/calibration.py` (Phase 9 calibration/validation)
- `py/pytanga/viz/sdf/distance.py` (Phase 3 distance-function registry)
- `py/pytanga/viz/sdf/opacity.py` (Phase 12 opacity-transfer registry)

### Delete — frontend

- `py/pytanga/viz/templates/sdf/algebra/` (the whole directory):
  `eval.js`, `embeds.js`, `distances.js`, `opacities.js`

### Delete — tests / dev / examples

- `py/tests/viz/sdf/test_algebra_embedding.py`
- `py/tests/viz/sdf/test_algebra_eval.py`
- `py/tests/viz/sdf/test_calibration.py`
- `py/tests/viz/sdf/test_distance.py`
- `py/tests/viz/sdf/test_opacity.py`
- `dev/src/sdf_algebra_smoke.mjs`
- `py/examples/viz/demo_sdf_algebra.py`
- `py/examples/viz/demo_sdf_opacity.py`

### Modify — backend

- `py/pytanga/viz/sdf/serializer.py`
- `py/pytanga/viz/sdf/visualizer.py`
- `py/pytanga/viz/sdf/__init__.py`

### Modify — frontend

- `py/pytanga/viz/templates/sdf/scene-builder.js`
- `py/pytanga/viz/templates/sdf/composer.js`
- `py/pytanga/viz/templates/sdf/sdf_viewer.js`
- `py/pytanga/viz/templates/sdf/shaders/raymarch.glsl`

### Modify — tests

- `py/tests/viz/sdf/test_combine.py`
- `py/tests/viz/sdf/test_visualizer.py`
- `py/tests/viz/sdf/test_raymarch_shader.py`
- `dev/src/test_viz_sdf.py`

### Modify — docs

- `docs/py/viz/sdf-viewer.md`
- `docs/changelog/2026-08-22_feat-sdf-viewer.md` (add a `## Breaking Changes` entry)
- `dev/todos/viz-sdf-viewer/README.md` (mark phases 03/07–13 superseded — optional)

## Steps

### A. Backend removal

- [x] Delete `py/pytanga/viz/sdf/algebra_embedding.py`, `calibration.py`,
      `distance.py`, `opacity.py`.
- [x] `py/pytanga/viz/sdf/serializer.py`:
  - [x] Remove `from .algebra_embedding import embed_entity_mv` and the
        `from pytanga.algebra import MV` import.
  - [x] Remove the `serialize_mv(...)` function.
  - [x] In `serialize_entity`, drop the `if isinstance(entity, MV): return
        serialize_mv(...)` branch. After this change `serialize_entity` accepts
        entities/operators/`SdfNode`/`Composed` only; raw MVs are resolved by the
        caller (see `SdfVisualizer._resolve`) before reaching it.
  - [x] In `_composed_tree`, resolve MV constituents via `geometry.analyze()`
        before serializing (so `Composed` can still contain a raw MV).
- [x] `py/pytanga/viz/sdf/visualizer.py`:
  - [x] Remove `from .distance import DistanceFunction` and
        `from .opacity import OpacityTransfer`.
  - [x] Remove `self._distance` / `self._opacity` and the `distance`/`opacity`
        properties + setters.
  - [x] Remove `_warn_signedness()` and its two call sites in `add`/`update_entity`.
  - [x] Remove the algebra-only `add`/`update_entity`/`_build_props` kwargs:
        `bound`, `normalize`, `calibrate`, `falloff`, `max_distance` (keep
        `size`, `thickness`, `style`, `combine`, `polarity`, `smoothness`,
        `color`, `opacity`).
  - [x] Rewrite `_resolve` to mirror the standard viewer: pass through
        `SdfNode`/`Composed`/`GeoEntity`/`GeoOperator` unchanged; resolve
        everything else (raw MVs) via `pytanga.geometry.analyze()` and raise a
        clear error when `analyze()` returns `None`.
  - [x] `_push_config`: drop the `"distance"` and `"opacity"` keys; keep
        `**self._lighting_dict()` and `"overlays"`.
- [x] `py/pytanga/viz/sdf/__init__.py`:
  - [x] Remove imports of `algebra_name`, `embed_entity_mv`, `embed_src`,
        `calibrate_scale`, `distance_value`, `evaluate_sdf`, `find_surface_point`,
        `gradient`, `gradient_norm`, `scale_at`, `serialize_mv`,
        `DistanceFunction`, `DistanceFunctionMeta`, `OpacityTransfer`.
  - [x] Remove the matching `__all__` entries (keep the primitives, overlay,
        lights, `Composed`, `SdfNode`, `SdfVisualizer`, `serialize_entity`).

**Verify:** `uv run python -c "import pytanga.viz.sdf"` imports cleanly;
`uv run pytest py/tests/viz/sdf -q` (expect the still-algebra tests to fail
until Step C).

### B. Frontend removal

- [x] Delete `py/pytanga/viz/templates/sdf/algebra/`.
- [x] `templates/sdf/scene-builder.js`: remove the `obj.sdfKind === 'mv_sdf'`
      branch and the `dist_mv_<i>` delegation; always `return
      vec2(${emitTree(obj.tree)}, 1.0);`.
- [x] `templates/sdf/composer.js`: change `map()` to return `vec2(d, m)`; delete
      the `g` gradient-norm accumulator and every `g`/`d${i}.y` threading line
      (material `m` selection stays).
- [x] `templates/sdf/sdf_viewer.js`:
  - [x] Remove the algebra imports (`distinctEmbedSrcs`, `matrixUniformDecls`,
        `mvLayout`, `emitDistanceFunctions`, `emitAlgebraLeaves`,
        `buildAlgebraUniforms`) and the `opacityFuncs` import.
  - [x] Remove `activeDistance` / `activeOpacity` module state.
  - [x] In the fragment assembly, drop the algebra preamble lines
        (`distinctEmbedSrcs`, `matrixUniformDecls`, `emitDistanceFunctions`,
        `emitAlgebraLeaves`) and the opacity-function emission.
  - [x] In the uniform build/apply, drop `u_M` and `u_ObjectParams`.
  - [x] Drop `warnUnsignedBooleans` and its call site.
  - [x] In `structureKey`, drop the `distance`/`opacity`/`alg` components
        (`mv_sdf`/`algebra`/`smoothness` that only applied to algebra).
  - [x] In the `sdf_viewer_config` message handler, drop the `distance` and
        `opacity` handling.
- [x] `templates/sdf/shaders/raymarch.glsl`:
  - [x] March loop: `vec2 m = map(p); float d = m.x;` and step `t += d;`
        (delete `m.z`, `stepSize = d / max(m.z, 1.0)`).
  - [x] Delete `mapDensity`, the `u_ObjectParams` reads, and the
        `transmittance`/`haloMatId`/`maxSigma` volumetric accumulation; simplify
        the miss path to plain background colour.
  - [x] `shade`: replace `col *= opacityOf(map(p).x, surfaceOpacity);` with
        `col *= surfaceOpacity;` (alpha comes from `materialColor().a`).
  - [x] Keep `calcNormal` (reads only `.x`), `softShadow`, `shade`, `main`,
        `SDF_EPSILON`/`MAX_DIST`.

**Verify:** after Step C, `uv run pytest py/tests/viz/sdf/test_raymarch_shader.py -q`;
brace balance holds; no reference to `mapDensity`/`u_ObjectParams`/`u_M`/
`mv_sdf` remains in `templates/sdf/`.

### C. Tests / dev / examples

- [ ] Delete the four algebra test files and `dev/src/sdf_algebra_smoke.mjs`.
- [ ] `py/tests/viz/sdf/test_combine.py`:
  - [ ] Remove `test_combine_serialized_mv_sdf`, `test_distance_signed_property`,
        `test_signedness_gate`, `test_signedness_gate_silent_when_signed`,
        `test_frontend_signedness_gate_present`, `test_smooth_subtract_signedness_gate`.
  - [ ] Remove now-unused imports (`DistanceFunction`, `BasisPGA3`,
        `create_entity`, `Direction`/`Plane`, `serialize_mv`).
- [ ] `py/tests/viz/sdf/test_visualizer.py`:
  - [ ] Remove `test_distance_setter_emits_config_value` (distance/opacity gone).
  - [ ] Add a test that `SdfVisualizer.add(plane_mv)` now serializes an analytic
        `box`/`Plane` tree (MV resolved through `analyze`).
  - [ ] Add a test that an un-analysable object raises a clear error.
- [ ] `py/tests/viz/sdf/test_raymarch_shader.py`:
  - [ ] Remove `test_volumetric_density_present`, `test_algebra_local_gradient_step`,
        `test_raymarch_opacity_step_treats_hit_band_as_opaque`.
  - [ ] Update `test_raymarch_map_and_material_contract` to assert the body calls
        `map(p)` (`.x`), never defines `vec2 map(`, and steps `t += d`.
  - [ ] Update `test_combined_fragment_is_brace_balanced` (unchanged inputs).
  - [ ] Add assertions: no `u_ObjectParams`, no `mapDensity`, no `m.z` in the
        assembled fragment.
- [ ] `dev/src/test_viz_sdf.py`:
  - [ ] Remove `test_algebra_path_and_calibration`, `test_distance_and_opacity_setters`,
        and the raw-plane `add` in `test_server_boot_and_flush`.
  - [ ] Keep the analytic sphere, combine/smooth round-trip, and server boot
        smoke steps.

**Verify:** `uv run pytest py/tests/viz/sdf -q` fully green.

### D. Docs / changelog

- [ ] `docs/py/viz/sdf-viewer.md`: remove the algebra half of "Two rendering
      paths", "Distance functions", "Rendering the algebra field", and "Soft
      opacity"; update the examples table (drop `demo_sdf_algebra.py` /
      `demo_sdf_opacity.py`).
- [ ] `docs/changelog/2026-08-22_feat-sdf-viewer.md`: add a
      `## Breaking Changes` bullet describing the algebra-path and opacity-axis
      removal (raw MVs now route through `analyze`; `distance`/`opacity`/
      `calibrate`/`falloff`/`max_distance`/`normalize`/`bound` MV props removed).
- [ ] `dev/todos/viz-sdf-viewer/README.md`: mark phases 03 and 07–13 as
      superseded by this phase (optional, historical).

**Verify:** build the docs (`uv run mkdocs build` if available) or eyeball the
rendered markdown.

## Verification (full)

- [ ] `uv run pytest py/tests/viz/sdf -q` — all green.
- [ ] `uv run pytest py/tests/viz -q` — no regressions in the broader viz suite.
- [ ] `uv run python dev/src/test_viz_sdf.py` — analytic smoke passes.
- [ ] Grep for leftovers: `mv_sdf`, `serialize_mv`, `embed_entity_mv`,
      `calibrate_scale`, `DistanceFunction`, `OpacityTransfer`, `u_ObjectParams`,
      `u_M`, `mapDensity`, `dist_mv_` return nothing under `py/pytanga/viz/sdf/`
      and `py/pytanga/viz/templates/sdf/` (docs/changelog/todos may retain
      historical mentions).
- [ ] Manual browser check: `uv run python py/examples/viz/demo_sdf_entities.py`
      and `demo_sdf_composed.py` render correctly and at full speed.

