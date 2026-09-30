# Phase 3 — Handle visibility + polygon end-handle styles

## Goal

Make hidden translate/rotate handles non-interactive, and give the calibrated
polygon the same red vertex / green endpoint handle styling as the image
labeler.

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py`
- Edit: `py/tests/viz/test_act_rectangle2d.py` (or `test_act_ellipse.py`)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **3.1 — `set_translate_handle_visible` / `set_rotate_handle_visible` toggle interaction**
  - After `self._viz_handle.set_visible(handle.entity_id, visible)`, also call
    `handle.set_enabled(visible)` so a hidden handle no longer raycasts/drags.
- [x] **3.2 — Calibrated polygon gets vertex + endpoint handle styles**
  - `_CalibratedLabeler` now defines red `vertex_style` / green `end_style`
    (screen-space circles) and passes them to the polygon `DragPreview`
    `factory_kwargs` (drag-created polygons only; loaded polygons keep defaults).
- [x] **3.3 — Regression test**
  - `TestHandleVisibility` asserts a hidden rotate/translate handle flips its
    `_enabled` flag to `False`.

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py -q`

## Notes

- `set_enabled` re-pushes the `interaction` aspect via `refresh_interaction()`,
  so the frontend stops raycasting it immediately.
- For loaded polygons, apply the styles at construction time if `iter_objects`
  can carry them; otherwise keep the styles on the drag-created polygon only
  and note the limitation.
