# Phase 8 — `pytanga.viz.labelme` submodule

## Goal

Add a public `pytanga.viz.labelme` submodule: labelme dataclasses, JSON
load/save, and `add_shapes(handle, doc, *, active=…)` that maps every shape type
to a constant entity or active composite (per the README contract).

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md`).  This is a
> pure data-mapping module with no transport/rendering — it composes the existing
> entity/add API; no architecture change.

## Files

- New: `py/pytanga/viz/labelme.py`
- Edit: `py/pytanga/viz/__init__.py` (export `LabelShape`, `LabelMeDocument`,
  `LabelMeStore`)
- New: `py/tests/viz/test_labelme.py`

## Steps

- [x] **8.1 — Dataclasses**
  - `LabelShape(label, points, shape_type, group_id=None, description="",
    flags=…)` and `LabelMeDocument(shapes, image_path="", image_height=None,
    image_width=None, image_data=None, version="5.0.1", flags=…)`, exactly as in
    the README contract.
- [x] **8.2 — `load` / `loads` / `save` / `dumps`**
  - `loads` parses the labelme JSON into `LabelMeDocument` (tolerate a missing
    `version`; `imageData` is read but never written).  `dumps` serializes back
    to the same schema (sorted keys, `imageData: null`, 2-decimal point rounding).
- [x] **8.3 — Shape-type mapping (entity side)**
  - `rectangle` → `Rectangle2D.between(p0, p1)`; `circle` → `Circle(center,
    radius=dist)`; `ellipse` → `Ellipse` from `[center, rim_u, rim_v]`;
    `polygon` → closed `PointPath`; `linestrip` → open `PointPath`;
    `line` → `Line.from_points(p0, p1)`; `point` → `Point`.
- [x] **8.4 — `add_shapes(handle, doc, *, active=True)`**
  - `active=True` returns `ActRectangle2D`/`ActCircle`/`ActEllipse`/`ActPolygon`
    (open for `linestrip`, closed for `polygon`)/`ActLine`/`ActPoint` and adds
    them via `handle.add(act, style=…)`;
    `active=False` adds the plain entities.  Apply a default style per shape type
    (e.g. `Rectangle2DStyle`/`EllipseStyle`/`CircleStyle`/`PointPathStyle`/
    `LineStyle`/`PointStyle`).
  - Return the list of added objects so callers can track/select them.
- [x] **8.5 — `allow_extensions`**
  - `LabelMeStore(allow_extensions=True)`; on save, `ActEllipse` with
    `ru != rv` → `ellipse` when allowed, else `circle` (ru≈rv) or a 32-point
    sampled `polygon`.  Never emit `ellipse` when disallowed.
- [x] **8.6 — Inverse mapping for saving a scene**
  - A helper (e.g. `LabelMeStore.shapes_from_objects(objects)`) that accepts a
    list of (`Act*`, style) pairs and produces `LabelShape`s (used by the app).
- [x] **8.7 — Tests**
  - Round-trip a document with every shape type; `allow_extensions` on/off for an
    ellipse; `add_shapes` with `active=True` and `active=False`.

## Validation

```
uv run pytest py/tests/viz -q
```

## Notes

- Keep the module import-light (no `Visualizer`); `add_shapes` takes a
  `VizSceneHandle` (lazy import of `VizSceneHandle` to avoid circulars, per the
  `viz-architecture.md` pitfalls).
