<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2021 Christian Perwass (author) -->

# Quadric intersection — the elliptic "hard case" (implementation sketch)

**Status:** Sketch (not a plan) | **Related plan:** `dev/todos/quadric-intersection/`

This is a *sketch* of the one case deliberately left out of the
`quadric-intersection` plan.  That plan raises `NotImplementedError` here.

## What the hard case is

The pencil `Q1 − λQ2` generically has `det(Q1 − λQ2) = 0` as a degree‑4
polynomial.  When **none** of the four roots is real, there is no real
degenerate member — no plane pair and no cone to exploit.  The intersection is
then a **smooth quartic space curve of genus 1** (elliptic), irreducible: no
lines, no conics, no rational global parametrisation (a rational curve has genus
0; an elliptic quartic does not).  That is what makes it hard.

## Implementation approach (sketch)

Two standard routes; both start from the same seed problem.

**Seed point.** Intersect `Q1 = 0` with a generic line (e.g. a coordinate line,
or a line through a known point) to obtain one real point `P` on the curve
(a quadratic solve).  If no real point exists, the real intersection is empty and
we return an empty `Curve`.

**Route A — implicit marching (most general, all we need for rendering).**

1. At a current point `x` on the curve, the tangent direction is
   `t = ∇(xᵀQ1x) × ∇(xᵀQ2x)` (both gradients evaluated at `x`; the curve tangent
   is orthogonal to both).
2. Predict `x′ = x + h·t̂`, then **correct** back onto the curve: solve the 2×2
   Newton system `xᵀQ1x = 0, xᵀQ2x = 0` in the plane spanned by the two gradient
   directions (2 variables, 2 constraints).
3. Step adaptively (`h` halved when the correction grows), walk until the loop
   closes (or a step budget is exhausted), and emit the sampled `Point`s as a
   `Curve`.
4. Robustness knobs: seed the tangent sign consistently, dedupe near points,
   and treat a failed correction as a break (emit the partial arc).

**Route B — elliptic parametrisation (exact, optional).**

1. Project the quartic from `P` onto a plane: the projection is a **plane cubic**
   (genus 1, as expected).  A plane cubic with a known point is parametrisable
   via its Weierstrass normal form (`y² = x³ + a x + b`), giving the curve exactly
   in terms of `(℘, ℘′)`.
2. Lift each cubic point back along its projector line to recover the 3D curve.
3. This yields exact (non-adaptive) samples and a closed-form length/area, but is
   materially more code (Weierstrass reduction + `℘` evaluation).

**Recommendation.** Implement **Route A** (marching) first — it reuses the
existing line‑quadric quadratic solve and the `Curve` entity, and covers every
smooth case.  Route B is a later refinement if exact parametrisation is wanted.

## References

- Dupont, Lazard, Lazard, Petitjean — "Near-optimal parameterization of the
  intersection of quadrics" (the standard algorithmic reference; classifies the
  pencil into the plane-pair / cone / elliptic cases used by the main plan).
- Any projective-geometry text for the "smooth complete intersection of two
  quadrics is a genus-1 quartic" fact (Bézout degree 4; genus-degree formula).
