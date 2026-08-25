# Phase 8 — Algebra SDF evaluation (JS) inside the single composed `map()`

**Status:** Implemented

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

- [x] `embeds.js` (Phase 7 output): `Map<algebra, {NP, NR, SLOT_PSEUDO,
      snippet}>`; the snippet is `evalPoint<algebra>(vec3 p, out float a[NP])`.
- [x] `eval.js`:
  - [x] `emitAlgebraLeaf(obj, info, activeDistance)` → the `dist_mv_<i>`
        function body, using the object's `algebra`, `M`, `bound`, and the
        active distance snippet from `distances.js`.
  - [x] `algebraPreamble` → split into `distinctEmbedSrcs` (deduped `evalPoint`
        set), `matrixUniformDecls` (packed `u_M[]` + `u_Scale[]` declarations,
        `MAX_MV_FLOATS = 1024`; escalate to a data texture later — see README
        "texture escalation"), and `emitDistanceFunctions`.
  - [x] `buildAlgebraUniforms(objects)` → packs every `mv_sdf` `M` into the
        flat `u_M` uniform (row-major per object, stride `NP*NR`) and every
        per-object `scale` into `u_Scale` (default `1.0`; Phase 9 fills in the
        calibrated value).
  - [x] **Decision:** the distance function is instantiated **per distinct
        algebra** (substituting that algebra's `NR`/`SLOT_PSEUDO` and suffixing
        the function name, e.g. `distOfScalarPseudo_E3`), because the result
        vector is the full algebra and `NR`/`SLOT_PSEUDO` are per-algebra. This
        replaces the single-algebra `const int NR/SLOT_PSEUDO` implied by
        `distances.js` (written for the superseded per-program cache).
- [x] `scene-builder.js` integration:
  - [x] Treat `sdfKind:"mv_sdf"` objects as algebra leaves (delegate to
        `eval.js` via `dist_mv_<i>(p)`), fold them with analytic objects, and
        assign `matId` for the material table (the `composeObjects` contract).
  - [x] Apply the object's `bound` via `opIntersect(…, sdBox(p, halfExtents))`
        in the leaf.
- [x] `sdf_viewer.js` rebuild split:
  - [x] Compute the `structureKey` (distance, opacity, per-object
        kind/combine/algebra); `rebuildProgram()` only creates a new
        `ShaderMaterial` when the structure key changed.
  - [x] Data-only changes (matrix/material uniforms) update the existing
        material's uniforms in place (no recompile).
  - [x] Distance/opacity setters (already wired to `rebuildProgram`) change the
        structure key, so they still recompile.

## Verification

- [x] A single `mv_sdf` object (known entity) evaluates a valid SDF — the
      headless numeric spot-check (`test_algebra_sdf_zero_set_matches_plane`)
      confirms the zero-set matches the analytic plane and the distance is
      proportional off it (the residual scale is the Phase 9 calibration
      target). The visual check is the browser slice (Phase 9/10 examples).
- [x] Switching the distance function recompiles (the structure key includes
      `activeDistance`).
- [x] Two different algebras coexist in one scene in the **same** `map()` with
      no `if(algebra…)` branching (asserted in `dev/src/sdf_algebra_smoke.mjs`).
- [x] Updating only an object's `M` (same shape) updates uniforms without
      recompiling (the structure key is independent of the matrix data).
- [x] No `if(algebra…)` / `if(distance…)` / `if(opacity…)` constructs remain in
      generated shader source (asserted by string inspection in both the Node
      smoke and `test_algebra_eval.py`).
- [x] A headless Node smoke test (`dev/src/sdf_algebra_smoke.mjs`) assembles
      the fragment for a single and a mixed-algebra scene and asserts the leaf/
      distance/embed structure and no GLSL identity branching.
