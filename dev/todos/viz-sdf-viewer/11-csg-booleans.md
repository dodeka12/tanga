# Phase 11 — CSG booleans: positive/negative objects (union/intersection/subtract)

**Status:** Mostly done — the per-object `combine`/`polarity` fold and the
`Composed` per-constituent modes shipped in Phases 5/6b/6c; remaining work is
the signedness gate, smooth variants, and a dedicated test file.

## Goal

Expose SDF set operations as first-class per-object controls: an object can be
`positive` or `negative`, and the compositor folds it into the global SDF as a
`union`, `intersection`, or `subtract`. This lets a user carve one object with
another and intersect overlapping solids, etc.

## Background

A signed distance is negative inside. The three combiners are:

- **union** `min(dA, dB)` — inside either.
- **intersection** `max(dA, dB)` — inside both.
- **difference A − B** `max(dA, −dB)` — inside A, not inside B.

A **negative** object is just its distance negated before folding; by itself it
is an inside-out bubble (a hole), so it is only meaningful combined with a
positive object via `max` (difference).

## Files

- Done: `py/pytanga/viz/sdf/serializer.py` (`_normalize_combine` emits
  `combine`/`polarity`)
- Done: `py/pytanga/viz/sdf/visualizer.py` (`add()`/`update_entity()` accept
  `combine=`/`polarity=`)
- Done: `py/pytanga/viz/templates/sdf/composer.js` (ordered
  union/intersection/subtract fold with the positive accumulator's `matId`
  preferred on subtract)
- Modify (remaining): `py/pytanga/viz/sdf/visualizer.py` + `serializer.py`
  (signedness gate — warn/reject `intersection`/`subtract` under unsigned
  `magnitude`)
- Modify (remaining): `py/pytanga/viz/templates/sdf/composer.js` (smooth
  variants using the Phase 1 `vec2` combinators)

## Combine model

- **Per-object `combine`** ∈ `{union, intersection, subtract}`; shorthand
  `polarity` ∈ `{positive, negative}` maps to `union`/`subtract`. Default is
  `union` (positive).
- Fold order follows insertion order (authoritative scene order), so
  `A (union) …, B (subtract)` means "everything, then carve B out of the
  accumulated result". Grouping/nested CSG is deferred; flat ordered fold in v1.
- **Signedness requirement:** `intersection`/`subtract` require a signed
  distance function (`scalar_pseudo` default, or `scalar`). With the unsigned
  `magnitude` mode these operations are rejected/warned.

## Steps

- [x] Serializer: accept and forward `combine`/`polarity` on analytic entity
      trees (a single `combine` field in the wire object). *(the `mv_sdf`
      forwarding lands with Phase 7)*
- [x] Visualizer API: `add(obj, ..., combine=...)` / `add(obj, ...,
      polarity="negative")`; validate the value and store it as per-object
      metadata emitted in serialization.
- [x] Scene builder fold (`composer.js`):
  - [x] `union` → `acc = min(acc, d)`; winner's `matId` propagated.
  - [x] `intersection` → `acc = max(acc, d)`; `matId` from the closer operand.
  - [x] `subtract` → `acc = max(acc, -d)`; `matId` **forced to the positive
        accumulator's material** (a negative object emits no colored surface).
- [x] Material table: subtraction prefers the positive `matId` on carved
      surfaces (the `composer.js` fold keeps the accumulator's material).
- [ ] Signedness gate: inspect the active distance function; when
      `intersection`/`subtract` objects exist and the function is unsigned
      (`magnitude`), surface a warning (backend) / reject (frontend).
- [ ] Smooth variants: `smooth_subtract`/`smooth_intersection` blend `matId`
      using the blend factor (Phase 1 vec2 combinators).

## Unit tests

File: `py/tests/viz/sdf/test_combine.py`

*(`test_sdf_serializer.py::test_serialize_combine_and_polarity` already covers
round-trip; the new file consolidates the combine-specific cases.)*

- [ ] `test_combine_serialized` — `combine`/`polarity` round-trips into the
      wire object for analytic and `mv_sdf` objects.
- [ ] `test_polarity_maps_to_combine` — `positive`→`union`, `negative`→
      `subtract`.
- [ ] `test_signedness_gate` — `intersection`/`subtract` with unsigned
      `magnitude` is rejected/warned.
- [ ] `test_default_is_union` — an object without `combine` defaults to
      `union`.

## Verification

- [ ] A negative sphere carves a cavity out of a positive sphere (visual + the
      positive sphere's material is visible inside the cavity).
- [ ] Intersection of two overlapping spheres renders only the lens of overlap.
- [ ] Union remains the default and behaves as before.
- [ ] Boolean ops with unsigned `magnitude` are rejected/warned.
- [ ] Changing an object from `positive` to `negative` re-emits the composed
      map and renders correctly without a full scene reload.
- [ ] `uv run pytest py/tests/viz/sdf/test_combine.py` passes.
