# Phase 3 — Fixed distance-function set (registry + selectable recompile)

**Status:** Done

## Goal

Establish the **shared per-axis function-registry mechanism** (a name-keyed
Python enum + a matching name-keyed JS GLSL snippet registry + a
recompile-on-change hook), and use it for the first axis: the fixed,
algebra-agnostic set of distance calculation functions. The same mechanism is
reused unchanged for the opacity transfer axis (Phase 12) — distance and
opacity are two independent function registries, not two code paths, so adding
opacity later populates a registry rather than refactoring the compiler.

The backend selects which distance function is active for the SDF viewer; the
frontend recompiles the shader with the selected function's GLSL snippet. This
is a **viewer-level** setting because the composed global SDF is one ray-march
program.

## Background

For an MV object the shader computes a result coefficient vector `r[] = M·a`
(the general product MV). A distance function maps `r[]` (and optional
parameters) to a scalar distance. The functions below are identical for all
algebras — only the inputs (result-vector size / blade ordering) are fixed at
program specialization.

## Files

- New: `py/pytanga/viz/sdf/distance.py` (Python enum + metadata)
- New: `py/pytanga/viz/templates/sdf/algebra/distances.js` (GLSL snippet
  registry keyed by the same names — a `.js` module with embedded GLSL strings
  rather than a `.glsl` file, so the shared key/value registry is directly
  importable and the snippets are assembled into the shader as strings)

## Distance-function set (fixed)

| Name | GLSL signature | Formula |
|------|----------------|---------|
| `scalar_pseudo` | `float distOfScalarPseudo(in float r[NR])` | `r[0] + r[I] + length(r_rest)` |
| `magnitude` | `float distOfMagnitude(in float r[NR])` | `length(r)` |
| `scalar` | `float distOfScalar(in float r[NR])` | `r[0]` |
| `grade` | `float distOfGrade(in float r[NR], int k)` | norm of the grade-`k` slice |
| `component` | `float distOfComponent(in float r[NR], int bid)` | `r[blade_id_slot]` |

- `scalar_pseudo` is the **default**. It is signed (`r[0] + r[I]`), so it
  supports boolean subtraction, while `length(r_rest)` (magnitude of every
  other grade) keeps it nonzero for trivector results (P3 `point op line`).
  The pseudoscalar slot `I` (and the set of "rest" grades) are compile-time
  constants supplied per algebra.
- `magnitude` is unsigned and only defines the zero-set; it is unsuited to
  booleans but is universally defined for arbitrary result grades.
- `scalar` is the signed raw scalar, provided for experimentation and documented
  as degenerate when the scalar blade is never populated.
- `grade` / `component` are parametrized; their parameters are supplied as
  compile-time constants in the specialized shader (no runtime branching).

## Shared registry mechanism (reused by opacity)

- Each function axis (`distance`, `opacity`) has:
  1. a Python enum (name → value string + params metadata + `default()`),
  2. a JS `Map<string, {params, snippet}>` keyed by the same value strings,
  3. a viewer-level `active*` field whose change invalidates the program-cache
     entry for that axis and triggers recompile.
- The compiles are driven by one `buildProgram(algebra, distance, opacity)`
  entry point (Phase 8). Adding the `opacity` axis later is therefore a
  **registry population**, not a refactor of the compilation mechanism.
- The distance `snippet`s are pure functions of `r[]`; the opacity `snippet`s
  (Phase 12) are pure functions of `d` (and `ε`).

## Steps

- [x] Python `DistanceFunction` enum in `sdf/distance.py`:
  - [x] Members: `SCALAR_PSEUDO`, `MAGNITUDE`, `SCALAR`, `GRADE`, `COMPONENT`.
  - [x] `name`/`value` strings that key the JS registry (e.g. `"magnitude"`).
  - [x] Metadata describing required params (`grade` → `int k`; `component` →
        `int blade_id`) and a plain-text description.
  - [x] A `default()` returning `SCALAR_PSEUDO`.
- [x] JS `distances.js` keyed registry:
  - [x] `distanceFuncs: Map<string, {params: [..], snippet: string}>`.
  - [x] Snippets are pure functions of `r[]` (+ params), no `main()`, no
        algebra or entity branching.
- [ ] Viewer-level selection plumbing (stubs until Phase 6 wires the server):
  - [ ] `sdf_viewer.js` holds `activeDistance` (default `"scalar_pseudo"`).
  - [ ] A change to `activeDistance` invalidates the program cache entry and
        triggers a recompile.
  - [ ] A tiny, temporary switch (UI button or JS console hook) to exercise
        the recompile path now.

## Unit tests

File: `py/tests/viz/sdf/test_distance.py`

- [x] `test_enum_values` — every `DistanceFunction` value string is a valid,
      known key (matches the JS registry names).
- [x] `test_default_is_scalar_pseudo` — `DistanceFunction.default()` returns
      `SCALAR_PSEUDO`.
- [x] `test_params_metadata` — `grade` requires an `int k`, `component` requires
      an `int blade_id`; `magnitude`/`scalar`/`scalar_pseudo` require none.
- [x] `test_snippet_purity` — generated snippets contain no `main()`, no
      algebra/entity branch keywords.

## Verification

- [x] Python enum serializes to the exact string keys the JS registry expects.
- [ ] Toggling the distance function recompiles the shader and renders (verify
      with a sphere whose `r[]` is a known analytic vector via a hand-made
      test object). *(deferred — needs the `r[] = M·a` path from Phase 8 and a
      live recompile hook wired by Phase 6)*
- [ ] `scalar_pseudo` equals `scalar` on a result whose only non-scalar,
      non-pseudoscalar grades vanish; `magnitude` and `scalar` agree on a pure
      scalar result; `grade` with `k=0` equals `|scalar|`. *(deferred — GLSL
      evaluation needs a compiled shader from Phase 8)*
- [x] `uv run pytest py/tests/viz/sdf/test_distance.py` passes.
