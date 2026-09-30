# Phase 3 — `LabelMeStore` entity-only

## Goal

Remove the act path from `LabelMeStore` so it only maps JSON ↔ plain geometry.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Steps

- [ ] **3.1 — Delete `_act_from_shape` and the `active=` parameter**
  - `iter_objects(doc)`, `add_shapes(handle, doc)`, `shapes_from_objects(objects)`
    drop `active` and always call `_entity_from_shape`.
- [ ] **3.2 — Remove act branches from `_shape_from_object` / `_shape_from_ellipse`**
  - Change `isinstance(obj, (ActRectangle2D, Rectangle2D))` → `isinstance(obj,
    Rectangle2D)` (etc.); drop the `act`-typed imports and `obj.rectangle if …`
    coercions (obj is always the plain entity).
- [ ] **3.3 — Update `test_labelme.py`**
  - Replace `active=True`/`active=False` usages with the entity-only API;
    delete act-specific assertions; add one test asserting the store never
    returns an `Act*` instance.

## Validation

`uv run pytest py/tests/viz/test_labelme.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- The label apps already switched to `active=False` in Phase 2, so removing the
  flag is safe here.
- The store should have zero imports of `Act*` after this phase.
