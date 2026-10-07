# Phase 5 — Example apps round-trip `normal`/rotation

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This only updates example code to use the new
> `normal` parameter; no architecture change.

## Goal

Fix the two labelling example apps so converting a loaded labelme `Ellipse`/
`Rectangle2D`/`Circle` into its `Act*` preserves the shape's plane instead of
collapsing to `angle = math.atan2(du.y, du.x)` (which drops the out-of-plane
component).

## Files

- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/examples/apps/image_labeling_app.py`

## Steps

- [x] **5.1 — `calibrated_labeling_app.py` `_act_from_entity`.**
  - `Circle` → `ActCircle(center=..., radius=..., normal=entity.normal, on_click=select)`.
  - `Rectangle2D` → `ActRectangle2D(center=..., size=..., angle=entity.angle,
    normal=entity.normal, on_click=select)`.
  - `Ellipse` → `ActEllipse(center=..., radius_u=..., radius_v=..., angle=<in-plane>,
    normal=entity.normal, on_click=select)`.

- [x] **5.2 — Recover the ellipse angle from `dir_u`.**
  - `Rectangle2D` stores rotation as `angle`, so it passes straight through;
    `Ellipse` stores rotation as `dir_u`/`dir_v`, so recover the angle in the
    plane: import `_plane_basis` from `pytanga.viz._active` (the codebase already
    imports `_default_drag_triggers` from `_active`), build
    `u0, v0 = _plane_basis(entity.normal)`, then
    `angle = math.atan2(du·v0, du·u0)` with `du = entity.dir_u or u0`.

- [x] **5.3 — `image_labeling_app.py` `_act_from_entity`.**
  - Apply the same three conversions (its entities lie on `z = 0`, so
    `normal=+z` and the in-plane angle reduce to the current behaviour, but the
    code should no longer hardcode `atan2(du.y, du.x)`).

- [x] **5.4 — Smoke validation.**
  - Run the calibrated-labelling example's automated test (already exercises the
    labelme → `Act*` conversion path) and lint.

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q && uv run ruff check py/examples/apps/calibrated_labeling_app.py py/examples/apps/image_labeling_app.py`

## Notes

- The `Ellipse` in-plane angle can also be written inline (cross-product basis),
  but reusing `_plane_basis` keeps a single source of truth for the reference
  axis.
- `calibrated_labeling_app.py` uses a `CalibratedPlaneMapper` whose `normal` is
  the optical axis — passing that `normal` through is what keeps the edited
  ellipse on the depth plane.
