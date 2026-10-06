# Phase 2 — Composite size mappings through `pixel_scale`

## Goal

Add `pixel_scale` to the `_ActWithHandles` composites and route the
handle-derived and min-clamp distances through it, fixing the ellipse start
radius, the rotate-icon overlap, and the polygon auto-close snapping.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/tests/viz/test_act_circle.py`, `test_act_ellipse.py`,
  `test_act_rectangle2d.py`, `test_act_polygon.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **2.1 — Add `pixel_scale` to `_ActWithHandles`**
  - Stored as `self._pixel_scale` (default `1.0`); `set_pixel_scale(value)` sets
    it (no immediate re-clamp) and `_handle_world_size()` converts the handle
    px size to world units.
- [x] **2.2 — `create_from_points` clamps to the minimum (ellipse, rectangle, circle)**
  - `ActEllipse` / `ActRectangle2D` / `ActCircle` read `min_radius` / `min_size`
    from `kwargs` and clamp the computed radius/size before constructing.
- [x] **2.3 — Polygon auto-close tolerance uses the scale**
  - `ActPolygon._effective_close_tolerance` now returns
    `2.0 * self._handle_world_size()` (the explicit `close_tolerance` override
    path is kept).
- [x] **2.4 — Rotate-handle offset gets a pixel minimum**
  - `ActRectangle2D` / `ActEllipse` use
    `offset = max(0.25 * max(hw, hh), 2.0 * self._handle_world_size())`.
- [x] **2.5 — Regression tests**
  - Ellipse/rectangle `create_from_points` min-clamp; polygon tolerance follows
    `pixel_scale`.

## Validation

`uv run pytest py/tests/viz/test_act_circle.py py/tests/viz/test_act_ellipse.py py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_polygon.py -q`

## Notes

- The min/max limits (`min_radius`/`min_size`/`max_*`) already exist from the
  prior session; keep them in world units.  Only the *initial* clamp in
  `create_from_points` is new.
- `pixel_scale` is a scalar (world units per camera pixel), per the README
  contract.
