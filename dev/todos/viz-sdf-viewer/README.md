# Viz SDF Viewer — Overview

**Created:** 2026-08-22 | **Status:** In progress — Phases 1–6c implemented
(plus configurable lighting, shader-drawn grid/axes overlays, the object/light
update API, and browser reconnect/version parity); Phases 7–9 and 11 (algebra
embedding backend + shader eval + calibration + CSG booleans) implemented;
Phases 10 and 12 (finalize, opacity transfers) remain.

## Target

Add a signed-distance-function (SDF) based viewer to Tanga. The SDF viewer
renders geometry by ray-marching a fragment shader built for three.js
`ShaderMaterial`, using the inigo quilez SDF reference formulas for the base
primitives and combinators.

There are two rendering paths:

1. **Analytic path** — geometry entities and operators are mapped to
   compositions of a SDF primitive library, with the primitive set exposed
   directly as `SdfNode` objects and grouped via `Composed` (Phases 06b/06c).
   `Point`→sphere, crosshair point→3-axis crosshair, `Line`→segment,
   `Sphere`→sphere, `Rotor`→disc+ring+axis, `Translator`/`Direction`→arrow,
   `Dilator`→rings, `Motor`→disc+arrow, etc. `wireframe` is not honoured
   (a true wireframe cage cannot be expressed as a solid); only
   `TripleReflection`/`VersorFactors` remain deferred (`TypeError`).
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
  Entity/Operator          MV              SdfNode/Composed   Light/Overlay
      │                     │                   │                 │
      │ analytic            │ algebra           │ fundamental     │ config
      ▼                     ▼                   ▼                 ▼
  sdf/serializer.py    sdf/algebra_embedding.py   sdf/primitives.py + sdf/composed.py
  (SDF primitive tree)   · canonical blade ordering (point/result masks)
                         · product_tensor(ip|op) contracted over entity blade
                           → M[c,a]   ("the general MV already in the matrix")
                         · embed_src: algebra-specific point-embedding GLSL
                         · normalize option (entity normalized before forming M)
                         · bound: finite clip for infinite planes/lines
      └────────────────────┬──────────────────────────────────────────┘
                           ▼
        WS (scene_update / object_update / sdf_viewer_config:
            distance, opacity, sdf_lighting, sdf_overlays)
                           ▼
Frontend (py/pytanga/viz/templates/sdf/)
  sdf_viewer.js  →  ONE composed global SDF (single fullscreen-quad ShaderMaterial)
      fragment = common + primitives + combinators + material + lighting
                 + overlays + embed_src(algebra)… + composeObjects() + raymarch
      rebuild split: structure changes recompile, data-only changes update uniforms
  material-ID hit tracking + combine modes + depth-composited overlays
