# Phase 3 — `ActRectangle2D` rotation + minimum size

## Goal

Make `ActRectangle2D` rotatable (store `angle`, pass it to `Rectangle2D`, make
corner resize rotation-aware, add an icon rotate handle) and add `min_size`
clamping.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`).  This mirrors `ActEllipse`'s existing rotate
> handle; no architecture change.

## Files

- Edit: `py/pytanga/viz/_active.py` (`ActRectangle2D`)
- Edit: `py/tests/viz/test_act_rectangle2d.py` (rotation + min_size tests)

## Steps

- [x] **3.1 — Store `angle` and `min_size`**
  - Add `angle: float = 0.0` and `min_size: float | None = None` constructor
    args; build `self._rect = Rectangle2D(center=…, size=…, angle=self._angle)`.
  - Add a `show_rotate_handle: bool = True` arg and a `self._rotate_handle`.
- [x] **3.2 — Rotation-aware corners**
  - Rewrite `_corners()` to rotate the half-extents `(hw, hh)` by `angle`
    around the center (cos/sin of `self._angle`), returning the four world
    corners.
- [x] **3.3 — Rotation-aware resize**
  - Rewrite `_resize_corner(i, pos)`: project `(pos - center)` onto the rotated
    local axes (`dir_u`/`dir_v` from `angle`) to get the local half-extents,
    clamp each to `min_size/2` (when set), and rebuild `Rectangle2D(center, size,
    angle)` keeping the opposite corner anchored.
- [x] **3.4 — Preserve `angle` on translate + entity**
  - `_translate_by` rebuilds `Rectangle2D(center, size, angle=self._angle)`.
  - Ensure `entity`/`rectangle` return the `angle`-carrying `Rectangle2D`.
- [x] **3.5 — Rotate handle**
  - Add `_make_rotate_handler()` / `_dispatch_rotate()` / `_rotate_to(pos)` (set
    `self._angle = atan2(dy, dx)` from center) and a rim `ActPoint` handle at
    `center + dir_u * (hw + offset)` using `rotate_handle_style`; refresh in
    `_refresh_handles()`.
- [x] **3.6 — `on_rotate` + `on_change`**
  - Add optional `on_rotate` callback (mirror `on_translate`/`on_corner_drag`);
    `_commit()` passes the updated `Rectangle2D` to `on_change` (already does).
- [x] **3.7 — `create_from_points(a, b)`**
  - Classmethod building a rectangle from two opposite corners (delegate to
    `Rectangle2D.between`), forwarding `min_size`/`angle`/handle args.
- [x] **3.8 — Tests**
  - Drag a corner of a rotated rectangle → `angle` unchanged, size updated in the
    rotated frame; `_rotate_to` sets the expected angle; `min_size` clamps;
    `create_from_points` round-trips.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- `Rectangle2D` already serializes `angle` and `rectangle2d.js` already applies
  `rotateZ(angle)` — no renderer change is needed; this phase only makes the
  *active* object drive it.
