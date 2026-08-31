# Phase 4 — Docs & changelog

## Goal

Document the ideal-drag behaviour and the new hook, and record the change in
the branch changelog.

## Files

- Edit: `docs/py/viz/entities/active-elements/act-point.md`
- Edit: `docs/py/viz/entities/active-elements/index.md` (if it lists the
  `ActSceneObject` API surface)
- Edit: `docs/changelog/2026-08-31_fix-scene-alert.md` (branch changelog)

## Steps

- [x] **4.1 — Document the ideal anchor**
  - In `act-point.md`, add a short subsection: interactive objects drag from an
    "ideal anchor" computed from the ideal geometry; `ActPoint.drag_anchor`
    returns the point centre, so the mesh-surface offset (e.g. the z-jump when
    dragging on `XY_PLANE` while looking down the z-axis) no longer appears.
  - Note the hook is the extension point for future active entities (a circle
    drawn as a torus anchors on the nearest point of the ideal circle).
  - Note that the drag also re-anchors the pixel→world scale onto the ideal
    point (pixel deltas are buffered until the anchor arrives and converted once
    at the anchor's depth), so a future torus/circle or sphere drags at the
    correct speed with no per-class handling.

- [x] **4.2 — Changelog**
  - Append to `docs/changelog/2026-08-31_fix-scene-alert.md` (the branch
    changelog; it already has `## New Features`, `## Breaking Changes`, and
    `## Bug Fixes` sections):
    - Add a bullet at the end of `## New Features`:
      `ActSceneObject.drag_anchor(ray_origin, ray_direction)` ideal-drag hook
      plus the `interaction:drag_anchor` backend reply (drag anchored on the
      ideal geometry, per type).
    - Add a bullet at the end of `## Bug Fixes`: `ActPoint` XY/XZ/YZ-plane
      drags were anchored on the rendered mesh surface; the ideal anchor now
      keeps the point on the constraint plane (no spurious out-of-plane
      component).

## Validation

`uv run mkdocs build --strict`

## Notes

- Rename the changelog to its hash-based form and index it in
  `docs/changelog/index.md` only at PR time (`dev/workflows/pull-request.md`).
