# Part B — Frontend: per-mask distance fn + `vec3 map()` + analytical `|∇d|`

**Status:** Planned · [Overview](README.md) · Depends on: Part A · Feeds: Part C

## Goal

Carry each object's analytical gradient norm `g = scale·|∇d|` through the single
composed `map()` (now returning `vec3(d, m, g)`), and replace the raymarch
finite-difference `calcGradientNorm` with `stepSize = d / max(m.z, 1.0)`. The
distance function is instantiated **per distinct result mask** instead of per
algebra. The derivative uses branchless guards (no `if (rest < eps)`).

## Context

The leaf is `d = D(r)·scale − thickness`, `r = M·a(p)`. The chain rule
`∇d = Jᵀ(Mᵀg)` (see overview "Reference — derivative math") is fully closed-form:
`g[k] = ∂D/∂r[k]`, `h = Mᵀg` (a second matvec over the transposed `M`), and the
per-algebra point Jacobian `J = ∂a/∂p` is a few dot products. This is computed
inside the leaf (no recomputation, no `matId` dispatch) and returned alongside
`d`.

## Design notes

- The leaf returns `vec2(d, g)`; analytic objects contribute `g = 1.0` (a proper
  SDF has `|∇d| = 1`), so `max(1.0, 1.0) = 1.0` keeps their step `= d` (unchanged).
- `map()` returns `vec3(d, m, g)`; the fold threads `g` exactly like `m`.
- The `u_ObjectParams.w` "is algebraic" sentinel is removed (the carried `g`
  already encodes analytic=1.0 vs algebraic).

## Files

- `py/pytanga/viz/templates/sdf/algebra/embeds.js`
- `py/pytanga/viz/templates/sdf/algebra/distances.js`
- `py/pytanga/viz/templates/sdf/algebra/eval.js`
- `py/pytanga/viz/templates/sdf/scene-builder.js`
- `py/pytanga/viz/templates/sdf/composer.js`
- `py/pytanga/viz/templates/sdf/shaders/raymarch.glsl`

## Steps (each individually testable)

### B1 — `embeds.js`: per-algebra gradient, drop `NR`/`SLOT_PSEUDO`

- [x] Remove `NR` and `SLOT_PSEUDO` from each entry (they become per-object wire
      data; keep `NP` + `snippet`).
- [x] Add a `gradient` field per entry: the GLSL `vec3 grad = …` contraction of
      `h[NP]` and `p` (e3/p3: `vec3(h[0],h[1],h[2])`; n3: the `x/y/z·(h[3]+h[4])`
      form; pga3: `vec3(-h[3]-h[6], h[2]+h[5], -h[1]-h[4])`).
- **Verify:** after Part C updates `test_embeds_registry_complete` /
      `test_embed_src_consistency`, the `NP:` and `gradient:` tokens are present
      and `NR:`/`SLOT_PSEUDO:` are gone. (Intermediate: no standalone run — see
      B3.)

### B2 — `distances.js`: document the derivative

- [x] Add a `derivative` field to each entry documenting the `g[k]` formula
      (scalar/pseudo slots → `1.0`; rest → `r[k]·invRest`; `magnitude` →
      `r[k]·invNorm`; `scalar`/`component` → `δ[k,0]`; `grade` → `r[k]·invGrade`
      on the grade). The concrete emission is generated per-mask in `eval.js`
      (B3), where the slot indices are known.
- **Verify:** `test_distance_registry_names_present` still passes; add an
      assertion (Part C) that each entry carries a `derivative` field.

### B3 — `eval.js`: per-mask distance fn + `vec2` leaf with analytical `|∇d|`

- [x] `mvLayout`: `nr = obj.result_ids.length`, `np = entry.NP`,
      `slotPseudo = obj.slot_pseudo` (always valid from Part A); stride `np*nr`.
      No `embeds.js` `NR`.
- [x] `emitDistanceFunctions` (per-mask, dedup key = `result_ids.join(',')`):
      `distOf<Dist>_<suffix>` with per-mask `NR`/`SLOT_PSEUDO` substituted;
      `gradeNorm_<suffix>` uses `const int RESULT_IDS_<suffix>[NR] = int[](…)`
      and `bitCount(RESULT_IDS_<suffix>[i]) == k`.
- [x] `emitAlgebraLeaves`: leaf returns `vec2` — compute `r`, then `d` (via
      `distOf`, scaled + thickness + bound) and `g = scale·length(grad)`, where
      `grad` comes from the inlined derivative (`h[m] = Σₖ u_M[slot(k,m)]·g[k]`
      unrolled) + the per-algebra `gradient` field. Use the branchless guard
      `inversesqrt(rest + float(rest < 1e-6) * 1e-6)` (no `if`).
- [x] `buildAlgebraUniforms`: drop the `-1` sentinel fill (plain `max_distance`
      defaults, analytic objects stay `(0,0,0,0)`).
- **Verify:** `node dev/src/sdf_algebra_smoke.mjs` (update its assertions in
      Part C to match the new leaf/distOf/`vec2` output).

### B4 — `scene-builder.js` + `composer.js`: `vec2`/`vec3`

- [x] `buildObjectExpr`: analytic → `vec2(<treeExpr>, 1.0)`; `mv_sdf` →
      `dist_mv_<i>(p)` (now `vec2`).
- [x] `composeObjects`: `map()` returns `vec3(d, m, g)`; hard folds take the
      winner's `g`; `smooth_*` folds `mix` `g` with `sm.y` like `m`;
      `subtract`/`smooth_subtract` keep the positive accumulator's `g`.
- **Verify:** `node dev/src/sdf_composer_smoke.mjs` (update `vec2 map` →
      `vec3 map` assertion in Part C).

### B5 — `raymarch.glsl`: consume `m.z`, delete the finite-difference step

- [x] `vec3 m = map(p)`; `d = m.x`; `stepSize = d / max(m.z, 1.0);` (unconditional).
- [x] Delete `calcGradientNorm` and the `u_ObjectParams.w > -0.5` gate.
- [x] Keep `mapDensity(d, m.y)`, `calcNormal`, `softShadow`, `shade`, halo on
      their `.x`/`.y` reads (now on a `vec3`).
- **Verify:** after Part C updates `test_raymarch_shader.py` (no
      `calcGradientNorm`, `stepSize = d / max(m.z, 1.0);`, no sentinel gate).

## Verification

- [ ] `node dev/src/sdf_algebra_smoke.mjs && node dev/src/sdf_composer_smoke.mjs`
- [ ] The generated fragment (string-inspected) contains no `if (rest` /
      `if (rest <` epsilon branch and no `calcGradientNorm`.
- [ ] Analytical `|∇d|` matches `calibration.gradient()` to ~1e-9 for the demo
      entities (numeric spot-check; see overview baselines).
