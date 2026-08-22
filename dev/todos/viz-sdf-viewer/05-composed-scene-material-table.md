# Phase 5 — Composed global SDF + material-ID hit tracking

**Status:** Done (union fold + material-ID tracking + material table)

## Goal

Combine all per-object SDF subtrees into a **single** global SDF function
(`min`/`max` fold over objects with per-object combine modes) and track which
object each ray hit, so color/opacity can be applied per object in one
ray-march pass.

## Background

Because all objects share one SDF, the raymarcher evaluates one function per
step. We need two outputs from that function:
1. the combined **distance**, and
2. the **material id** (object index) at the current sample, so the shader can
   blend colors correctly on the smoothed boundaries.

This mirrors IQ's "combining materials" technique: distance combinators carry
a second channel (`mat`) using their blend factor.

## Files

- New: `py/pytanga/viz/templates/sdf/composer.js` (fold per-object expressions
  into one global `vec2 map(vec3 p)`)
- New: `py/pytanga/viz/templates/sdf/material-table.js` (color/opacity table
  upload + sampler)

*(`scene-builder.js` + `objects/*` landed in Phase 4.)*

## Steps

- [x] Extend the SDF evaluation to return `vec2(distance, matId)`; the
      composed `map(vec3 p)` returns the minimum distance over all objects plus
      the winner's 0-based `materialId` (assigned by serialization order).
- [x] Global `vec2 map(vec3 p)` (`composer.js`):
  - [x] `union` fold: `acc = min(acc, d)`, propagate the winner's `matId`
        (the common case for the six supported entities).
  - [ ] `intersection` → `max`, `subtract` → `max(acc, -d)` with **positive
        operand's `matId`** preference, and smooth-blend `matId` interpolation:
        *(deferred to Phase 11 — CSG booleans own signed combine semantics and
        the material preference on carved surfaces)*
- [ ] Signedness gate for booleans *(deferred to Phase 11)*:
  - [ ] `intersection`/`subtract` require a signed distance function
        (`scalar_pseudo` or `scalar`); warn/reject when the active distance is
        unsigned `magnitude`.
- [x] Material table:
  - [x] Serialize per-object `color` + `opacity` as a small uniform array
        (`uMaterial`, fixed max count in v1; texture escalation later).
  - [x] `material-table.js` packs the table and emits a
        `materialColor(matId)` GLSL sampler (plus the `uMaterial` preamble).
- [x] Shading pass uses the resolved `matId` to look up color before applying
      the Phase 2 lighting.
- [ ] Bounding-box pruning *(deferred)*:
  - [ ] Per-object AABB sent as uniforms; early-out objects whose box is far
        from the current ray (coarse precheck in `map`).
- [x] Step-count cap + early termination from Phase 2 tuned for multi-object
      scenes (256-step cap reused; fine-tuning deferred).

## Verification

- [ ] A multi-object scene (sphere + line + point) renders with distinct
      per-object colors. *(deferred — browser slice in Phase 6a; the composed
      map + per-object material table are in place)*
- [ ] Smooth-union boundary between two objects blends their colors. *(Phase 11)*
- [ ] A negative sphere carving a positive sphere shows the positive sphere's
      material on the carved wall; intersection of two positive spheres keeps
      only the overlap. *(Phase 11)*
- [ ] Selecting unsigned `magnitude` while a `subtract`/`intersection` object
      is present warns/rejects per the signedness gate. *(Phase 11)*
- [ ] Object removal updates the composed SDF and the material table without
      leaking uniforms. *(deferred — dynamic update wiring lands in Phase 6)*
- [x] A headless Node smoke test (`dev/src/sdf_composer_smoke.mjs`) exercises
      the composed multi-object `map(...)` from the scene builder, plus the
      material table, and asserts the emitted GLSL is well-formed.
