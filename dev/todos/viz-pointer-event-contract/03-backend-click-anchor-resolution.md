# Phase 3 — Backend: resolve the click anchor from the event ray

## Goal

Change `_resolve_click_anchor` to use `event.ray_origin`/`event.ray_direction`
(the frontend's ray) instead of reconstructing one via
`event.camera.pixel_ray(screen_position)`, and cover it with tests.

## Files

- Edit: `py/pytanga/viz/_hosts.py`
- Edit: `py/tests/viz/test_active.py`
- Edit: `py/tests/viz/test_interaction_surface.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **3.1 — Use the event ray in `_resolve_click_anchor`**
  - Replaced `event.camera.pixel_ray(screen_position)` with
    `event.ray_origin` / `event.ray_direction`; dropped the `camera is None`
    guard; kept the `NotImplementedError` + `anchor is None` guards and the
    `event.world_position = anchor` overwrite.
- [x] **3.2 — Update `test_click_handler_receives_ideal_anchor`**
  - Added `ray_origin`/`ray_direction` to the click payload; the expected
    `Point(0, 2, 0)` is unchanged (`ActPoint.click_anchor` ignores the ray).
- [x] **3.3 — Add a surface regression test**
  - `TestClickAnchorResolution.test_surface_click_resolves_from_event_ray`
    dispatches a click whose event ray hits z=0 at `(2,3,0)` with a decoy
    `screen_position`; asserts the handler observes `Point(2,3,0)` (the event
    ray, not `pixel_ray`).

## Validation

`uv run pytest py/tests/viz/test_active.py py/tests/viz/test_interaction_surface.py -q`

## Notes

- For surfaces, this recompute is now redundant-but-correct (the frontend's
  `world_position` already equals the plane hit); for `ActPoint` it remains the
  required ideal-anchor resolution.