```

### The three shader-specialization axes (no if-branching)

- **Point embedding is algebra-specific** and (for N3) nonlinear in the point,
  so it is *code*, not a matrix. Each algebra contributes an `embed_src` GLSL
  snippet `evalPoint(vec3 p, out float a[NP])`, deduped by identity and emitted
  once per distinct algebra present in the scene.
- **Distance functions are a fixed algebra-agnostic set**, applied to the result
  vector `r[] = M·a`. The backend selects the active distance function for the
  viewer; the frontend recompiles the shader with the selected `distOf` snippet.
- **Opacity transfer functions are a fixed set**, applied to the distance. The
  backend selects the active transfer; the frontend recompiles with the
  selected `opacityOf` snippet.

All axes are handled by string-concatenation compilation into the **single
composed `map()`**. Algebra is per-object data (each `mv_sdf` leaf carries its
own `M`/`bound`), while distance and opacity are viewer-level. Recompilation is
keyed on a program's *structure* (`(distance, opacity, distinct embeds, object
kinds/combines)`); data-only changes (matrix/material/lighting uniforms) update
uniforms without recompiling. The shader therefore contains **no** `if (algebra
== …)` / `if (entity == …)` / `if (distance == …)` / `if (opacity == …)`
branching — the selection is resolved entirely at compile time, and switching a
viewer axis (or changing object structure) triggers a recompile.

## SDF object hierarchy (two layers)

The analytic path is layered, keeping fundamentals and compositions separate:

- **Layer 1 — fundamental objects.** Each is described directly by a distance
  function: `sphere`, `box`, `cylinder`, `torus`, `cone`, `capsule`, `segment`,
  … (the Phase 1 GLSL set), exposed as addable `SdfNode` objects via named
  constructors in `pytanga.viz.sdf`.
- **Layer 2 — composed drawables.** A `Composed` object bundles several
  constituents into **one** scene entry / material, with a **per-constituent
  combine mode** (`union` / `intersection` / `subtract`). It serializes to a
  `group` node folded in order, and nests `Composed` recursively.

Geometry entities and operators each map to a **basic or composed** SDF object
per draw style (Phase 06c): `Point`→sphere, `CrossHairPointStyle`→3-axis
crosshair, `Rotor`→disc, `Translator`→arrow, `Motor`→disc+arrow, etc.

### Reserved future seams (not implemented yet)

Three seams are intentionally left open so texture-based features can be added
later without refactoring:

- **UV mode** — a per-object surface parameterization (planar/spherical/
  cylindrical/triplanar) will be an additive `SdfNode` field plus a parallel
  `emitUv` emitter, and `map()` will widen from `vec2` to also carry `uv`.
- **Signed displacement field** — a per-object distance modifier folded with
  `add`/`min`/`max` at the object-expression boundary. This covers continuous
  displacement maps and emboss/engrave glyph relief (an MSDF atlas is one such
  "distance texture"; a true per-glyph SDF is the future fallback for deep
  extrusion).
- **Texture binding** — `sampler2D` uniforms join the `uMaterial` array
  ("texture escalation"); `materialColor(matId)` becomes
  `materialColor(matId, uv)` inside the single material-table module.

### Known limitations

- **Subtractive CSG vs. soft shadows.** The soft-shadow term marches the single
  composed distance field, so it only knows the distance to the nearest
  *boundary*, not whether that boundary is a solid occluder or the wall/rim of a
  subtracted hole. A `subtract` volume (e.g. the cylinder bored through the
  `demo_sdf_composed.py` bead) can consequently cast a faint penumbra even
  though a hole has no material to block light. A proper fix would trace shadow
  rays against a solid-only distance field (excluding subtractive volumes) and
  is deferred as a known limitation.

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
the shared function-registry mechanism is built in Phase 3 (and emitted through
the Phase 8 single-`map()` assembly), so Phase 12 only *populates* the registry
with `linear`/`sigmoid` and adds the volumetric accumulation — no refactor.

## Boolean combine modes (positive/negative objects)

*(Implemented in Phases 5/6b/6c — `serializer._normalize_combine`,
`SdfVisualizer.add(..., combine=/polarity=)`, and the `composer.js` fold; the
signedness gate and smooth variants are the remaining Phase 11 work.)*

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
| 6b | [06b-composed-objects.md](./06b-composed-objects.md) | Primitive object library + `Composed` objects (per-constituent combine modes) |
| 6c | [06c-entity-operator-drawstyles.md](./06c-entity-operator-drawstyles.md) | Entity/operator → SDF-object mapping per draw style |
| 7 | [07-algebra-embedding-python.md](./07-algebra-embedding-python.md) | `algebra_embedding.py`: ordering, `M`, `embeds.js`, normalize, bound |
| 8 | [08-algebra-eval-shader-compile.md](./08-algebra-eval-shader-compile.md) | `algebra/eval.js`: `embed → M·a → distOf → opacityOf` inside the single composed `map()` (structure-vs-data rebuild split) |
| 9 | [09-calibration-validation.md](./09-calibration-validation.md) | `|∇d|≈1` calibration + algebra-SDF vs analytic-SDF validation |
| 10 | [10-tests-examples-docs.md](./10-tests-examples-docs.md) | Examples, docs, changelog, PR (per-phase unit tests live in their phases) |
| 11 | [11-csg-booleans.md](./11-csg-booleans.md) | Positive/negative objects: `union`/`intersection`/`subtract` combine modes (core shipped in 5/6b/6c; gate + smooth variants remain) |
| 12 | [12-opacity-transfer.md](./12-opacity-transfer.md) | Populate non-`step` opacity transfers + volumetric (mechanism from Phases 2/3/8) |

The table above is a **file index** keyed by the plan filename. The recommended
**build order** is:

`1 → 2 → 3 → 4 → 5 → 6 → 6a → 6b → 6c → 7 → 8 → 9 → 11 → 12 → 10`

Phases 11 (CSG booleans) and 12 (opacity transfers) are implemented *before*
Phase 10 (finalize), which runs last and folds their examples
(`demo_sdf_booleans.py`, `demo_sdf_opacity.py`) and tests (`test_combine.py`,
`test_opacity.py`) into the accumulated full suite. The filenames/numbers are
left unchanged to avoid renaming churn.

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
- **Full entity/operator mapping** (Phase 06c): every entity/operator kind maps
  to a basic or composed SDF object per draw style (`style=` honoured); only
  `TripleReflection`/`VersorFactors` still raise `TypeError`. `wireframe` is
  not honoured (a true wireframe cage is a 1D structure the ray-marcher cannot
  express as a solid).
- **Configurable lighting** mirrors the standard viewer's add/update API:
  `DirectionalLight` via `add()`, `set_ambient_light()`, `add_default_light`.
- **Shader-drawn overlays** (`Grid`, `Axes`) are depth-composited in the
  fragment shader, not raymarched volumes; `add_default_grid`/`add_default_axes`.
- **Object/light updates** via `update_entity()`/`update_light()` + `flush()` /
  `sleep_ms()` support animation without a full scene reload.
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
- **Camera parity.** The SDF viewer's default camera and custom-camera handling
  are identical to the standard viewer: the same `view_mode.js`
  `createCamera` / `switchToCamera` (3D branch) and `controls.js` defaults are
  reused, and the camera travels through the shared `scene_config.camera`
  field. Default (`PerspectiveCamera(50, aspect, 0.1, 1000)` at
  `position=(8,6,10)` looking at the origin) and any custom `CameraConfig3d`
  therefore match the standard viewer 1:1. `fit_camera` auto-fit is a known
  gap (see Risks).

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
- **Algebra-leaf uniform budget:** each `mv_sdf` `M` matrix is a per-object
  float array; with large result spaces (N3 ≈ 32 blades) the fragment-uniform
  budget (`GL_MAX_FRAGMENT_UNIFORM_VECTORS`) is reached after only a few
  objects. Mitigate by packing all `M` into one flat `u_M[]` uniform and, past
  a threshold, a data texture (the material table's planned "texture
  escalation").
- **Volumetric opacity cost:** soft/volumetric transfer requires accumulation
  along the ray (more samples) and depends on a unit-scaled distance (Phase 9);
  `step`/`linear`/`sigmoid` are cheap, true absorption is the optional follow-on.
- **`fit_camera` auto-fit gap:** the standard viewer's `fitCamera` derives a
  bounding box from entity meshes, which the SDF path does not build. SDF
  auto-fit needs its own bounds computation; deferred to a later phase. Until
  then the SDF viewer relies on the default/custom camera only.
