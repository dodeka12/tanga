# Viz SDF Viewer — Overview

**Created:** 2026-08-22 | **Status:** Planned

## Target

Add a signed-distance-function (SDF) based viewer to Tanga. The SDF viewer
renders geometry by ray-marching a fragment shader built for three.js
`ShaderMaterial`, using the inigo quilez SDF reference formulas for the base
primitives and combinators.

There are two rendering paths:

1. **Analytic path** — the initially-supported geometric entities (`Point`,
   `Line`, `Plane`, `Sphere`, `Circle`, `PointPair`) are mapped to compositions
   of a SDF primitive library. Operators, `Direction`, `Space`, and other
   entity kinds are deferred.
2. **Algebra path** — an MV is drawn by directly evaluating `ip(point, mv)` or
   `op(point, mv)` (chosen by the MV's algebra `opns` setting) and mapping the
   resulting multivector to a signed distance via a registered distance
   function (default `scalar_pseudo`: scalar + pseudoscalar + magnitude of the
   rest). The general product MV is reduced to a partially-contracted matrix on
   the backend; the shader only embeds the ray point (algebra-specific,
   compile-time) and does a matrix-vector multiply, then applies a registered
   distance function and an opacity transfer function.

The SDF viewer is a **separate module** and a **separate JavaScript library**,
but it reuses the existing viewer's `server.py` WebSocket infrastructure and its
HTML bootstrap (CDN import map, status, loading, error/fallback handling).

## Architecture

```
Python backend
  Entity (six kinds)       MV
      │                     │
      │ analytic            │ algebra
      ▼                     ▼
  sdf/serializer.py    sdf/algebra_embedding.py
  (SDF primitive tree)   · canonical blade ordering (point/result masks)
                         · product_tensor(ip|op) contracted over entity blade
                           → M[c,a]   ("the general MV already in the matrix")
                         · embed_src: algebra-specific point-embedding GLSL
                         · normalize option (entity normalized before forming M)
                         · bound: finite clip for infinite planes/lines
      └──────────┬────────────┘
                 ▼
        WS (scene_update / object_update / sdf_viewer_config)
                 ▼
Frontend (py/pytanga/viz/templates/sdf/)
  sdf_viewer.js  →  program cache keyed by (algebra, distance, opacity)
      fragment = common + embed_src(algebra) + distOf(distance)
                 + opacityOf(opacity) + raymarch_body
  one composed global SDF, material-ID hit tracking
```

### The three shader-specialization axes (no if-branching)

- **Point embedding is algebra-specific** and (for N3) nonlinear in the point,
  so it is *code*, not a matrix. Each algebra contributes an `embed_src` GLSL
  snippet `evalPoint(vec3 p, out float a[NP])`.
- **Distance functions are a fixed algebra-agnostic set**, applied to the result
  vector `r[] = M·a`. The backend selects the active distance function for the
  viewer; the frontend recompiles the shader with the selected `distOf` snippet.
- **Opacity transfer functions are a fixed set**, applied to the distance. The
  backend selects the active transfer; the frontend recompiles with the
  selected `opacityOf` snippet.

All three axes are handled by string-concatenation compilation with a program
cache keyed by `(algebra, distance, opacity)`. The shader therefore contains
**no** `if (algebra == …)` / `if (entity == …)` / `if (distance == …)` /
`if (opacity == …)` branching — the selection is resolved entirely at compile
time, and switching any axis triggers a recompile.

## Distance functions (fixed set, all algebras, algebra-agnostic)

`distOf(r[], …)` maps the result MV coefficient vector to a scalar distance:

| Name | Formula | Notes |
|------|---------|-------|
| `scalar_pseudo` | `r[0] + r[I] + length(r_rest)` | **default**; signed via the scalar + pseudoscalar blades, plus the magnitude of every other grade |
| `magnitude` | `length(r)` | unsigned; works when `r` is any grade (e.g. P3 `point op line` → trivector where `r[0] ≡ 0`) |
| `scalar` | `r[0]` | signed raw scalar; provided for experimentation — degenerate when the scalar blade is always zero |
| `grade` | `length(r restricted to grade k)` | parametrized by a compile-time/external `grade` constant |
| `component` | `r[blade_id]` | a single result blade coefficient |

`scalar_pseudo` is signed (scalar + pseudoscalar contribute with sign), so it is
usable for boolean subtraction, while the magnitude-of-rest term keeps it
nonzero for trivector results (P3 `point op line`). `magnitude` is unsigned and
therefore unsuited to boolean difference/intersection.

The distance function is a **viewer-level** setting (one active at a time),
because the composed global SDF is a single ray-march program. `normalize` is an
orthogonal per-object option (normalize the MV *before* forming `M`, default
`True`) independent of the distance function.

## Opacity transfer (distance → opacity)

The distance (whether analytic or algebra-derived) is mapped to opacity through
a **selectable transfer function**, independent of the distance function. There
are two places opacity is applied:

- **Surface opacity** — a single hit resolves the object color and its `opacity`
  is the per-object blend factor (blended color, `depthWrite:false`).
- **Volumetric opacity** — for soft/translucent looks, absorbance is integrated
  along the ray (`transmittance = exp(−Σ σ(p)·Δt)`, `opacity = 1 −
  transmittance`) using a density `σ(p)` derived from the distance.

The fixed transfer-function set, chosen from the backend and recompiled into the
shader (no branching):

| Name | Formula | Effect |
|------|---------|--------|
| `step` | `d < 0 ? 1 : 0` | crisp solid |
| `linear` | `clamp(1 − d/ε, 0, 1)` | soft band around the surface |
| `sigmoid` | `1 − 1/(1 + exp(−d/ε))` | smooth soft edge |

Knobs: a per-object `opacity` acting as the falloff breadth `ε` when the
transfer is not `step`, and optionally a global `density` scale `σ₀` for the
volumetric path.

The `opacityOf` call site and its `step` default are **stubbed in Phase 2**, and
the shared function-registry mechanism is built in Phase 3 (and compiled by
`(algebra, distance, opacity)` in Phase 8), so Phase 12 only *populates* the
registry with `linear`/`sigmoid` and adds the volumetric accumulation — no
refactor.

## Boolean combine modes (positive/negative objects)

A signed distance is negative inside. Combinators produce:

- **union** `min(dA, dB)` — inside either.
- **intersection** `max(dA, dB)` — inside both.
- **difference** `max(dA, −dB)` — inside A, not inside B.

A **negative** object is one whose distance is negated before folding; combined
with `max` against a positive object it carves (subtracts). Exposed as a
per-object `combine` mode (`union` / `intersection` / `subtract`) or
`polarity` (`positive` / `negative`). Because `subtract`/`intersection` rely on
signedness, they require a signed distance function (`scalar_pseudo` or
`scalar`); the unsigned `magnitude` mode is unsuited to them.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-primitives-combinators.md](./01-primitives-combinators.md) | IQ SDF primitive + combinator GLSL library |
| 2 | [02-webgl2-raymarcher-core.md](./02-webgl2-raymarcher-core.md) | WebGL2 gate + fullscreen-quad raymarcher + gradient normal + shading + `opacityOf` stub |
| 3 | [03-distance-function-registry.md](./03-distance-function-registry.md) | Fixed distance-function set (Python enum + JS GLSL registry) |
| 4 | [04-entity-sdf-serializer.md](./04-entity-sdf-serializer.md) | Analytic entity → SDF primitive-tree mapping |
| 5 | [05-composed-scene-material-table.md](./05-composed-scene-material-table.md) | Composed global SDF + material-ID hit tracking |
| 6 | [06-sdf-viewer-server-html.md](./06-sdf-viewer-server-html.md) | `SdfVisualizer` facade + `sdf_viewer.html`, reusing `server.py` + WS protocol |
| 6a | [06a-first-vertical-slice.md](./06a-first-vertical-slice.md) | First vertical slice: `demo_sdf_entities.py` (line + sphere) with manual user confirmation |
| 7 | [07-algebra-embedding-python.md](./07-algebra-embedding-python.md) | `algebra_embedding.py`: ordering, `M`, `embed_src`, normalize, bound |
| 8 | [08-algebra-eval-shader-compile.md](./08-algebra-eval-shader-compile.md) | `algebra/eval.js`: `embed → M·a → distOf → opacityOf` with per-`(algebra,distance,opacity)` program cache |
| 9 | [09-calibration-validation.md](./09-calibration-validation.md) | `|∇d|≈1` calibration + algebra-SDF vs analytic-SDF validation |
| 10 | [10-tests-examples-docs.md](./10-tests-examples-docs.md) | Examples, docs, changelog, PR (per-phase unit tests live in their phases) |
| 11 | [11-csg-booleans.md](./11-csg-booleans.md) | Positive/negative objects: `union`/`intersection`/`subtract` combine modes |
| 12 | [12-opacity-transfer.md](./12-opacity-transfer.md) | Populate non-`step` opacity transfers + volumetric (mechanism from Phases 2/3/8) |

