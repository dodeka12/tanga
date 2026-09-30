# LabelMeStore purity + pixel-scale on the base — Overview

**Created:** 2026-09-30 | **Status:** In progress | **Branch:** `feat/calibrated-pane-interaction`

## Goal

Separate the two concerns currently tangled in `LabelMeStore` — **data**
(JSON ↔ plain geometry) and **interaction** (act composites with handlers) —
so the store only ever touches `Point`/`Line`/`Circle`/`Ellipse`/`PointPath`/
`Rectangle2D`, never `ActPoint`/`ActRectangle2D`/….  The label apps become the
single place that wraps plain geometry into interactive acts.  As part of the
same cleanup, move `pixel_scale` from `_ActWithHandles` to `ActSceneObject`
(a scene-coordinate property, not a handle property), which removes the
`hasattr` guard in the label apps.

## Architecture (short)

- **`LabelMeStore`** (`pytanga.viz.labelme`) keeps only the data path:
  - `_entity_from_shape(shape)` → plain geometry (unchanged).
  - `iter_objects(doc)` → `[(entity, label), …]` (plain geometry; `active=` gone).
  - `shapes_from_objects(objects)` / `add_shapes(handle, doc)` → plain geometry
    only (act branches removed).
- **Label apps** (`ImageLabeler`, `_CalibratedLabeler`) own the interaction path:
  - `_act_from_entity(entity)` → wraps `Point`→`ActPoint`, `Line`→`ActLine`,
    `Circle`→`ActCircle`, `Ellipse`→`ActEllipse`, `Rectangle2D`→`ActRectangle2D`,
    `PointPath`→`ActPolygon`, adding `on_click`, drag modes, handle styles.
  - Save path passes `act.entity` (the plain geometry) back to the store.
- **`ActSceneObject`** gains `_pixel_scale` (default `1.0`) + `set_pixel_scale()`;
  `_ActWithHandles._handle_world_size()` keeps reading `self._pixel_scale`
  (inherited).  `_apply_size_limits` calls `act.set_pixel_scale(...)`
  unconditionally — no `isinstance`, no `hasattr`.

### Fixed contract (decided up front)

1. `ActSceneObject` owns `_pixel_scale`/`set_pixel_scale`; `_ActWithHandles`
   keeps `_handle_world_size()`.
2. `LabelMeStore.iter_objects(doc) -> list[tuple[Any, str]]` (no `active=`).
3. `LabelMeStore.shapes_from_objects` and `add_shapes` accept **plain geometry
   only**; the act-typed branches and `_act_from_shape` are deleted.
4. Label apps own `_act_from_entity(entity)`; the store never imports act classes.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Decisions (confirmed)

- Keep the store's method names (`iter_objects`, `shapes_from_objects`,
  `add_shapes`) but make them entity-only; no renames, to limit churn.
- `pixel_scale` is a scene/plane property, so it lives on `ActSceneObject`
  (which `ActPoint` and `_ActWithHandles` both inherit).
- `_ActWithHandles` stays a plain (private) base class; nothing outside
  `_active.py` references it after this plan.

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-pixel-scale-on-base.md](./01-pixel-scale-on-base.md) | Move `pixel_scale` to `ActSceneObject`, drop `hasattr` |
| 2 | [02-label-apps-act-from-entity.md](./02-label-apps-act-from-entity.md) | Label apps wrap entities → acts |
| 3 | [03-labelme-store-entity-only.md](./03-labelme-store-entity-only.md) | `LabelMeStore` drops the act path |
| 4 | [04-docs-changelog.md](./04-docs-changelog.md) | Developer docs + changelog |

## Testing as you go

```
uv run pytest py/tests/viz/test_labelme.py -q           # store (phase 2/3)
uv run pytest py/tests/viz/test_calibrated_labeling_example.py -q
uv run pytest py/tests/viz -q                           # fast viz suite
uv run pytest -q                                        # full (final phase)
uv run mkdocs build --strict                            # docs (final phase)
```

## Non-goals

- Renaming `iter_objects`/`shapes_from_objects`/`add_shapes`.
- Changing the frontend or the mapper (`world_units_per_pixel` stays as-is).
- Making `_ActWithHandles` public or converting it to a Protocol/ABC.
