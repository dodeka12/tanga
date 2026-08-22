# Phase 12 — Opacity transfer functions: non-`step` transfers + volumetric

**Status:** Planned

## Goal

Populate the opacity transfer axis with the full function set and the
volumetric accumulation path. The registry mechanism, the `opacityOf` call
site, and the three-axis program key already exist (Phase 2 stubs `opacityOf`
as `step`; Phase 3 establishes the shared registry; Phase 8 compiles by
`(algebra, distance, opacity)`). **This phase adds functionality, not a
refactor.**

## Already in place (no rework here)

- Phase 2: an `opacityOf(float d)` call site in the shading path, wired to the
  `step` implementation, with the per-object color multiplier reserved.
- Phase 3: the shared per-axis registry contract (Python enum ↔ JS
  `Map<name, {params, snippet}>` ↔ viewer `active*` recompile hook).
- Phase 8: `buildProgram(algebra, distance, opacity)` and the
  `"<algebra>:<distance>:<opacity>"` cache key, plus the `opacityOf` emission.

## Background

There are two opacity application points:

- **Surface opacity** — on a ray hit, the object's `opacity` style factor is
  applied to the shaded color.
- **Volumetric opacity** — for soft/translucent volumes, absorbance is
  integrated along the ray:
  `transmittance = exp(−Σ σ(p)·Δt)`, `opacity = 1 − transmittance`, where the
  density `σ(p)` is derived from the distance by the transfer function.

## Transfer functions (populated here)

| Name | GLSL snippet | Formula | Effect |
|------|--------------|---------|--------|
| `step` | `opacityOfStep` | `d < 0.0 ? 1.0 : 0.0` | crisp solid (the Phase 2 default) |
| `linear` | `opacityOfLinear` | `clamp(1.0 − d/ε, 0.0, 1.0)` | soft band around the zero-surface |
| `sigmoid` | `opacityOfSigmoid` | `1.0 − 1.0/(1.0 + exp(−d/ε))` | smooth soft edge |

Knobs:
- Per-object `opacity` doubles as the falloff breadth `ε` for non-`step`
  transfers.
- Optional viewer-level `density` scale `σ₀` for the volumetric path.

## Files

- New: `py/pytanga/viz/sdf/opacity.py` (Python enum + metadata, mirroring the
  Phase 3 `distance.py` contract)
- New: `py/pytanga/viz/templates/sdf/algebra/opacities.glsl` (GLSL snippets
  keyed by name, mirroring `distances.glsl`)
- Modify: `py/pytanga/viz/templates/sdf/sdf_viewer.js` (populate `activeOpacity`
  and the recompile hook that already exists)
- Modify: `py/pytanga/viz/sdf/visualizer.py` (setter emitting the config
  message)

## Steps

- [ ] Populate the opacity registry (no new mechanism):
  - [ ] `opacity.py` enum: `STEP`, `LINEAR`, `SIGMOID`; `default()` → `STEP`.
  - [ ] `opacities.glsl`: `opacityFuncs` map with `linear`/`sigmoid` snippets.
  - [ ] Wire `sdf_viewer.js` `activeOpacity` (default `"step"`) to the existing
        `buildProgram`/recompile hook.
- [ ] Emit the `opacityOf(...)` snippet through the existing Phase 8 builder
      (replacing the Phase 2 `step` stub only when a non-default transfer is
      active).
- [ ] Surface path: multiply the resolved color alpha by the per-object
      `opacity` factor, then by `opacityOf(d)`.
- [ ] Volumetric path: for non-`step` transfers, accumulate
      `1 − exp(−σ·Δt)` along the ray using `opacityOf(d)` as the density and
      the per-object `ε` as the falloff.
- [ ] Expose `SdfVisualizer.opacity_transfer` setter and a per-object
      `opacity`/`thickness` style value.

## Unit tests

File: `py/tests/viz/sdf/test_opacity.py`

- [ ] `test_enum_values` — every `OpacityTransfer` value string is a valid,
      known key (matches the JS registry names).
- [ ] `test_default_is_step` — `OpacityTransfer.default()` returns `STEP`.
- [ ] `test_params_metadata` — `linear`/`sigmoid` require an `ε`; `step`
      requires none.
- [ ] `test_snippet_purity` — generated snippets contain no `main()`, no
      algebra/entity branch keywords.

## Verification

- [ ] Default (`step`) renders identically to Phase 2/8 with no behavior
      change — confirming this is additive, not a refactor.
- [ ] Toggling `step` ↔ `linear` ↔ `sigmoid` recompiles the shader and updates
      the render via the existing three-axis cache.
- [ ] `linear`/`sigmoid` produce a soft/translucent edge whose breadth follows
      the per-object `opacity` (`ε`).
- [ ] A volumetric scene accumulates opacity along the ray (soft volume look).
- [ ] No `if(opacity…)` branches remain in the generated shader (string
      assertion).
- [ ] `uv run pytest py/tests/viz/sdf/test_opacity.py` passes.