## Testing strategy (fail early)

- **Every implementation phase ships its own unit tests** under
  `py/tests/viz/sdf/` and runs them in its Verification step
  (`uv run pytest py/tests/viz/sdf/<file>`). Failures surface in the phase that
  introduced the code, not in a late integration pass.
- Phase-local test files:
  - Phase 3 → `test_distance.py`
  - Phase 4 → `test_primitives.py` + `test_serializer.py`
  - Phase 6 → `test_visualizer.py`
  - Phase 7 → `test_algebra_embedding.py`
  - Phase 9 → `test_calibration.py`
  - Phase 11 → `test_combine.py`
  - Phase 12 → `test_opacity.py`
- JS phases (2, 5, 8) add a headless Node smoke / GLSL compile check in their
  Verification steps, so the shader/compiler fails early too.
- Phase 10 runs the **accumulated full suite** and finalizes examples/docs/
  changelog/PR; it does not re-own the per-phase tests.

## Milestones

- **First vertical slice (Phase 6a)** — the analytic entity path works
  end-to-end: `py/examples/viz/demo_sdf_entities.py` opens the viewer and
  draws a `Line` and a `Sphere` from `pytanga.geometry`, confirmed manually by
  the user in the browser before any algebra/CSG/opacity work starts.

## Guiding decisions

