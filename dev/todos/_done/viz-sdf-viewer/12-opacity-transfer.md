# Phase 12 — Opacity transfer functions: non-`step` transfers + volumetric

**Status:** Implemented (surface path) — the full opacity registry, the
`opacityOf` emission through the Phase 8 assembly, and the surface path landed
here; the volumetric accumulation path is deferred (optional follow-on).

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

*(Note: the Phase 2 `opacityOf` seam only covers **surface** opacity — the
snippet swaps in without touching the raymarch body. **Volumetric** opacity
needs a separate absorption march loop in the raymarch `main()` that integrates
`σ(p)` along the ray; it is a new code path, not a snippet swap, and remains
optional.)*

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

- [x] Populate the opacity registry (no new mechanism):
  - [x] `opacity.py` enum: `STEP`, `LINEAR`, `SIGMOID`; `default()` → `STEP`.
  - [x] `algebra/opacities.js`: `opacityFuncs` map with `linear`/`sigmoid`
        snippets (mirroring `algebra/distances.js`).
  - [x] Wire `sdf_viewer.js` `activeOpacity` (default `"step"`) to the existing
        `rebuildProgram()` hook (it already triggers a rebuild on change).
- [x] Emit the `opacityOf(...)` snippet through the existing Phase 8 builder
      (`emitOpacityFunction()` in `sdf_viewer.js`; the Phase 2 step stub was
      removed from `raymarch.glsl` and moved into `opacities.js`).
- [x] Surface path: `col *= opacityOf(d, ε)` where the per-object `opacity` is
      `ε` — the surface alpha for `step`, the soft-edge breadth for
      `linear`/`sigmoid`.
- [ ] Volumetric path: for non-`step` transfers, accumulate
      `1 − exp(−σ·Δt)` along the ray — **deferred** (a second absorption march
      loop in the raymarch `main()`, not a snippet swap; optional follow-on).
- [x] `SdfVisualizer.opacity` setter now uses the `OpacityTransfer` enum and
      accepts a string or enum member.

## Unit tests

File: `py/tests/viz/sdf/test_opacity.py`

- [x] `test_enum_values` — every `OpacityTransfer` value string is a valid,
      known key (matches the JS registry names).
- [x] `test_default_is_step` — `OpacityTransfer.default()` returns `STEP`.
- [x] `test_params_metadata` — `linear`/`sigmoid` require an `ε`; `step`
      requires none.
- [x] `test_snippet_purity` — generated snippets contain no `main()`, no
      algebra/entity branch keywords.

## Verification

- [x] Default (`step`) preserves the Phase 2/8 behavior — the `step` transfer
      is `d < SDF_EPSILON ? ε : 0` (the per-object α), so the render is
      unchanged — confirming this is additive, not a refactor.
- [x] Toggling `step` ↔ `linear` ↔ `sigmoid` recompiles the shader (the
      structure key includes `activeOpacity`).
- [x] `linear`/`sigmoid` produce a soft edge whose breadth is the per-object
      `opacity` (`ε`) — surface path.
- [ ] A volumetric scene accumulates opacity along the ray (soft volume look) —
      deferred (optional follow-on).
- [x] No `if(opacity…)` branches remain in the generated shader (the active
      transfer is a registry lookup).
- [x] `uv run pytest py/tests/viz/sdf/test_opacity.py` passes (6 passed).
