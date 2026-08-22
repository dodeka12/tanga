# Phase 3 — Fixed distance-function set (registry + selectable recompile)

**Status:** Planned

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
- New: `py/pytanga/viz/templates/sdf/algebra/distances.glsl` (GLSL snippets,
  keyed by the same names)

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

- [ ] Python `DistanceFunction` enum in `sdf/distance.py`:
  - [ ] Members: `SCALAR_PSEUDO`, `MAGNITUDE`, `SCALAR`, `GRADE`, `COMPONENT`.
  - [ ] `name`/`value` strings that key the JS registry (e.g. `"magnitude"`).
  - [ ] Metadata describing required params (`grade` → `int k`; `component` →
        `int blade_id`) and a plain-text description.
  - [ ] A `default()` returning `SCALAR_PSEUDO`.
- [ ] JS `distances.glsl` keyed registry:
  - [ ] `distanceFuncs: Map<string, {params: [..], snippet: string}>`.
  - [ ] Snippets are pure functions of `r[]` (+ params), no `main()`, no
        algebra or entity branching.
- [ ] Viewer-level selection plumbing (stubs until Phase 6 wires the server):
  - [ ] `sdf_viewer.js` holds `activeDistance` (default `"scalar_pseudo"`).
  - [ ] A change to `activeDistance` invalidates the program cache entry and
        triggers a recompile.
  - [ ] A tiny, temporary switch (UI button or JS console hook) to exercise
        the recompile path now.

## Verification

- [ ] Python enum serializes to the exact string keys the JS registry expects.
- [ ] Toggling the distance function recompiles the shader and renders (verify
      with a sphere whose `r[]` is a known analytic vector via a hand-made
      test object).
- [ ] `scalar_pseudo` equals `scalar` on a result whose only non-scalar,
      non-pseudoscalar grades vanish; `magnitude` and `scalar` agree on a pure
      scalar result; `grade` with `k=0` equals `|scalar|`.
