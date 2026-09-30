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

- [ ] **2.1 — ImageLabeler `_act_from_entity`**
  - Map `Rectangle2D`→`ActRectangle2D`, `Ellipse`→`ActEllipse`, `Circle`→`ActCircle`,
    `Line`→`ActLine`, `PointPath`→`ActPolygon`, `Point`→`ActPoint`, adding
    `on_click=self._make_select_handler()` (+ polygon `handle_style`/`end_handle_style`).
- [ ] **2.2 — ImageLabeler load/save switch**
  - `load_document`: `iter_objects(doc, active=False)` → `_act_from_entity` →
    `add_shape(act, label)`.
  - `to_document`: pass `(s.act.entity, s.label)` to `shapes_from_objects`.
- [ ] **2.3 — CalibratedLabeler `_act_from_entity` + load switch**
  - Add `_act_from_entity(entity)` (with `on_click=select`); `add_loaded_shape`
    takes an entity and calls it; `_loaded_style` checks plain geometry
    (`Point`, `Rectangle2D`, `Circle`, `Ellipse`, `PointPath`, `Line`).
  - `main()`: `iter_objects(result.document, active=False)`.

## Validation

`uv run pytest py/tests/viz/test_calibrated_labeling_example.py py/tests/viz/test_image_canvas.py -q`

## Notes

- Keep using `active=False` here; Phase 3 removes the flag from the store.
- `_style_for_act`/`_loaded_style` may be renamed to `_style_for_entity` where
  they now receive plain geometry.
