# Phase 5 — Python wire serializers + dispatch

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture. If this
> work introduces or changes architecture, update the developer docs.

## Goal

Implement the Python side of the wire contract: a line-drawn `Ellipse`, the
missing `ParallelLinePair` and `Cone` serializers, and their `_dispatch_entity`
branches.

## Files

- Edit: `py/pytanga/viz/serializer.py`
- Edit: `py/tests/viz/test_conic_renderers.py`

## Steps

- [x] **5.1 — `_serialize_ellipse` as a 2D line.**
  - Emit `center`, `radiusU`, `radiusV`, `normal`, and the `thickness` style
    field (line width). Remove any slab/wireframe builtins. Match the README wire
    contract.
- [x] **5.2 — `_serialize_parallel_line_pair`.**
  - Mirror `_serialize_line_pair`: emit `line1`/`line2` (`_line_wire`) with
    `kind="ParallelLinePair"` and the `ParallelLinePairStyle` fields.
- [x] **5.3 — `_serialize_cone`.**
  - Emit `vertex` (list), `axis` (list), `halfAngle` (float) from `Cone.vertex`/
    `axis`/`half_angle`, plus `ConeStyle` fields.
- [x] **5.4 — Dispatch branches.**
  - Add `isinstance(entity, ParallelLinePair)` and `isinstance(entity, Cone)`
    branches to `_dispatch_entity` (import both), routed to the new serializers.
- [x] **5.5 — Tests.**
  - Serialize an `Ellipse` (assert no wireframe keys, `thickness` present);
    serialize a `ParallelLinePair`; serialize a `Cone` (assert `halfAngle`).

## Validation

`uv run pytest py/tests/viz/test_conic_renderers.py -q`

## Notes

- `Cone` currently has no serializer and no `_dispatch_entity` branch; after this
  phase `refine(Quadric3D)` can produce a drawable `Cone`.
- Keep content fields camelCase (`halfAngle`, `radiusU`, `radiusV`) and style
  fields snake_case, matching the existing serializers.
