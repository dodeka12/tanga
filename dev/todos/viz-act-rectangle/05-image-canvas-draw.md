# Phase 5 — `ImageCanvas.draw_rectangle()`

## Goal

Let a user drag out a rectangle on an image, then hand off to an
`ActRectangle2D`.  The initial drag is a normal `ImageCanvas` drag binding; on
drag end it removes the preview and constructs the active rectangle.

## Files

- Edit: `py/pytanga/viz/_image_view.py` (add `draw_rectangle`)
- New: `py/tests/viz/test_image_canvas_rect.py`
- Edit: `py/examples/viz/image/image_canvas.py` (or a new example)

## Steps

- [x] **5.1 — `ImageCanvas.draw_rectangle(on_done=None, **act_kwargs)`**
  - Register a drag flow (via the `ActImagePlane`/`_bind_drag` machinery): on
    `drag_start` record the anchor pixel; on `drag_move` add/update a preview
    `Rectangle2D` (or 4 `Line`s) via `self._handle.add`/`update_entity`; on
    `drag_end` remove the preview, build `ActRectangle2D` from anchor→current,
    `self._handle.add(...)` it, and call `on_done(rect)`.
  - Return a handle to cancel/end the draw mode.

- [x] **5.2 — example**
  - Extend the image-canvas example to draw a rectangle on the image and print
    the resulting `ActRectangle2D`.

- [x] **5.3 — tests**
  - `draw_rectangle` builds a preview during drag and finalizes an
    `ActRectangle2D` on drag end (fake transport/handle).

## Validation

`uv run pytest py/tests/viz/test_image_canvas_rect.py -q`

## Notes

- The initial draw handler and the (not-yet-existing) rectangle handles never
  overlap, so there is no interaction conflict.

---

**Architecture note — check the developer docs.** Before implementing, check
`docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this work
touches, so the new code aligns with the documented architecture. If this work
introduces or changes architecture, update the developer docs.
