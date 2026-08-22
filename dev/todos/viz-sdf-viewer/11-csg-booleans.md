# Phase 11 — CSG booleans: positive/negative objects (union/intersection/subtract)

**Status:** Planned

## Goal

Expose SDF set operations as first-class per-object controls: an object can be
`positive` or `negative`, and the compositor folds it into the global SDF as a
`union`, `intersection`, or `subtract`. This lets a user carve a box with a
sphere, intersect overlapping solids, etc.

## Background

A signed distance is negative inside. The three combiners are:

- **union** `min(dA, dB)` — inside either.
- **intersection** `max(dA, dB)` — inside both.
- **difference A − B** `max(dA, −dB)` — inside A, not inside B.

A **negative** object is just its distance negated before folding; by itself it
is an inside-out bubble (a hole), so it is only meaningful combined with a
positive object via `max` (difference).

## Files

- Modify: `py/pytanga/viz/sdf/serializer.py` (emit `combine`/`polarity`)
- Modify: `py/pytanga/viz/sdf/visualizer.py` (accept `combine="subtract"` /
  `polarity="negative"` in `add()`)
- Modify: `py/pytanga/viz/templates/sdf/scene-builder.js` (combine-mode fold)
- Modify: `py/pytanga/viz/templates/sdf/material-table.js` (material preference
  under subtraction)

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

- [ ] Serializer: accept and forward `combine`/`polarity` on both analytic
      entity trees and `mv_sdf` objects (a single `combine` field in the wire
      object).
- [ ] Visualizer API: `add(obj, ..., combine=...)` / `add(obj, ...,
      polarity="negative")`; validate the value and store it as per-object
      metadata emitted in serialization.
- [ ] Scene builder fold:
  - [ ] `union` → `acc = min(acc, d)`; winner's `matId` propagated.
  - [ ] `intersection` → `acc = max(acc, d)`; `matId` from the closer operand.
  - [ ] `subtract` → `acc = max(acc, -d)`; `matId` **forced to the positive
        accumulator's material** (a negative object emits no colored surface).
- [ ] Material table: record which objects are negative so subtraction prefers
      the positive `matId` on carved surfaces.
- [ ] Signedness gate: inspect the active distance function; when
      `intersection`/`subtract` objects exist and the function is unsigned
      (`magnitude`), surface a warning (backend) / reject (frontend).
- [ ] Smooth variants: `smooth_subtract`/`smooth_intersection` blend `matId`
      using the blend factor (Phase 1 vec2 combinators).

## Verification

- [ ] A negative sphere carves a cavity out of a positive box (visual + the
      box's material is visible inside the cavity).
- [ ] Intersection of two overlapping spheres renders only the lens of overlap.
- [ ] Union remains the default and behaves as before.
- [ ] Boolean ops with unsigned `magnitude` are rejected/warned.
- [ ] Changing an object from `positive` to `negative` re-emits the composed
      map and renders correctly without a full scene reload.