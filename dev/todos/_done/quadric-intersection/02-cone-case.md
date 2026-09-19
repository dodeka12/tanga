# Phase 2 — Cone (rank-3) member → sampled `Curve`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `geometry-module-layering.md`) for the subsystem(s) this work touches, so the
> new code aligns with the documented architecture.  If this work introduces or
> changes architecture, update the developer docs.

## Goal

Handle a rank-3 **cone** degenerate member in `intersect_quadrics`: parametrize
the cone by its rulings and intersect each ruling with the other quadric, sampling
the quartic intersection into a `Curve`.  This closes the cone branch left as
`NotImplementedError` in phase 1.

## Files

- Edit: `py/pytanga/quadric/_intersection.py`
- Edit: `py/tests/geometry/test_conic_analysis.py`

## Steps

- [x] **2.1 — Cone vertex + base conic**
  - `_cone_vertex(C)`: the null vector of the 4×4 rank-3 matrix `C`
    (smallest singular vector of `C` via `np.linalg.svd`); raise if `C` is not a
    real cone (indefinite signature).
  - Pick a base plane **not** through the vertex (e.g. the plane through the
    origin perpendicular to the cone axis, or a coordinate plane offset from the
    vertex).  Intersect `C` with that plane → a 2D conic (reuse the
    `_conic_from_plane_quadric` machinery from phase 1 with the base plane).
- [x] **2.2 — `_sample_conic_2d(conic, n)`** (shared, also used by phase 4)
  - Sample a 2D `Conic` into ~`n` ordered points in its own plane frame.  Refine
    the `Conic` first (`refine`) and sample by kind (ellipse → angular loop,
    hyperbola → two branches, parabola → clipped extent, line pair → each line as
    a segment), matching the existing frontend samplers' behaviour; keep it
    numpy-only.  Return a list of `(s, t)` tuples.
- [x] **2.3 — Ruling intersection → curve points**
  - For each base-conic point `b` (sampled via 2.2): the ruling is the line
    `x(t) = v + t·(b − v)` (vertex `v`).  Substitute into `x_Hᵀ Q1 x_H = 0` →
    quadratic in `t`; real roots → 3D points (mapped back via the base-plane
    frame).  Collect all points ordered by the base-conic parameter (two points
    per ruling).
  - Dedupe near-coincident points and map to `Point`s → a `Curve`.
- [x] **2.4 — Wire into `intersect_quadrics`**
  - Replace the phase-1 `raise NotImplementedError("cone member …")` branch: when
    no plane-pair/plane member exists but a real cone member does, return the
    sampled `Curve`.
- [x] **2.5 — Tests**
  - Two quadrics whose pencil has a real cone member (e.g. a sphere and an
    offset ellipsoid chosen so the intersection is non-planar) →
    `intersect_quadrics` returns a `Curve` with a non-empty point tuple, and
    every returned point satisfies both `xᵀQ1x ≈ 0` and `xᵀQ2x ≈ 0` (residual
    check).
  - Sphere ∩ plane (a planar circle): still returns the plane-pair/plane path
    (exact conic), not a sampled curve.

## Validation

`uv run pytest py/tests/geometry/test_conic_analysis.py -q`

## Notes

- The quartic is a double cover of the base conic (2 roots per ruling), so the
  generic cone case yields an elliptic quartic — sampled, not parametrized.  This
  is expected; the plan only samples it for rendering.
- Multi-component curves are not split (single polyline) — see README non-goals.
- Keep `_sample_conic_2d` importable/usable by the phase-4 serializer (same
  sampling, so the serialized polylines match).
