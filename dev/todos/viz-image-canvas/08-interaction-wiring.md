# Phase 8 — Interaction wiring (plane raycast → pixel coords → uniform)

## Goal

Wire `ActImagePlane` end-to-end: the frontend raycasts the image plane and
reports pixel-coordinate `world_position`, and the backend handler modifies a
uniform via `set_uniform` (JSON update, no image re-transmit).

## Files

- Edit: `py/pytanga/viz/templates/interaction.js` (image-plane raycast)
- Edit: `py/pytanga/viz/_image_view.py` (`ImageCanvas` default handlers)
- New: `py/tests/viz/test_image_canvas_handlers.py`

## Steps

- [ ] **8.1 — frontend raycast**
  - Ensure the image plane entity, when registered via `set_interaction`, is
    raycastable and sends `interaction:*` events; `DragMode.XY_PLANE`/the
    `drag_anchor` path yields `world_position` in pixel coordinates (no new
    event field — reuse `world_position`/`world_delta`).

- [ ] **8.2 — backend handlers**
  - `ImageCanvas` default `on_drag`/`on_click` read `event.world_position` as
    `(px, py)` and call `set_uniform`; expose the values to user handlers
    (e.g. `u_brightness` from vertical drag).

- [ ] **8.3 — example binding**
  - Provide the documented default: ctrl+left drag adjusts
    `u_brightness`/`u_contrast`; plain drag reports pixel position.

- [ ] **8.4 — tests**
  - `py/tests/viz/test_image_canvas_handlers.py`: a `DragEvent` with a known
    `world_position` updates the expected uniform; handler registration matches
    the `(object_id, event_type)` contract.

## Validation

`uv run pytest py/tests/viz/test_image_canvas_handlers.py -q && uv run ruff check py/pytanga/viz/_image_view.py py/tests/viz/test_image_canvas_handlers.py && node --check py/pytanga/viz/templates/interaction.js`

## Notes

- This phase only wires existing interaction plumbing — no new `DragMode`, no
  new event type; the plane's `drag_anchor` from Phase 3 supplies the hit.
- Pixel coordinates are world coordinates here (y-down frame), so no separate
  image↔screen transform is needed.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
