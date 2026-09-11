# Phase 9 — Gradient calibration + algebra-vs-analytic validation

**Status:** Implemented

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

- [x] Analytic gradient probe:
  - [x] Add a finite-difference check in Python (`calibration.gradient` /
        `gradient_norm`) to estimate `|∇d|` at a point. (`calcNormal` in
        `raymarch.glsl` still serves the analytic path; this probe validates
        the *algebra* SDF and drives the per-object scale.)
  - [x] Compute the required per-object scale `s = 1/|∇d|`
        (`calibration.scale_at` / `calibrate_scale`, evaluating the gradient
        offset from the surface to avoid the `|·|` cusp of unsigned fields).
- [x] Wire a per-object `scale` uniform:
  - [x] Backend computes/persists `scale` in the `mv_sdf` wire object
        (`embed_entity_mv(..., calibrate=True)` / `serialize_mv` /
        `SdfVisualizer.add(..., calibrate=…)`).
  - [x] JS multiplies the distance by `scale` — already wired in Phases 7/8
        (`u_Scale[i]` packed in `buildAlgebraUniforms` and applied in the
        `dist_mv_<i>` leaf).
- [x] Inside/outside sign calibration:
  - [x] **Decision:** the sign is *documented*, not auto-flipped. For
        `scalar_pseudo` the sign comes from the scalar + pseudoscalar blades
        (`r[0] + r[I]`); it is per-algebra and entity-orientation dependent
        (e3/n3 plane → `-z`, p3 → `+z`, pga3 → unsigned `|z|·√2`), not a
        single global flip. Auto-flipping for interior/exterior shading only
        matters for closed entities in signed modes and is deferred.
  - [x] Document that `magnitude` is unsigned (zero-set only).
- [x] Cross-validation matrix:
  - [x] For each algebra (e3, p3, n3, pga3) and a representative plane,
        compare the algebra SDF `M·a` against the analytic plane: zero-set
        agreement + proportionality off the surface (`test_zero_set_matches_analytic_plane`).
- [x] Special-case checks:
  - [x] P3 `point op line` → trivector: nonzero `|r|` and a valid zero-set
        (the line) (`test_p3_trivector_zero_set`).
  - [x] N3 quadratic embedding: the `½ρ²·e∞` term yields a correct point
        distance (vanishes at the point, grows away)
        (`test_n3_quadratic_point`).

## Unit tests

File: `py/tests/viz/sdf/test_calibration.py`

- [x] `test_gradient_near_unit` — finite-difference `|∇(s·d)|` ≈ 1 near a
      surface point for each supported algebra/entity.
- [x] `test_zero_set_matches_analytic` — the algebra-SDF zero-set matches the
      analytic plane within tolerance.
- [x] `test_scale_applied` — the per-object `scale` corrected the raw `|r|`
      (pga3 plane: raw `√2` → calibrated `1/√2`).
- [x] `test_sign_observed` — the signed-mode sign convention is locked in per
      algebra (e3/n3 `-z`, p3 `+z`, pga3 unsigned).
- [x] `test_p3_trivector` / `test_n3_quadratic` — special-case zero-sets are
      correct.

## Verification

- [x] A documented per-algebra/entity calibration table (scale + sign) exists
      (the `calibration.py` module docstring) and is applied via
      `calibrate=True`.
- [ ] Algebra SDF visually matches analytic SDF for the same entity in the
      viewer (side-by-side scene) — deferred to the Phase 10 example.
- [ ] Sphere-tracing step counts stay within the cap (browser measurement) —
      deferred; the unit-gradient calibration is the enabling fix.
- [x] `uv run pytest py/tests/viz/sdf/test_calibration.py` passes (14 passed).
