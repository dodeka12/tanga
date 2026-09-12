# Projective Quadric Space (Conic + Quadric3D) — Overview

**Created:** 2026-08-29 | **Status:** Done | **Branch:** `feat/quadric-space`

## Goal

Implement the **projective quadric space** (Perwass's conic space,
`GAGeometry/GAConicSpc.tex`, generalized to 3D): points
embed as rank-1 symmetric matrices (`D_op(x) = x xᵀ`), conics (2D) and quadrics (3D)
are symmetric 3×3 / 4×4 matrices, and the **outer product** of point embeddings
builds conics/quadrics. Add the 3D quadric **analytic ray renderer** as a *general*
renderer framework (style-selected), and expose both the raw (`Conic`/`Quadric3D`)
and refined (Ellipse, Ellipsoid, …) geometric entities.

- **2D**: quadric space `CA{6}` → `Algebra(6, 0)`, 2⁶ = 64 blades.
- **3D**: quadric space → `Algebra(10, 0)`, 2¹⁰ = 1024 blades (extension of the
  thesis's 2D construction to symmetric 4×4 matrices).

## Math (fixed up front; implement against this)

Perwass's 2D conventions (Euclidean-rescaled basis `b₁…b₆`, all `bᵢ·bᵢ = 1`; the
thesis's `eᵢ` with squared-norms `(1,1,2,2,2,1)` maps to `bᵢ` via `b₃₄₅ = e₃₄₅/√2`):

- Symmetric 3×3 `A` (entries `a₁₁…a₃₃`, `aᵢⱼ = aⱼᵢ`) → coeff vector
  `(a₁₃, a₂₃, (√2/2)a₃₃, (√2/2)a₁₁, (√2/2)a₂₂, a₁₂)`.
- `embed_point(x, y) = x b₁ + y b₂ + (√2/2) b₃ + (√2/2)x² b₄ + (√2/2)y² b₅ + x y b₆`.
- Incidence `embed_point(x,y)·coeff(A) = ½ xᵀ A x`, so `= 0` ⟺ point on conic.
- Conic through 5 points `= coeff⁻¹(dual(∧ᵢ D_op(aᵢ)))`.
- Line through 2 points `= D_op(a) ∧ D_op(b) ∧ b₄ ∧ b₅ ∧ b₆`.

3D generalization (symmetric 4×4 `Q`): 10 coeffs, ordering
`(q₁₄, q₂₄, q₃₄, (√2/2)q₄₄, (√2/2)q₁₁, (√2/2)q₂₂, (√2/2)q₃₃, q₁₂, q₁₃, q₂₃)`;
`embed_point(x,y,z) = x b₁ + y b₂ + z b₃ + (√2/2) b₄ + (√2/2)x² b₅ + (√2/2)y² b₆
+ (√2/2)z² b₇ + xy b₈ + xz b₉ + yz b₁₀`.

Metric decision: **rescale to Euclidean** `Algebra(6,0)`/`Algebra(10,0)` (no C++
changes); the `√2/2` factors live only in `embed_point` / `to_coeffs` /
`from_coeffs`.

## Naming

- Bases: `BasisQ2` (2D) and `BasisQ3` (3D); "Q" = quadric (the general degree-2
  hypersurface — a conic is a 2D quadric).
- Entities: `Conic` (2D; synonym `Quadric2D = Conic`) and `Quadric3D` (3D).
  "Conic" is used for 2D because it is inherently 2D; `Quadric2D` is the symmetric
  alias. `analysis_q2.py` / `create_q2.py` / detect `"q2"` serve `BasisQ2`;
  `analysis_q3.py` / `create_q3.py` / `"q3"` serve `BasisQ3`.

## Key decisions

- **Two-level analysis.** `analyze(mv)` in quadric spaces always returns the raw
  `Conic`/`Quadric3D` (lossless). Calling `geo(conic)` / `geo(quadric3d)`
  again **refines** it to a specific entity (Ellipse, Ellipsoid, …) when possible.
- **`PointSet`** is the unified output for finite point sets (single/pair/triplet/
  quadruplet/n-tuple) from OPNS point-joins (`blade_factorize` + per-factor SVD).
- **General ray renderer.** Style-selected renderer dispatch, exactly like the
  existing mesh/SDF split: `RayStyle` marker → `kind:"ray"` → proxy mesh with an
  analytic fragment shader writing `gl_FragDepth`. `Quadric3D`'s default style is
  `RayQuadricStyle`.
- **2D conics are explicit-entity-first.** Every conic refines to a concrete entity
  (Circle/Ellipse/Hyperbola/Parabola/Line/LinePair/ParallelLinePair); no 2D analytic
  renderer in this plan.
- **Deferred:** general 3D intersection analysis (space curves / 8-point triple
  intersections) — render those blades via the quadric ray renderer instead.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-quadric-space-core.md](./01-quadric-space-core.md) | `pytanga.quadric`: bases, embedding, coeff maps, build-from-points |
