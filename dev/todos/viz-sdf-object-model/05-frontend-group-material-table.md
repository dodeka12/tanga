# Phase 5 — Per-object materials: `vec2 map()` + material table

## Goal

Give multi-member SDF objects (`Combine`/`Composed`/`SdfGroup`) an independent
color/opacity **per member**. The group proxy switches from `float map()` to
`vec2 map()` returning `(distance, materialIndex)`, backed by a `uMaterial`
uniform table. Single-member objects keep `float map()` + single `uColor`/
`uOpacity` (no regression).

## Files

- Modify: `templates/renderers/sdf/glsl.js` — `buildGroupMap()` emits `vec2 map`
  + material propagation; add the material-table preamble.
- Modify: `templates/renderers/sdf/proxy.glsl` — shade using the hit material.
- Modify: `templates/renderers/sdf.js` — build/update `uMaterial`; hover per
  material.
- Modify: `templates/sdf/shaders/combinators.glsl` (or inline) — `opXor`.
- Modify: `dev/src/sdf_proxy_smoke.mjs` — assert `vec2 map` + material table.

## Steps

- [ ] **5.1 — `vec2 map` + material propagation** (`glsl.js`)
  - `buildGroupMap` becomes `vec2 map(vec3 p) { ... }` folding members inline:
    union `if (di.x < d.x) { d = di; m = i; }`; subtract `if (-di.x > d.x) {
    d.x = -di.x; m = i; }`; intersection `if (di.x > d.x) { d = di; m = i; }`.
  - Emit `const int MAX_GROUP_MEMBERS = …; uniform vec4 uMaterial[MAX_GROUP_MEMBERS];`
    when the object has a `materials` array.
  - Keep the single-object `float map` path untouched.

- [ ] **5.2 — Material lookup in the shader** (`proxy.glsl`)
  - The shade reads `map(p)` once, uses `.x` for distance/normal/shadow, and
    colors the hit with `uMaterial[int(m)].rgb` / opacity `.a`.
  - `calcNormal`/`softShadow` use `map(p).x` (material index discarded).

- [ ] **5.3 — `uMaterial` build/update** (`sdf.js`)
  - `_buildUniforms` adds `uMaterial` (padded to `MAX_GROUP_MEMBERS`, reuse the
    `material-table.js` color/opacity packing) when `ent.materials` is present.
  - `updateSdfProxy` updates the table in place (reuse `padMaterialRows`-style
    padding).

- [ ] **5.4 — Hover per material** (`sdf.js` / `proxy.glsl`)
  - `uHover` emissive + `hover_opacity` apply to the *hit* material (`col +=
    uHover; opacity *= hover_opacity` after the material lookup) instead of a
    single `uColor`.

- [ ] **5.5 — `opXor`** (`combinators.glsl`)
  - Add `float opXor(float a, float b) { return min(max(a, -b), max(b, -a)); }`
    (symmetric difference; binary-only).

- [ ] **5.6 — Smoke/unit tests**
  - `dev/src/sdf_proxy_smoke.mjs`: a multi-member ent asserts `vec2 map(`, the
    `uMaterial` declaration, and material-index propagation; a single-member ent
    still asserts `float map(`.
  - `node --test 'dev/src/js-tests/*.test.mjs'` (pure GLSL assembly helpers).

- [ ] **5.7 — Validate**
  - `node dev/src/sdf_proxy_smoke.mjs` + `node --test 'dev/src/js-tests/*.test.mjs'`
    + `uv run pytest py/tests/viz/ -q`.

## Validation

`node dev/src/sdf_proxy_smoke.mjs` (green) +
`node --test 'dev/src/js-tests/*.test.mjs'` (green) +
`uv run pytest py/tests/viz/ -q` (green).

## Notes

- **Performance:** the march cost is unchanged; the only additions are a
  compare/select per fold (material propagation) and one `uMaterial` fetch per
  fragment — a few percent at most, zero for single-material objects.
- The material index == member index (serialization order), matching the Phase 4
  `materials` array contract.
