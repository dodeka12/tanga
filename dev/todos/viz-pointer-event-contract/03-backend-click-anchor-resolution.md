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

- [ ] **3.1 — Use the event ray in `_resolve_click_anchor`**
  - Replace the `event.camera.pixel_ray(...)` call with
    `ray_origin, ray_direction = event.ray_origin, event.ray_direction`.
  - Keep the `NotImplementedError` guard and the `anchor is None` guard, and
    keep overwriting `event.world_position = anchor` (the ideal-anchor behavior
    must stay).
- [ ] **3.2 — Update `test_click_handler_receives_ideal_anchor`**
  - Add `ray_origin`/`ray_direction` to the click payload (mirroring the new
    frontend), since the handler now reads the event ray.  `ActPoint.click_anchor`
    ignores the ray, so the expected `Point(0, 2, 0)` is unchanged.
- [ ] **3.3 — Add a surface regression test**
  - In `test_interaction_surface.py`, dispatch a `click` on a `PlanarMapper`
    surface with a ray `origin=(2,3,5), direction=(0,0,-1)` plus a deliberately
    wrong `screen_position`, and assert the handler observes `Point(2,3,0)` (the
    ray↔plane hit from the **event** ray, not `pixel_ray`).

## Validation

`uv run pytest py/tests/viz/test_active.py py/tests/viz/test_interaction_surface.py -q`

## Notes

- For surfaces, this recompute is now redundant-but-correct (the frontend's
  `world_position` already equals the plane hit); for `ActPoint` it remains the
  required ideal-anchor resolution.
