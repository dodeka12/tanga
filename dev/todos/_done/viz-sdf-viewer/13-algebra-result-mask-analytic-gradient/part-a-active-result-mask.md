# Part A — Backend: active result mask

**Status:** Done · [Overview](README.md) · Depends on: — · Feeds: Part B

## Goal

Shrink each `mv_sdf` object's `M` matrix from the full result algebra
(`2^dim × NP`) to the *exact* non-zero result blades plus the scalar and
pseudoscalar blades. This cuts `u_M` by ~6.5× for the demo (608 → 93 floats)
with no change to the rendered distance.

## Context

`embed_entity_mv` currently uses `result_mask = BladeMask(alg, _result_ids(alg))`
(the full algebra), producing `M` with mostly-zero rows. The exact output mask
already exists — `product_blade_mask(point_mask, entity_mask, product)` — and is
the same function `product_tensor(..., c_mask=None)` uses internally.

## Design notes

- The result mask is `product_blade_mask(...) ∪ {0, pseudoscalar_id}`. The two
  extra blades are structurally zero when an entity doesn't produce them, so
  they contribute nothing to any distance function; keeping them means the
  scalar always sits at slot `0` and `slot_pseudo` is always valid (never `-1`).
- `slot_pseudo == len(result_ids) - 1` still holds (the pseudoscalar is the
  largest blade id).
- No `slot_scalar` wire field is needed (the scalar is always slot `0`, as the
  frontend already assumes).

## Files

- `py/pytanga/viz/sdf/algebra_embedding.py`
- `py/pytanga/viz/sdf/calibration.py`
- (no change expected) `py/pytanga/viz/sdf/serializer.py` — `**wire` forwards new fields

## Steps (each individually testable)

### A1 — active result mask in `embed_entity_mv`

- [x] Import `product_blade_mask` from `pytanga.blade_mask.predict`.
- [x] Replace `result_mask = BladeMask(alg, _result_ids(alg))` with
      `result_mask = BladeMask(alg, sorted(set(product_blade_mask(point_mask, entity_mask, product=product).ids) | {0, alg.pseudoscalar_id}))`.
- [x] `slot_pseudo = result_ids.index(alg.pseudoscalar_id)` (now always valid).
- [x] Remove the now-unused `_result_ids` helper and update the module docstring
      (the "full result mask" decision is superseded).
- **Verify:** `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py -q`
  (existing `test_m_reconstruction` / `test_shape_and_ordering` / `test_p3_trivector`
  / `test_normalize_scales` must stay green — they don't assert a full-algebra size).

### A2 — calibration on the masked vector

- [x] `distance_value(r, slot_pseudo, distance, result_ids=None)`: when
      `result_ids` is `None`, default to `list(range(len(r)))` (full-layout
      backward compatibility). Fix the `grade` branch to use the *blade* grade
      `bin(result_ids[i]).count("1")` instead of the slot index `bin(i)`.
      `scalar_pseudo`/`magnitude`/`scalar`/`component` stay unchanged (scalar at
      `r[0]`, pseudo at `r[slot_pseudo]`).
- [x] `evaluate_sdf` passes `result_ids=wire["result_ids"]` into `distance_value`.
- **Verify:** `uv run pytest py/tests/viz/sdf/test_calibration.py -q` (existing
      `test_distance_value_matches_reference`, `test_sign_observed`,
      `test_zero_set_matches_analytic_plane`, `test_scale_calibration_pga3`, etc.
      must stay green — the active-mask `scalar_pseudo` value is unchanged).

### A3 — serializer passthrough (verify only)

- [x] Confirm `serialize_mv` (`**wire`) already forwards `result_ids` and
      `slot_pseudo` unchanged — no code change expected.
- **Verify:** `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py::test_thickness_wire py/tests/viz/sdf/test_algebra_embedding.py::test_soft_opacity_wire -q`.

## Tests to add / update

- Add `test_active_result_mask` (in `test_algebra_embedding.py`): for the four
  demo entities, `wire["result_ids"] == sorted(set(product_blade_mask(...).ids) |
  {0, pseudoscalar_id})`, and the active `M` equals the full `M` with its
  all-zero rows dropped.
- Add a `grade` case to `test_distance_value_matches_reference` (in
  `test_calibration.py`) exercising `result_ids`-aware grade selection.

## Verification

- [x] `uv run pytest py/tests/viz/sdf/test_algebra_embedding.py py/tests/viz/sdf/test_calibration.py -q`
- [x] Spot-check: `embed_entity_mv` on the demo entities reports `u_M`-relevant
      `M` lengths 28 / 20 / 10 / 35 (see overview baselines).
