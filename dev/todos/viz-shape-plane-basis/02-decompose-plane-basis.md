# Phase 2 — Deterministic planar frame in `_decompose`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the "Decomposition" section).  This
> stays inside the existing `_entity_decompose` contract; no architecture change.

## Goal

Replace the degenerate `quat_from_vectors((0,0,1), normal)` frame used by
`Rectangle2D` and `Ellipse` with a deterministic `_frame_quaternion(base, normal)`
frame whose base is `dir_u` (when given) or `_plane_basis_u0(normal)` — the same
basis the `Act*` handles use.  This fixes Finding 1.

## Files

- Edit: `py/pytanga/viz/_decompose.py`
- Edit: `py/tests/viz/test_entity_decompose.py`

## Steps

- [x] **2.1 — `_plane_basis_u0(normal)` helper.**
  - Add a module-level numpy helper mirroring `_active._plane_basis`:
    `n = _unit(normal)`; `ref = (0,1,0)` (use `(1,0,0)` when `abs(ref·n) > 0.999`);
    return `_unit(np.cross(ref, n))`.
  - Cross-reference `_active._plane_basis` in the docstring/comment (they must
    stay in sync).

- [x] **2.2 — `Rectangle2D` frame.**
  - `base = _dir(entity.dir_u) if entity.dir_u is not None else _plane_basis_u0(_dir(entity.normal))`;
    `q = _frame_quaternion(base, _dir(entity.normal))`.
  - Keep shape `{"size", "angle"}` unchanged.

- [x] **2.3 — `Ellipse` frame + `angle` in shape.**
  - Same `base`/`q` as 2.2 (replace the `dir_u is not None` branch *and* the
    `quat_from_vectors` fallback).
  - Shape becomes `{"radiusU", "radiusV", "angle": float(entity.angle)}`.

- [x] **2.4 — Tests.**
  - Rectangle2D with `normal ≈ -z` (e.g. `Direction(-0.009,-0.009,-1.0)`) maps
    local `+x` to `_plane_basis(normal)[0]` (compare against
    `_active._plane_basis`).
  - `dir_u` override is respected (local `+x` maps to the given in-plane axis,
    orthogonalized against `normal`).
  - Ellipse: `angle` appears in the shape; `dir_u is None` uses the
    `_plane_basis` frame; `dir_u` given still works.
  - Parity check: `_decompose._plane_basis_u0(n)` == `_active._plane_basis(n)[0]`
    for `+z`, `-z`, and two tilted normals.

## Validation

`uv run pytest py/tests/viz/test_entity_decompose.py -q`

## Notes

- `_frame_quaternion` already orthogonalizes `x` against `z` and derives `y =
  z × x`, which is exactly `_plane_basis`'s `v0 = n × u0` — so body and handles
  agree by construction.
- `Circle` is left on `quat_from_vectors` (its body is symmetric; changing it
  would only churn).  `Disk`/`PartialDisk` are out of scope (see README).
