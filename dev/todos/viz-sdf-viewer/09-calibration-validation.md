# Phase 9 — Gradient calibration + algebra-vs-analytic validation

**Status:** Planned

## Goal

Ensure the algebra SDF distances are usable for sphere-tracing: `|∇d| ≈ 1`
near the surface. Then validate algebra SDF output against the analytic SDF for
the same entities across the supported algebras.

## Background

`|r|` is proportional to, but not exactly, the Euclidean distance. With
`normalize=True` the entity is unit-normalized before `M` is formed, but a
residual per-algebra/entity scale can remain. A scale error makes sphere-tracing
step too far (miss) or too short (slow / banding).

## Steps

- [ ] Analytic gradient probe:
  - [ ] Add a finite-difference check in Python (evaluate the SDF `|r|` on a
        small stencil) to estimate `|∇d|` at a surface point.
  - [ ] Compute the required per-object scale `s` so `|∇(s·d)| ≈ 1`.
- [ ] Wire a per-object `scale` uniform:
  - [ ] Backend computes/persists `scale` alongside `M` (and exposes it as a
        calibration override).
  - [ ] JS multiplies the distance by `scale` before ray-marching.
- [ ] Inside/outside sign calibration:
  - [ ] For signed distance modes (`scalar`), determine and (if needed) flip
        the per-algebra global sign so interior/exterior shading is correct.
  - [ ] Document that `magnitude` is unsigned (zero-set only) and therefore
        has no interior shading.
- [ ] Cross-validation matrix:
  - [ ] For each algebra (e3, p3, n3, pga3) and representative entities
        (point, line, plane, sphere/circle where available), compare the
        algebra SDF `M·a` against the analytic SDF on a sampling grid.
  - [ ] Assert agreement of the zero-set within tolerance, and of the
        gradient direction (up to sign) near the surface.
- [ ] Special-case checks:
  - [ ] P3 `point op line` → trivector: confirm nonzero `|r|` and a valid
        zero-set (the line).
  - [ ] N3 quadratic embedding: confirm the `½ρ²·e∞` term yields a correct
        sphere/point distance.

## Verification

- [ ] A documented per-algebra/entity calibration table (scale + sign) exists
      and is applied automatically.
- [ ] Algebra SDF visually matches analytic SDF for the same entity in the
      viewer (side-by-side scene).
- [ ] Sphere-tracing step counts stay within the cap for all supported
      entities (no overshoot-induced failures).