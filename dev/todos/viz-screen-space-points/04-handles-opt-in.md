# Phase 4 — Opt-in on Act handles

## Goal

Make the Act composite handles (vertex/corner + translate/rotate) render at a
constant screen size by setting `screen_space=True` on their styles.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-controls-and-interactions.md`
> and `viz-architecture.md`) for the `_ActWithHandles` handle-style model, so the
> opt-in follows the documented active-entity recipe.  No architecture change is
> expected.

## Files

- Edit: `py/pytanga/viz/_active.py` (default handle styles, if any)
- Edit: `py/examples/apps/image_labeling_app.py` (handle styles)
- Edit: `py/tests/viz/test_act_rectangle2d.py` and/or `test_act_polygon.py`

## Steps

- [x] **4.1 — `_ActWithHandles` default handle styles**
  - Set `screen_space=True` on the default vertex/corner and translate/rotate
    handle styles (so any Act composite opts in by default).
- [x] **4.2 — example app handle styles**
  - Update `_handle_style` / `_vertex_style` / `_end_handle_style` (and the
    translate/rotate icon styles) to `screen_space=True` with sensible screen
    pixel sizes.
- [x] **4.3 — tests**
  - Assert the handle style serializes `screen_space=True` (extend the existing
    handle-style tests).

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- Re-run the app and confirm handles stay a constant size when zooming out to the
  new 1/4 min zoom.