| 2 | [02-entities.md](./02-entities.md) | `Conic`, `Quadric3D`, `Hyperbola`, `Parabola`, `LinePair`, `ParallelLinePair`, `PointSet` |
| 3 | [03-analysis-grade1.md](./03-analysis-grade1.md) | grade-1/dual → `Conic`/`Quadric3D` + `refine()` → specific entities |
| 4 | [04-analysis-pointsets-intersections.md](./04-analysis-pointsets-intersections.md) | `PointSet` (joins) + 2D two-conic intersection (thesis pencil method) |
| 5 | [05-creation.md](./05-creation.md) | `create()`: entities → quadric-space MV |
| 6 | [06-ray-renderer-framework.md](./06-ray-renderer-framework.md) | `RayStyle` + `_is_ray_styled` + `kind:"ray"` + generic ray proxy |
| 7 | [07-quadric-ray-rendering.md](./07-quadric-ray-rendering.md) | `RayQuadricStyle` + `Quadric3D` wire contract + quadric shader |
| 8 | [08-conic-renderers.md](./08-conic-renderers.md) | Hyperbola/Parabola/LinePair/ParallelLinePair/PointSet curve renderers |
| 9 | [09-integration-tests-docs.md](./09-integration-tests-docs.md) | Examples, docs, changelog, full regression |

## Testing as you go

- **Python:** `uv run pytest py/tests/quadric py/tests/geometry py/tests/viz -q` for
  the new/updated suites; full `uv run pytest` at the end.
- **JS:** `node --input-type=module --check` on each touched renderer + `factory.js`;
  `uv run pytest py/tests/viz/test_export_renderers.py -q` keeps the export bundle in
  lockstep with the on-disk renderer set.
- Every phase ends with a runnable validation command before the next phase.

## Guiding decisions / no-refactor rule

- `Algebra(6,0)` / `Algebra(10,0)` are used **as-is** (Euclidean metric); the quadric
  metric normalization is isolated in `pytanga.quadric` mapping functions.
- Analysis follows the existing `analysis_*` / `create_*` / `Geometry` dispatcher
  pattern, and respects the algebra's `opns` flag.
- The ray renderer reuses the SDF **proxy** pattern (bounding box + `gl_FragDepth`
  shader) so ray objects depth-composite with meshes and SDF proxies in one scene.

## Deferred (not in this plan)

- General 3D intersection analysis (quartic space curves, triple-intersection point
  sets, line systems) — replaced by analytic quadric rendering for now.
- 2D analytic implicit-curve renderer (`Conic` rendered directly via `xᵀCx = 0`).
- `SdfQuadricStyle` (SDF fallback for `Quadric3D`).
- C++ core support for non-±1 diagonal metrics (would let the thesis coefficients be
  used verbatim without the `√2` rescaling).
