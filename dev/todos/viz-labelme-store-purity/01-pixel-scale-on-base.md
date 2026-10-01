# Phase 1 — `pixel_scale` on `ActSceneObject`

## Goal

Move `_pixel_scale`/`set_pixel_scale` from `_ActWithHandles` to `ActSceneObject`
and drop the `hasattr` guard in both label apps.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/examples/apps/image_labeling_app.py`, `calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_act_circle.py` (or a suitable act test)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **1.1 — Add `_pixel_scale` + `set_pixel_scale` to `ActSceneObject.__init__`**
  - `self._pixel_scale = 1.0` and `def set_pixel_scale(self, value)` (float).
- [x] **1.2 — Remove them from `_ActWithHandles.__init__`**
  - Deleted `self._pixel_scale = 1.0` and `set_pixel_scale` there; kept
    `_handle_world_size()` (reads the inherited attribute).
- [x] **1.3 — Drop the `hasattr` guard in both labelers**
  - `_apply_size_limits` calls `act.set_pixel_scale(self._pixel_scale)`
    unconditionally.
- [x] **1.4 — Regression test**
  - `TestPixelScale` asserts `ActPoint` has `set_pixel_scale` and a rectangle's
    rotate offset still respects `_handle_world_size()`.

## Validation

`uv run pytest py/tests/viz/test_act_circle.py py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_polygon.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- `ActPoint` now has a no-op `set_pixel_scale` (it never uses the scale); this
  is intentional — the scale is a scene property available on every act.
