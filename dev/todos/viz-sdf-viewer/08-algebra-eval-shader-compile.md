# Phase 8 — Algebra SDF evaluation (JS) inside the single composed `map()`

**Status:** Planned

## Goal

Implement the frontend algebra-SDF module: evaluate `embed → M·a → distOf →
opacityOf` entirely in the shader. Each `mv_sdf` object is emitted as an
algebra leaf **inside the existing single composed `map()`** (Phase 5) — not a
separate program per algebra — so mixed-algebra scenes and the existing
combine/material-id fold keep working with **no** algebra/entity/distance/
opacity branching. Recompilation is avoided by distinguishing a program's
*structure* (object kinds / distinct embeds / distance / opacity / combine)
from its *data* (matrix / material / lighting uniforms): structure changes
rebuild the fragment, data-only changes upload uniforms.

## Decision (supersedes the earlier program-cache idea)

The original "one program per `(algebra, distance, opacity)` key" does not fit
the shipped single-quad / single-`ShaderMaterial` renderer: two active programs
would need multi-pass compositing (breaking the single material-id/CSG fold) or
single-algebra scenes (losing mixed-algebra support). Instead **algebra is
per-object data**: each `mv_sdf` leaf carries its own `M` and `bound` and folds
into the one global `map()` like an analytic object. The cache collapses to a
**one-entry (structure vs data)** split:

- **structure key** = `(distance, opacity, set of distinct embed-src identities,
  object count + per-object kind/combine)` → a change rebuilds the fragment.
- **data** = `M` matrices, material rows, lighting → a change only uploads
  uniforms (no recompile).

## Files

- New: `py/pytanga/viz/templates/sdf/algebra/eval.js` (algebra-leaf expression
  emitter: `evalPoint` + `M·a` matmul + `distOf` call + matrix uniform upload)
- New: `py/pytanga/viz/templates/sdf/algebra/embeds.js` (algebra → `evalPoint`
  snippet + `NP`/`NR`/`SLOT_PSEUDO` constants — populated in Phase 7)
- Modify: `py/pytanga/viz/templates/sdf/scene-builder.js` (emit `mv_sdf`
  objects as algebra leaves alongside analytic objects)
- Modify: `py/pytanga/viz/templates/sdf/sdf_viewer.js` (thread `mv_sdf`
  uniforms + the structure-vs-data rebuild split into `rebuildProgram`)

## Shader assembly

The fragment stays one concatenation (`buildFragment()` in `sdf_viewer.js`);
algebra leaves are emitted **inside** `composeObjects()`:

```
fragment =
  common_header                         // #version, precision, MAX_DIST, ...
  + primitives + combinators            // analytic primitive library
  + materialPreamble + materialColorSrc // Phase 5
  + lightPreamble + overlaySrc          // lighting + overlays
  + embed_src(algebra)…                 // one evalPoint per distinct algebra
                                          //   present (deduped by identity)
  + matrix_uniform_decls                 // packed flat u_M[] + u_Scale[] for all mv_sdf
  + composeObjects(objects)              // folds analytic trees AND algebra
                                          //   leaves into one vec2 map()
  + raymarch                             // Phase 2 body (calls map())
```

Each `mv_sdf` leaf expands (in `eval.js`) to:

```
float dist_mv_<i>(vec3 p) {
    float a[NP]; evalPoint<algebra>(p, a);
    float r[NR]; // r[j] = Σ_k u_M[<i>*NP*NR + j*NP + k] · a[k]
    return distOf<distance>(r) * u_Scale[<i>];  // per-object calibration (Phase 9)
}
```

and `composeObjects` folds `dist_mv_<i>` with the object's `combine` mode and
applies `bound` via `opIntersect`, exactly like analytic trees.

## Steps

- [ ] `embeds.js` (Phase 7 output): `Map<algebra, {NP, NR, SLOT_PSEUDO,
      snippet}>`; the snippet is `evalPoint<algebra>(vec3 p, out float a[NP])`.
- [ ] `eval.js`:
  - [ ] `emitAlgebraLeaf(obj, index)` → the `dist_mv_<i>` function body above,
        using the object's `algebra`, `M`, `bound`, and the active distance
        snippet from `distances.js`.
  - [ ] `algebraPreamble(objects)` → emits the deduped `evalPoint` set, the
        `NR`/`NP`/`SLOT_PSEUDO` constants, and the packed `u_M[]` + `u_Scale[]`
        declarations (one flat float array; escalate to a data texture later —
        see README "texture escalation").
  - [ ] `buildAlgebraUniforms(objects)` → packs every `mv_sdf` `M` into the
        flat `u_M` uniform (row-major per object) and every per-object `scale`
        into `u_Scale` (default `1.0`; Phase 9 fills in the calibrated value).
- [ ] `scene-builder.js` integration:
  - [ ] Treat `kind:"mv_sdf"` objects as algebra leaves (delegate to
        `eval.js`), fold them with analytic objects, and assign `matId` for the
        material table (already the `composeObjects` contract).
  - [ ] Apply the object's `bound` via `opIntersect` for infinite entities.
- [ ] `sdf_viewer.js` rebuild split:
  - [ ] Compute the structure key; `rebuildProgram()` only creates a new
        `ShaderMaterial` when the structure key changed.
  - [ ] Data-only changes (matrix/material/lighting/overlay uniforms) update
        the existing material's uniforms in place (no recompile).
  - [ ] Distance/opacity setters (already wired to `rebuildProgram`) now
        change the structure key, so they still recompile.

## Verification

- [ ] A single `mv_sdf` object (known entity) renders identically to its
      analytic counterpart (visual + numeric SDF spot-check).
- [ ] Switching the distance function recompiles and updates the render.
- [ ] Two different algebras coexist in one scene in the **same** `map()` with
      no `if(algebra…)` branching (assert by string inspection).
- [ ] Updating only an object's `M` (same shape) updates uniforms without
      recompiling the shader.
- [ ] No `if(algebra…)` / `if(distance…)` / `if(opacity…)` constructs remain
      in generated shader source (assert by string inspection).
- [ ] A headless Node smoke test compiles the assembled fragment (per algebra +
      distance + opacity) and asserts no GLSL compile errors.
