# Phase 8 — Algebra SDF evaluation (JS) + per-`(algebra, distance, opacity)` program cache

**Status:** Planned

## Goal

Implement the frontend algebra-SDF module: evaluate
`embed → M·a → distOf → opacityOf` entirely in the shader, and compile one
program per `(algebra, distance, opacity)` key so shader specialization is
resolved at compile time with **no** algebra/entity/distance/opacity branching
inside the shader.

## Files

- New: `py/pytanga/viz/templates/sdf/algebra/eval.js` (embed snippets + matrix
  uniform upload + program cache)
- New: `py/pytanga/viz/templates/sdf/raymarch-algebra-builder.js` (fragment
  string assembly: common + embed_src + distOf + opacityOf + raymarch body)
- Modify: `py/pytanga/viz/templates/sdf/scene-builder.js` (integrate `mv_sdf`
  objects with analytic objects)

## Shader assembly

```
fragment =
  common_header                        // #version, precision, MAX_DIST, ...
  + primitives/analytic map parts      // only if the scene has analytic objects
  + embed_src(algebra)                 // evalPoint(vec3 p, out float a[NP])
  + matrix_uniform_decls               // uniform float u_M[NP*NR];
  + result_mul                          // r[i] = Σ_j u_M[i*NP+j] · a[j]
  + distOf(distance)                    // selected distance snippet
  + opacityOf(opacity)                  // selected opacity transfer snippet
  + raymarch_body                       // from Phase 2
```

The program key is `"<algebra>:<distance>:<opacity>"` (plus any distance/opacity
params). The `scene-builder` composes multiple `mv_sdf` objects by `opUnion`
over their `distOf` results, each with its own `M` and bound — the same
global-map pattern as analytic objects.

## Steps

- [ ] `eval.js`:
  - [ ] `embedRegistry: Map<algebra, string>` mapping the algebra name to the
        `evalPoint` snippet received from the backend (or a local generated
        snippet) — no algebra branching, lookups only.
  - [ ] `buildAlgebraBody(algebra, distanceName, distanceParams, opacityName,
        opacityParams)` returning the concat fragment section string.
  - [ ] Program cache `Map<key, {program, uniforms}>` keyed by
        `"<algebra>:<distance>:<opacity>"`; on a cache miss compile a new
        `THREE.ShaderMaterial`, on hit reuse.
  - [ ] `uploadMatrix(program, M, NP, NR)` writing `M` into
        `u_M` (flat float uniform in v1).
- [ ] `raymarch-algebra-builder.js`:
  - [ ] Emit `evalPoint` call + `r[] = M·a` matmul + `distOf(...)` call.
  - [ ] Loop bounds `NP`/`NR` are compile-time `#define`s from the algebra
        spec (no dynamic loop indexing issues).
- [ ] `scene-builder.js` integration:
  - [ ] Treat `kind:"mv_sdf"` objects as algebra SDF leaves; `opUnion` with
        analytic objects; assign `matId` for the material table.
  - [ ] Apply the object's `bound` via `opIntersect` for infinite entities.
- [ ] Recompile-on-change:
  - [ ] Distance-function setter (Phase 3/6) and opacity-transfer setter
        (Phase 12) recompute `"<algebra>:<distance>:<opacity>"` keys and
        swap/rebuild affected programs.
  - [ ] Object add/remove re-emits the composed map string and rebuilds the
        affected program(s).

## Verification

- [ ] A single `mv_sdf` object (known entity) renders identically to its
      analytic counterpart (visual + numeric SDF spot-check).
- [ ] Switching distance function recompiles (new program) and updates the
      rendered result.
- [ ] No `if(algebra…)` / `if(distance…)` / `if(opacity…)` constructs remain
      in generated shader source (assert by string inspection).
- [ ] Two different algebras can coexist in the scene (program cache has two
      entries) without shader branching.