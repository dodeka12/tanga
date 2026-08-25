# Phase 4 — Factory wiring, update/rebuild, WebGL2 fallback

## Goal

Register the SDF proxy in the standard render pipeline so `kind:"sdf"` objects
flow through the same scene-graph construction, update, and removal paths as
mesh objects, with a WebGL2 gate and a mesh fallback.

## Files

- Modify: `py/pytanga/viz/templates/renderers/factory.js` — `case "sdf"` in
  `createEntityMesh` and `updateEntityMesh`.
- Modify: `py/pytanga/viz/templates/renderers/utils.js` — `tagEntity` /
  `applyStyleUpdate` / `entityRequiresRebuild` for SDF.
- Modify: `py/pytanga/viz/templates/scene-builder.js` — confirm `buildSceneObject`
  treats `kind:"sdf"` like any scene object (transform wrap + parent + registry).
- Modify: `py/pytanga/viz/templates/views/three-view.js` — WebGL2 detection +
  per-object fallback decision.

## Steps

- [x] **4.1 — `factory.js` dispatch**
  - `case "sdf":` → `createSdfProxy(ent)`. Keep `ent.sdfKind` on
    `mesh.userData` for diagnostics and `tagEntity`.
  - `updateEntityMesh` routes SDF updates to `updateSdfProxy` (transform →
    mutate `obj.position`/`rotation`/`scale`; style → re-apply `uColor`/
    `uOpacity`/`uMaxSteps`; `tree`/`bound` change → rebuild).

- [x] **4.2 — Update semantics**
  - `entityRequiresRebuild(ent, prev)`: `true` when `tree`/`bound`/`sdfKind`
    changed, `false` for transform/style-only changes (no shader recompile for
    animation).
  - `applyStyleUpdate`: update `uColor`/`uOpacity` uniforms in place
    (`material.needsUpdate` not required for uniform-only changes).

- [x] **4.3 — Disposal**
  - Reuse the existing `removeEntityMesh` traversal (disposes geometry +
    material). Verify `ShaderMaterial.dispose()` releases the GLSL program.

- [x] **4.4 — WebGL2 gate + fallback**
  - On WebGL1, SDF objects are skipped and a single yellow warning banner is
    shown (per decision: no mesh equivalent — the wire contract has no mesh
    fields); the standard mesh pipeline keeps working.
  - `three-view.js` detects `renderer.capabilities.isWebGL2`. On WebGL1, SDF
    objects fall back to the normal mesh renderer (build the mesh equivalent
    from `ent.sdfKind` via the existing per-kind renderer) and log one console
    warning. Meshes keep working on WebGL1.

- [x] **4.5 — Validate**
  - `node --input-type=module --check` on all touched JS.
  - `uv run pytest py/tests/viz/ -q` (frontend-shape regression: the factory
    dispatch table and scene-builder contract checks).

## Validation

`node --input-type=module --check` on touched JS + `uv run pytest py/tests/viz/ -q`
(frontend-shape / serialization regression). Browser smoke deferred to Phase 5.

## Notes

- The transform update path (`updateEntityMesh` → `obj.position.set(...)`) is
  what makes SDF objects animate/scale/rotate without recompiling the shader —
  this depends on Phase 2's local-space emission.
