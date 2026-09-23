# Phase 6 — `Frustum` re-parameterization

## Goal

Re-parameterize `Frustum` so it carries intrinsic shape + placement (not raw
corners), so it participates in transform placement and diffing like the other
entities.

## Files

- Edit: `py/pytanga/geometry/entities/frustum.py` (class + `from_camera`)
- Edit: `py/pytanga/viz/serializer.py` (`_serialize_frustum`)
- Edit: `py/pytanga/viz/_decompose.py` (Frustum → transform + shape)
- Edit: `py/pytanga/viz/templates/renderers/frustum.js` (canonical frustum)
- Edit: `py/tests/geometry/test_frustum.py`, `py/tests/viz/test_frustum.py`

## Steps

- [x] **6.1 — re-parameterize `Frustum`**
  - Replace `near`/`far` corner tuples with: `origin: Point`, `axis: Direction`,
    `horizontal: Direction` (the horizontal axis of the far plane; vertical is
    derived `axis × horizontal`), `near: float` (distance origin → first plane;
    `<= 0` ⇒ apex at origin), `far: float` (distance origin → second plane),
    `far_half_width: float`, `far_half_height: float`. The first (near) plane
    half-extents are computed by similar triangles
    (`near/far * far_half_*`).
  - Keep an `apex` property (near `<= 0`) and rework `from_camera` to compute
    these from `position`/`target`/`up`/`fov`/`intrinsics` (reuse its existing
    `axis`/`right`/`true_up`/`half_extents` math).

- [x] **6.2 — serializer + decompose**
  - `_serialize_frustum` emits shape (`near`, `far`, `half_width`, `half_height`)
    only; `_entity_decompose` maps `origin` + `axis` + `horizontal` → the
    `Transform` (position + quaternion), so placement rides on the node
    transform and shape is diffable.

- [x] **6.3 — canonical frustum renderer**
  - `createFrustum` draws a canonical frustum: apex at origin (or near plane at
    `+Y near`), far plane at `+Y far`, with the given half-extents, in local
    space; the node transform places/orients it. Remove the corner-based
    near/far handling; keep `fill`/outline style.

- [x] **6.4 — tests**
  - Update geometry + serializer tests to the new fields; assert `from_camera`
    yields the expected origin/axis/near/far/half-extents and that the
    serializer output is shape-only with placement in `transform`.

## Validation

`uv run pytest py/tests/geometry/test_frustum.py py/tests/viz/test_frustum.py py/tests/viz/test_frustum_style.py -q`

## Notes

- Keep `Frustum` a viz-only dataclass (no MV) — same contract as today.
- `from_camera`'s `near <= 0` apex path maps to `near <= 0` (apex at origin),
  preserving existing behavior (`test_frustum.py` expectations are updated to
  the new field set).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
