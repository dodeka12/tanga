# Phase 1 — Frontend: canvas-local `screen_position` + click/dblclick ray

## Goal

Make the frontend send `screen_position` in canvas-local pixels and add
`ray_origin`/`ray_direction` to the click/dblclick payloads, so click and
drag_start carry the same position fields in the same frame.

## Files

- Edit: `py/pytanga/viz/templates/interaction.js`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [ ] **1.1 — Add a canvas-local pixel helper**
  - Add `_toLocal(evt)` returning `[evt.clientX - rect.left, evt.clientY - rect.top]`
    using `this.rendererDomElement.getBoundingClientRect()` (same `rect` the
    raycaster already uses).
- [ ] **1.2 — Send `screen_position` in canvas-local coords**
  - In every payload builder (`drag_move`/`drag_start`, `drag_end`, `click`,
    `dblclick`, `contextmenu`) replace `[event.clientX, event.clientY]` with the
    helper.  Leave `delta_pixels` (relative) unchanged.
- [ ] **1.3 — Send `ray_origin`/`ray_direction` on click and dblclick**
  - After `_getHit` (which sets `this.raycaster.ray`), add
    `ray_origin: [ray.origin.x, ray.origin.y, ray.origin.z]` and
    `ray_direction: [ray.direction.x, ray.direction.y, ray.direction.z]` to the
    `interaction:click` and `interaction:dblclick` payloads.

## Validation

`node js/dev/tests/check-syntax.mjs`

## Notes

- The drag payloads already send the ray on `drag_start`; click/dblclick now
  mirror it.
- `screen_position` is consumed by the backend only in `_resolve_click_anchor`,
  which Phase 3 switches to the event ray — so switching the frame is safe.