- **Composed global SDF** (one ray-march, material-ID hit tracking) unless
  per-object transparency forces a layered/pass approach later.
- **WebGL2 is a hard requirement.** If unavailable, the viewer shows an in-page
  error banner and logs; there is no silent WebGL1 fallback.
- **3D only** for the SDF viewer; 2D is deferred.
- **Style scope is minimal**: initially only `color` and `opacity` are read
  from entity styles; other flags (`wireframe`, sizes, …) are ignored until a
  later phase.
- **Initial entity scope**: only `Point`, `Line`, `Plane`, `Sphere`, `Circle`,
  `PointPair`; other entities/operators are deferred and raise `TypeError`.
- **Unit tests are phase-scoped and run per phase** (fail early) — no waiting
  until a late integration pass.
- **The default algebra distance is `scalar_pseudo`**: the signed scalar +
  pseudoscalar (`r[0] + r[I]`) plus the magnitude of every other grade.
  `magnitude` and `scalar` remain explicit alternatives.
- **`M` is the partially contracted product tensor.** The result blade axis is
  kept; the entity blade axis is contracted out on the backend so the general
  result MV is "already in the matrix".
- **Point embedding is shader code supplied per algebra**, never a runtime
  branch. `embed_src` and `M` share one canonical blade ordering, emitted
  together by `algebra_embedding.py` to prevent silent reorder bugs.
- **Distance function is viewer-level** and recompiles the shader on change.
- **`normalize` defaults to `True`** (normalize the entity MV before forming
  `M`); it is independent of the distance function.
- **Boolean combine modes** are per-object: `combine` (`union` / `intersection`
  / `subtract`) or `polarity` (`positive` / `negative`); negative = negated
  distance folded with `max`.
- **Distance → opacity transfer is viewer-level** and plugged in exactly like
  the distance function: a fixed registry (`step` / `linear` / `sigmoid`),
  selected from the backend, recompiled into the shader with no branching.
- **Infinite entities** (planes, lines) use an explicit `bound` region
  (`opIntersect` with a finite slab/capsule shell).
- **Reuse, don't fork.** `server.py` and the WS protocol are shared unchanged;
  the JS lives in a separate `sdf/` library reusing the existing HTML bootstrap.

## Risks

- **Gradient scale:** the distance (whether `scalar_pseudo`, `magnitude`, or
  `scalar`) is proportional to, but not exactly, metric distance.
  `normalize=True` is the hedge; a residual per-algebra/entity scale must be
  calibrated so sphere-tracing steps are well-scaled (`|∇d|≈1`).
- **Signedness for booleans:** `subtract`/`intersection` negate and `max`
  distances, so they only behave correctly with a signed distance
  (`scalar_pseudo` or `scalar`); the unsigned `magnitude` mode must not be
  combined with booleans.
- **`scalar_pseudo` gradient scale:** the scalar-pseudoscalar sum plus
  magnitude-of-rest is a heuristic — its gradient is not guaranteed to be
  unit-norm and its global sign must be calibrated per algebra (Phase 9).
- **`scalar` degeneracy:** some products (P3 `point op line`) never produce a
  scalar blade, so `scalar` is degenerate there; `scalar_pseudo` avoids this by
  adding the magnitude of the remaining grades.
- **N3 quadratic embedding:** `…+ ½ρ²e∞` cannot be reduced to a matrix — it
  lives in `embed_src`, keeping the algebra module the single source of truth.
- **Multi-object performance:** one global SDF per ray step is costly; mitigate
  with AABB coarse culling, step caps, adaptive stepping and early-out.
- **Volumetric opacity cost:** soft/volumetric transfer requires accumulation
  along the ray (more samples) and depends on a unit-scaled distance (Phase 9);
  `step`/`linear`/`sigmoid` are cheap, true absorption is the optional follow-on.
