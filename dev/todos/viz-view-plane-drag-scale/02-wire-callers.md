# Phase 2 — Wire the view direction into both callers

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  No architecture change; this passes the new
> `forward` argument at the two existing call sites.

## Goal

Pass the camera's view direction into `screenWorldScale` from the drag path and
the marker-sizing path so both actually use depth.

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`
- Edit: `py/pytanga/viz/templates/views/three-view.js`

## Steps

- [x] **2.1 — `interaction.js::_computeScreenPlaneVectors`.**
  - Reorder so `right`/`up`/`forward` are extracted (and normalized) before the
    scale is computed.
  - `const viewDir = forward.clone().negate().normalize();`
    (`extractBasis`'s third column is the camera's +Z/backwards; the view
    direction is -Z).
  - Call `screenWorldScale(this.camera, viewportHeight, intersectPoint, viewDir)`.
  - Leave the returned `dist` (`intersectPoint.distanceTo(...)`) unchanged — it
    is stored in `_activeDrag.dist` but never used for scaling.

- [x] **2.2 — `three-view.js::_updateScreenSpaceMarkers`.**
  - Compute `const forward = this.camera.getWorldDirection(new THREE.Vector3());`
    once before the loop.
  - Pass it: `screenWorldScale(this.camera, viewportPx, worldPos, forward)`.

## Validation

`node --check py/pytanga/viz/templates/interaction.js py/pytanga/viz/templates/views/three-view.js`

## Notes

- `getWorldDirection` returns a normalized vector; `extractBasis` columns are
  unit length for cameras with no scale — the `.normalize()` in 2.1 makes it
  robust regardless.
