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

- [x] **3.1 — Delete `_act_from_shape` and the `active=` parameter**
  - `iter_objects(doc)`, `add_shapes(handle, doc)`, `shapes_from_objects(objects)`
    drop `active` and always call `_entity_from_shape`.
- [x] **3.2 — Remove act branches from `_shape_from_object` / `_shape_from_ellipse`**
  - `isinstance(obj, (ActX, EntityX))` → `isinstance(obj, EntityX)`; added a
    `PointPath` branch (closed detected via first==last point); dropped the
    `Act*` imports.
- [x] **3.3 — Update `test_labelme.py`**
  - Entity-only `TestAddShapes` (incl. `test_never_returns_acts`),
    `test_shapes_from_objects` on plain entities, `active=` removed from the
    round-trip tests.

## Validation

`uv run pytest py/tests/viz/test_labelme.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- The label apps already switched to `active=False` in Phase 2, so removing the
  flag is safe here.
- The store should have zero imports of `Act*` after this phase.
