# Phase 12 — Opacity transfer functions: non-`step` transfers + volumetric

**Status:** Planned

## Goal

Populate the opacity transfer axis with the full function set and the
volumetric accumulation path. The registry mechanism and the `opacityOf` call
site already exist (Phase 2 stubs `opacityOf` as `step`; Phase 3 establishes
the shared registry; Phase 8 emits the snippets through the single-`map()`
assembly with a structure-vs-data rebuild split). **This phase adds
functionality, not a refactor.**

## Already in place (no rework here)

- Phase 2: an `opacityOf(float d)` call site in the shading path, wired to the
  `step` implementation (with `SDF_EPSILON` band handling), and the per-object
  `opacity` factor applied as the surface alpha multiplier in `shade()`.
- Phase 3: the shared per-axis registry contract (Python enum ↔ JS
  `Map<name, {params, snippet}>` ↔ viewer `active*` recompile hook).
- Phase 6: `SdfVisualizer.opacity` property/setter emitting the
  `sdf_viewer_config` message, and `activeOpacity` + the `rebuildProgram()` hook
  in `sdf_viewer.js` (default `"step"`).
- Phase 8: the single-`map()` assembly with a structure-vs-data rebuild split;
  `opacityOf` is emitted through that assembly (replacing the Phase 2 `step`
  stub only when a non-default transfer is active).

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
- New: `py/pytanga/viz/templates/sdf/algebra/opacities.js` (GLSL snippets
  keyed by name — a `.js` module mirroring `algebra/distances.js`, not a
  `.glsl` file)
- Modify: `py/pytanga/viz/templates/sdf/sdf_viewer.js` (emit the selected
  `opacityOf` snippet through the Phase 8 assembly; `activeOpacity` already
  exists)
- Modify: `py/pytanga/viz/sdf/visualizer.py` (the `opacity` property/setter
  and the `sdf_viewer_config` message already exist)

## Steps

- [ ] Populate the opacity registry (no new mechanism):
  - [ ] `opacity.py` enum: `STEP`, `LINEAR`, `SIGMOID`; `default()` → `STEP`.
  - [ ] `algebra/opacities.js`: `opacityFuncs` map with `linear`/`sigmoid`
        snippets (mirroring `algebra/distances.js`).
  - [ ] Wire `sdf_viewer.js` `activeOpacity` (default `"step"`) to the existing
        `rebuildProgram()` hook (it already triggers a rebuild on change).
- [ ] Emit the `opacityOf(...)` snippet through the existing Phase 8 builder
      (replacing the Phase 2 `step` stub only when a non-default transfer is
      active).
- [ ] Surface path: multiply the resolved color alpha by the per-object
      `opacity` factor, then by `opacityOf(d)`.
- [ ] Volumetric path: for non-`step` transfers, accumulate
      `1 − exp(−σ·Δt)` along the ray using `opacityOf(d)` as the density and
      the per-object `ε` as the falloff.
- [ ] `SdfVisualizer.opacity` setter already exists; add the per-object
      `opacity`/`thickness` style value as the `ε` falloff knob.

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
      the render via the Phase 8 structure-vs-data rebuild split.
- [ ] `linear`/`sigmoid` produce a soft/translucent edge whose breadth follows
      the per-object `opacity` (`ε`).
- [ ] A volumetric scene accumulates opacity along the ray (soft volume look).
- [ ] No `if(opacity…)` branches remain in the generated shader (string
      assertion).
- [ ] `uv run pytest py/tests/viz/sdf/test_opacity.py` passes.
