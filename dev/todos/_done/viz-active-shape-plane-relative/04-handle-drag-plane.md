# Phase 4 — `VIEW_PLANE` handles + full-3D translate for the point-based shapes

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This reuses the existing `DragMode.VIEW_PLANE`
> already used by `ActPoint` and `InteractionSurface`; no new interaction model.

## Goal

Switch every composite's child handles from `DragMode.XY_PLANE` to
`DragMode.VIEW_PLANE`, and finish the full-3D translation for the free-form
point-based shapes (`ActPolygon`, `ActLine`).  `ActPoint` itself is already
correct and needs no change.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py`
- Edit: `py/tests/viz/test_act_ellipse.py`
- Edit: `py/tests/viz/test_act_circle.py`
- Edit: `py/tests/viz/test_act_polygon.py`
- Edit: `py/tests/viz/test_act_line.py`

## Steps

- [x] **4.1 — `VIEW_PLANE` handles.**
  - In `_spawn_handles()` of `ActRectangle2D` (3 sites), `ActEllipse` (3),
    `ActCircle` (2), `ActPolygon` (2), `ActLine` (2), change every
    `drag_mode=DragMode.XY_PLANE` to `drag_mode=DragMode.VIEW_PLANE`.

- [x] **4.2 — Full-3D `_translate_by` for the point-based shapes.**
  - `ActPolygon._translate_by`: map `p → Point(p.x + delta.x, p.y + delta.y, p.z + delta.z)`.
  - `ActLine._translate_by`: `start + delta` and `end + delta` (all three components).
  - (Rectangle/Ellipse/Circle `_translate_by` were already made full-3D in
    Phases 1–3; re-confirm they add `delta.z`.)

- [x] **4.3 — Tests.**
  - For each composite, assert each spawned child handle's `interaction_config`
    exposes exactly one unmodified DRAG trigger with
    `drag_mode == DragMode.VIEW_PLANE` (no modifier-plane triggers).
  - `ActPolygon`/`ActLine`: assert `_dispatch_translate` with a
    `world_delta` whose `z != 0` moves points by that delta (existing
    `test_translate_preserves_z` still passes with `delta.z == 0`).
  - `ActPoint` standalone: confirm no regression (existing `test_active.py`
    `TestDragModeConstraint` stays green).

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py py/tests/viz/test_act_circle.py py/tests/viz/test_act_polygon.py py/tests/viz/test_act_line.py py/tests/viz/test_active.py -q`

## Notes

- `VIEW_PLANE` = "plane ⟂ camera view at initial depth".  For a calibrated
  camera viewing along its optical axis this is parallel to (and tangent at) the
  depth plane, so handles stay on the surface plane — the whole point of
  `_input/pytanga-act-ellipse-world-xy-plane-only.md`.
- In `space_dim == 2`, `VIEW_PLANE` and `XY_PLANE` coincide, so flat labelling is
  unaffected.
- Passing `drag_mode=VIEW_PLANE` (rather than `None`) keeps a single trigger and
  avoids the modifier-switched XZ/YZ escapes that would let a handle leave the
  shape's plane.
