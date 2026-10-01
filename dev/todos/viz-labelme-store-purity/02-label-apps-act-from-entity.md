# Phase 2 — Label apps wrap entities → acts

## Goal

Give both label apps an `_act_from_entity(entity)` mapping and switch their
load/save flows to the store's **entity** output (using `active=False` until
Phase 3 removes the flag).

## Files

- Edit: `py/examples/apps/image_labeling_app.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [x] **2.1 — ImageLabeler `_act_from_entity`**
  - Maps `Rectangle2D`→`ActRectangle2D`, `Ellipse`→`ActEllipse`, `Circle`→`ActCircle`,
    `Line`→`ActLine`, `PointPath`→`ActPolygon`, `Point`→`ActPoint` (with `on_click`,
    handle styles).
- [x] **2.2 — ImageLabeler load/save switch**
  - `load_document`: `iter_objects(doc, active=False)` → `_act_from_entity` →
    `add_shape(act, label)`; `to_document` passes `(s.act.entity, s.label)`.
- [x] **2.3 — CalibratedLabeler `_act_from_entity` + load switch**
  - Added `_act_from_entity(entity)`; `add_loaded_shape` takes an entity;
    `_loaded_style` checks plain geometry; `main()` uses `active=False`.

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py py/tests/viz/test_image_canvas.py -q`

## Notes

- Keep using `active=False` here; Phase 3 removes the flag from the store.
- `_style_for_act`/`_loaded_style` may be renamed to `_style_for_entity` where
  they now receive plain geometry.
