# Part C — Tests, docs & changelog

**Status:** Planned · [Overview](README.md) · Depends on: Parts A + B

## Goal

Update the existing tests and smoke checks to the new wire shape and `vec3 map()`
contract, add the new coverage from Parts A/B, and refresh the docs/changelog.

## Files

- `py/tests/viz/sdf/test_algebra_embedding.py`
- `py/tests/viz/sdf/test_calibration.py`
- `py/tests/viz/sdf/test_algebra_eval.py`
- `py/tests/viz/sdf/test_raymarch_shader.py`
- `dev/src/sdf_algebra_smoke.mjs`
- `dev/src/sdf_composer_smoke.mjs`
- `dev/todos/viz-sdf-viewer/README.md` (risks), later the changelog

## Steps (each individually testable)

### C1 — `test_algebra_embedding.py`

- [x] `test_embeds_registry_complete`: drop the `NR:`/`SLOT_PSEUDO:` token checks;
      assert `NP:` + `snippet:` + `gradient:`.
- [x] `test_embed_src_consistency`: drop the `NR:`/`SLOT_PSEUDO:` assertions;
      assert the `gradient` field is present per algebra.
- [x] Add `test_active_result_mask` (from Part A) and confirm existing tests
      (`test_m_reconstruction`, `test_shape_and_ordering`, …) are unchanged.
- **Verify:** `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py -q`

### C2 — `test_calibration.py`

- [x] Add a `grade` case to `test_distance_value_matches_reference` using
      `result_ids`; confirm `scalar_pseudo`/`magnitude`/`scalar` cases unchanged.
- **Verify:** `uv run pytest py/tests/viz/sdf/test_calibration.py -q`

### C3 — `test_algebra_eval.py`

- [x] Assert per-mask `distOf` emission; assert **no** `if (rest` / epsilon
      `if` in generated source; assert the branchless guard string
      (`inversesqrt(rest + float(rest <`).
- **Verify:** `uv run pytest py/tests/viz/sdf/test_algebra_eval.py -q`

### C4 — `test_raymarch_shader.py`

- [ ] `test_algebra_local_gradient_step`: assert `vec3 m = map(p)`,
      `stepSize = d / max(m.z, 1.0);`, no `calcGradientNorm`, no
      `u_ObjectParams[matId].w > -0.5`.
- [ ] Keep `test_volumetric_density_present` (still reads `u_ObjectParams.*`).
- **Verify:** `uv run pytest py/tests/viz/sdf/test_raymarch_shader.py -q`

### C5 — Node smoke checks

- [ ] `dev/src/sdf_algebra_smoke.mjs`: active `result_ids`, smaller `u_M`, the
      `vec2` leaf + per-mask `distOf`, branchless guard present, `if (rest`
      absent.
- [ ] `dev/src/sdf_composer_smoke.mjs`: `vec3 map(vec3 p)`; analytic
      `buildObjectExpr` emits `vec2(…, 1.0)`.
- **Verify:** `node dev/src/sdf_algebra_smoke.mjs && node dev/src/sdf_composer_smoke.mjs`

### C6 — docs & changelog

- [ ] Update `dev/todos/viz-sdf-viewer/README.md` risks (algebra-leaf uniform
      budget → active mask; gradient-scale → analytical step).
- [ ] Write the changelog entry per `dev/workflows/changelog.md`.
- **Verify:** markdown renders; changelog follows the naming/format rules.

## Verification

- [ ] `uv run pytest py/tests/viz/` green (full suite, 598 currently + new).
- [ ] `node dev/src/sdf_algebra_smoke.mjs && node dev/src/sdf_composer_smoke.mjs`
- [ ] `demo_sdf_algebra.py` renders: `u_M` total ~93 floats (was 608), the step
      uses the analytical `|∇d|`, no `if (rest < eps)` in the generated fragment.
