# Phase 1 — SDF primitive + combinator GLSL library

**Status:** Done

## Goal

Create the GLSL base library of signed-distance primitives and Boolean
combinators, ported from inigo quilez's SDF reference. This is the "base
modules" vocabulary every analytic entity builds on, and the fallback
primitives for bounded infinite entities.

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

- [x] Add `primitives.glsl` with the primitive set:
  - [x] `sdSphere`, `sdEllipsoid`
  - [x] `sdBox`, `sdRoundBox`
  - [x] `sdPlane` (infinite; used only with an explicit bound in later phases)
  - [x] `sdSegment` (rounded line), `sdCapsule` (two-point)
  - [x] `sdCylinder` (infinite), `sdCappedCylinder`
  - [x] `sdCone` (infinite), `sdCappedCone`
  - [x] `sdTorus`
- [x] Add `combinators.glsl`:
  - [x] `opUnion`, `opSubtract`, `opIntersect` (min/max forms with exact
        distance signs preserved)
  - [x] `opSmoothUnion`, `opSmoothSubtract`, `opSmoothIntersect` (vec2 blend)
- [x] Add a small `sdf_common.glsl` header for shared constants
      (`SDF_EPSILON`, `MAX_DIST`) and the IQ rotation helpers if needed.

## Verification

- [x] Both files contain no accidental `main()` and are valid GLSL ES 3.0 on
      inspection (they will only compile once the raymarcher concatenates
      them in Phase 2).
- [x] Primitive formulas cross-checked against IQ reference for argument order
      and sign conventions.
- [ ] A headless compile smoke check (e.g. `glslangValidator` or a Node
      `three` shader-probe harness) parses `primitives.glsl` +
      `combinators.glsl` with no syntax errors. *(deferred to Phase 2, which
      compiles the assembled shader via a Node+`three` harness — no
      `glslangValidator`/`glslc` installed locally)*
