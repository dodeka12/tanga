# Phase 3 — `from_entity` (one way to wrap an entity in an Act)

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-controls-and-interactions.md` (active objects) and
> `viz-architecture.md` (`LabelMeStore` is a pure data store).  `from_entity` is a
> classmethod on the `Act*` classes, so the store's data-only contract is kept.

## Goal

Provide `ActRectangle2D.from_entity`, `ActEllipse.from_entity`, and
`ActCircle.from_entity`, and switch the example apps to use them (removing the
hand-rolled frame/angle arithmetic).

## Files

- Edit: `py/pytanga/viz/_active.py`
- Edit: `py/examples/apps/calibrated_labeling_app.py` + `.md`
- Edit: `py/examples/apps/image_labeling_app.py` + `.md`
- Edit: `py/tests/viz/test_act_rectangle2d.py`, `test_act_ellipse.py`, `test_act_circle.py`

## Steps

- [x] **3.1 — `from_entity` classmethods.**
  - Add `@classmethod from_entity(cls, entity, **kwargs)` to each Act: copy
    `center`/`size` (or `radius`/`radius_u`/`radius_v`), `normal`, `dir_u`,
    `dir_v`, `angle`, then forward `**kwargs` to the constructor.

- [x] **3.2 — (Optional) `LabelMeStore.to_act`.**
  - Add `to_act(entity, **kwargs)` dispatching to the right `from_entity` (a
    convenience wrapper; keep the store data-only for load/save).

- [x] **3.3 — Example apps.**
  - Replace the hand-rolled `_act_from_entity` rectangle/ellipse/circle branches
    with `from_entity` calls.

- [x] **3.4 — Tests.**
  - `from_entity` round-trips each shape (entity fields preserved, incl.
    `dir_u`/`dir_v`/`angle`).

## Validation

`uv run pytest py/tests/viz/test_act_rectangle2d.py py/tests/viz/test_act_ellipse.py py/tests/viz/test_act_circle.py py/tests/viz/test_calibrated_labeling_example.py -q`

## Notes

- `from_entity` must not lose the entity's basis/angle — this is the "one way".
