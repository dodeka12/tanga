# Phase 1 — SDF primitive + combinator GLSL library

**Status:** Planned

## Goal

Create the GLSL base library of signed-distance primitives and Boolean
combinators, ported from inigo quilez's SDF reference. This is the "base
modules" vocabulary every analytic entity and operator builds on, and the
fallback primitives for bounded infinite entities.

## Files

- New: `py/pytanga/viz/templates/sdf/shaders/primitives.glsl`
- New: `py/pytanga/viz/templates/sdf/shaders/combinators.glsl`

## Conventions

- GLSL ES 3.0 (`#version 300 es`) with `float`-typed distances and `precision
  highp float;`.
- Each primitive is a `float sd<Name>(…)` function with the **local** point as
  first argument; combinators take two distances and return a `float`.
- Primitives follow IQ naming: `sdSphere`, `sdBox`, `sdRoundBox`,
  `sdCylinder`, `sdCappedCylinder`, `sdCone`, `sdCappedCone`, `sdTorus`,
  `sdEllipsoid`, `sdPlane`, `sdSegment` (rounded line).
- Combinators: `opUnion`, `opSubtract`, `opIntersect`, `opSmoothUnion`,
  `opSmoothSubtract`, `opSmoothIntersect`.
- Smooth combinators return a 2-float result (`vec2`) carrying the blend
  factor (`d.x`) and the material/discontinuity factor (`d.y`), matching IQ's
  `opSmooth*` pattern so material-ID tracking can reuse the blend value later.

## Steps

- [ ] Add `primitives.glsl` with the primitive set:
  - [ ] `sdSphere`, `sdEllipsoid`
  - [ ] `sdBox`, `sdRoundBox`
  - [ ] `sdPlane` (infinite; used only with an explicit bound in later phases)
  - [ ] `sdSegment` (rounded line), `sdCapsule` (two-point)
  - [ ] `sdCylinder` (infinite), `sdCappedCylinder`
  - [ ] `sdCone` (infinite), `sdCappedCone`
  - [ ] `sdTorus`
- [ ] Add `combinators.glsl`:
  - [ ] `opUnion`, `opSubtract`, `opIntersect` (min/max forms with exact
        distance signs preserved)
  - [ ] `opSmoothUnion`, `opSmoothSubtract`, `opSmoothIntersect` (vec2 blend)
- [ ] Add a small `sdf_common.glsl` header for shared constants
      (`SDF_EPSILON`, `MAX_DIST`) and the IQ rotation helpers if needed.

## Verification

- [ ] Both files contain no accidental `main()` and are valid GLSL ES 3.0 on
      inspection (they will only compile once the raymarcher concatenates
      them in Phase 2).
- [ ] Primitive formulas cross-checked against IQ reference for argument order
      and sign conventions.