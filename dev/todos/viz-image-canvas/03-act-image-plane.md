# Phase 3 — `ActImagePlane` interactive object

## Goal

An `ActSceneObject` whose entity is the image plane, so the frontend raycasts
the plane and reports pixel-coordinate hits/drags through the existing
`interaction:*` pipeline.  Reuses the documented `ActPoint`/`drag_anchor` pattern.

## Files

- Edit: `py/pytanga/viz/_active.py` (add `ActImagePlane`)
- New: `py/tests/viz/test_act_image_plane.py`
- Edit: `py/pytanga/viz/__init__.py` (re-export `ActImagePlane`)

## Steps

- [ ] **3.1 — `ActImagePlane(ActSceneObject)` in `_active.py`**
  - Constructor takes the `ImageView` (or its plane entity) plus
    `handler`/`on_drag_start`/`on_drag_end`/`on_click` like `ActPoint`.
  - `entity` property returns the image plane geometry (a `Plane` sized
    `frame`), placed in the image plane frame (z=0, pixel coords).
  - `interaction_config` registers a left-button drag on `DragMode.XY_PLANE`
    (the image's own plane) and an optional `CLICK` trigger (ctrl-modifier
    variant supported via `InteractionTrigger`).

- [ ] **3.2 — `drag_anchor(ray_origin, ray_direction) -> Point`**
  - Return the ray↔z=0 plane intersection (linear solve); the resulting
    `world_position` is already in pixel coordinates (frame from the README).

- [ ] **3.3 — re-export + tests**
  - Re-export `ActImagePlane`.
  - `py/tests/viz/test_act_image_plane.py`: `drag_anchor` hits the correct point
    for known ray/plane cases; `interaction_config` produces the expected
    `InteractionTrigger` (button + modifiers + `XY_PLANE`).

## Validation

`uv run pytest py/tests/viz/test_act_image_plane.py -q && uv run ruff check py/pytanga/viz/_active.py py/tests/viz/test_act_image_plane.py`

## Notes

- Do not add a new `DragMode` — `XY_PLANE` is the image plane in the dedicated
  2D scene.
- `ActImagePlane` imports `ImageView` lazily (inside methods) to avoid a
  circular import with `_image_view.py`.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
