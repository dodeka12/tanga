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

- [x] **1.1 — Add a canvas-local pixel helper**
  - Added `_localPosition(clientX, clientY)` returning `[clientX - rect.left,
    clientY - rect.top]` from `rendererDomElement.getBoundingClientRect()`.
- [x] **1.2 — Send `screen_position` in canvas-local coords**
  - Replaced raw `[clientX, clientY]` (and `[lastPos.x, lastPos.y]`) with the
    helper in every payload builder (drag, drag_end, anchor-pending drag_move,
    click, dblclick, scroll, cancel-drag).  `delta_pixels` untouched.
- [x] **1.3 — Send `ray_origin`/`ray_direction` on click and dblclick**
  - Added the raycaster ray to the `interaction:click` and `interaction:dblclick`
    payloads (mirroring `drag_start`).

## Validation

`node js/dev/tests/check-syntax.mjs`

## Notes

- The drag payloads already send the ray on `drag_start`; click/dblclick now
  mirror it.
- `screen_position` is consumed by the backend only in `_resolve_click_anchor`,
  which Phase 3 switches to the event ray — so switching the frame is safe.
