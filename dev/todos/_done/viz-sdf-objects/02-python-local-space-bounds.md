# Phase 2 — Local-space emission + AABB `bound`

## Goal

Emit the SDF `tree` in **object-local space** and compute a conservative
local-space AABB `bound` for the proxy mesh. Together with the node
`transform`, this makes SDF objects animate/interact/parent exactly like mesh
objects (the proxy `Object3D` carries all placement).

## Files

- New: `py/pytanga/viz/sdf/bounds.py` — tree → AABB walker.
- Modify: `py/pytanga/viz/sdf/serializer.py` — local-space emission mode +
  separate placement transform; wire `bound` into the Phase 1 object shape.
- Modify: `py/pytanga/viz/sdf/primitives.py` — if a per-primitive bounds table
  is cleaner co-located here.

## Steps

- [x] **2.1 — Per-primitive local AABB table** (`bounds.py`)
  - Map each primitive `kind` → local half-extent/box (sphere→`radius`;
    box/roundBox→`halfExtents`(+`radius`); ellipsoid→`radii`;
    cappedCylinder→`(halfHeight, radius)`; cylinder→needs an explicit `bound`
    clip; torus→`mainRadius + tubeRadius`; cone/cappedCone→analytic;
    capsule→segment + radii; segment→`a`/`b`; plane→needs an explicit `bound`).
  - Combinators: `union`→union of child AABBs, `intersect`→intersection,
    `subtract`→first child, `group`→fold children, `bound`→its clip box.
  - Apply a node's `transform` (position/rotation) to its child AABB.
  - Return `{"min": [x,y,z], "max": [x,y,z]}` (inflate by `bound_padding`).

- [x] **2.2 — Local-space emission** (`sdf/serializer.py`)
  - Done: re-centres the world tree at the origin (position stripped into the
    placement transform); intrinsic rotation stays on the primitives (a
    uniform, conservative approach for multi-primitive glyphs). The
    user-``transform=`` composition (intrinsic ∘ node transform) is wired in
    Phase 4 alongside the transform update path.
  - Add a `local=True` path that strips intrinsic `position`/`rotation` out of
    the tree (primitives emitted at the origin in local space) and returns the
    **placement transform** separately (position + axis-angle rotation →
    Euler), so the node `Object3D` can apply it.
  - Compose the entity's intrinsic placement with any user `transform=` into the
    single object `transform` field.
  - Keep the world-space `SdfVisualizer` path untouched (no regression).

- [x] **2.3 — Wire `bound` + `transform`** into the Phase 1 object shape
  (replace the temporary identity stubs).

- [x] **2.4 — Tests** (`py/tests/viz/sdf/test_bounds.py`,
  `test_standard_serializer_sdf.py`)
  - `compute_bounds` for sphere/box/torus/union/intersect/subtract/`bound`.
  - A `Sphere(center, r)` serializes to a local tree (no world `position`) with
    `transform.position == center` and a radius-sized `bound`.
  - Infinite `Plane`/`Line` produce a finite `bound` (from the serializer's
    explicit clip) — no `inf`/`nan` in `bound`.

- [x] **2.5 — Validate**
  - `uv run pytest py/tests/viz/sdf/ -q` + `uv run pytest py/tests/viz/ -q`.

## Validation

`uv run pytest py/tests/viz/sdf/ -q` (new bounds + local-space tests green) +
`uv run pytest py/tests/viz/ -q` (no regression).

## Notes

- The AABB must be **conservative** (any over-estimate is fine; under-estimate
  clips the surface). Prefer slightly inflating.
- Local-space emission is the crux of option B; it is what lets the
  `object.update` transform path and `animator.js` tweens work without
  recompiling the shader.
