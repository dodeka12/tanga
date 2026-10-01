# Phase 3 — Thread `CoordinateMapper` through `LabelMeStore`

## Goal

`LabelMeStore(mapper=...)` replaces the hardcoded `Point(x, y, 0.0)` / `.x`/`.y`
pixel↔world assumptions; the default `PlanarMapper` preserves current behavior.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/labelme.py`
- Edit: `py/tests/viz/test_labelme.py`

## Steps

- [x] **3.1 — Constructor**
  - `LabelMeStore(*, allow_extensions=True, mapper: CoordinateMapper | None = None)`
    with `self._mapper = mapper if mapper is not None else PlanarMapper()`.
- [x] **3.2 — Load side**
  - In `_entity_from_shape`/`_act_from_shape`, build `pts` via
    `self._mapper.to_world(x, y)` instead of `Point(x, y, 0.0)`.
- [x] **3.3 — Save side**
  - In `_shape_from_object`/`_shape_from_ellipse`/`_polygon_from_corners`/
    `_polygon_from_ellipse`, read `(u, v) = self._mapper.to_pixel(p)` instead of
    `(p.x, p.y)`.
- [x] **3.4 — Point drag mode**
  - Change `ActPoint(..., drag_mode=DragMode.XY_PLANE)` to `DragMode.VIEW_PLANE`
    so points stay camera-relative off the `z=0` plane (the other shapes already
    use `VIEW_PLANE`).
- [x] **3.5 — Tests**
  - `PlanarMapper` output identical to pre-change behavior; a
    `CalibratedPlaneMapper` round-trips shapes through `shapes_from_objects` +
    `_entity_from_shape`.

## Validation

```
uv run pytest py/tests/viz/test_labelme.py -q && uv run ruff check . && uv run ty check
```

## Notes

- The `_path` helper already carries `.z`; only the `Point(x, y, 0.0)` / `.x`/`.y`
  sites need the mapper.
