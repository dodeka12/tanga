# Phase 3 — Entity → `(Transform, shape)` decomposition + diffing

## Goal

Add `_entity_decompose(entity) -> (Transform, shape)` that maps an entity's
placement into a `Transform` and its remaining parameters into canonical shape
fields; wire it into the node and use it to diff shape vs placement in
`set_entity`.

## Files

- New: `py/pytanga/viz/_decompose.py` (imports `Transform` from geometry)
- Edit: `py/pytanga/viz/_nodes.py` (`VizSceneObject.__init__`, `set_entity`)

## Steps

- [x] **3.1 — `_entity_decompose(entity) -> (Transform, dict)`**
  - Implement per-kind mapping per the README canonical contract: `position`
    from `center`/`origin`/`vertex`/`point`; quaternion from `normal`/`axis`/
    `direction` (+ `startDirection`/`dirU`/`dirV`/horizontal axis where a second
    axis fixes the frame); `rotation` (Box/Ellipsoid) → quaternion.
  - Shape dict holds the rest (`radius`, `size`, `radii`, `halfAngle`, `length`,
    `a`, `b`, `p`, `radiusU`, `radiusV`, `angle`, `extent`, …).
  - Non-placement kinds (`PointPath`/`Curve`/`PointSet`, operators, axes/grid,
    sdf/ray/image) return `(Transform(), {})` — they are out of scope.

- [x] **3.2 — node transform init**
  - `VizSceneObject.__init__`: when an `entity` is present and no explicit
    `transform` was passed, set `self.transform` from `_entity_decompose`.
  - `set_entity` re-derives `self.transform` from the new entity.

- [x] **3.3 — `set_entity` diffing with epsilon**
  - Compare old/new `(Transform, shape)`; mark `"transform"` when placement
    changed, `"content"` when shape changed, `"full"` on kind change (existing
    rule), both when both changed.
  - Add a **settable epsilon** (default `1e-9`, e.g. a `Scene`/`Visualizer`
    parameter threaded to `VizSceneObject`); positions/quaternion components/
    shape scalars compare with `abs(a - b) <= eps`, arrays with
    `np.allclose(atol=eps)`, so FP noise does not recreate meshes.

- [x] **3.4 — tests**
  - Decompose `Circle`/`Cylinder`/`Box`/`Line`/`Arc`/`Plane` into the expected
    `(Transform, shape)`; assert `set_entity` marks `transform` on a
    center-only change, `content` on a radius-only change, `full` on kind
    change, and neither within `eps`.

## Validation

`uv run pytest py/tests/viz -q`

## Notes

- The `geometry.transforms._EPS = 1e-12` constant is for matrix math and is **not**
  settable; the diffing epsilon here is a separate, coarser, settable value.
- `alignCenter` (Cylinder) couples position to `length`; decompose reads all
  fields so a length change recomputes position (→ both `transform` + `content`
  when both actually move).

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
