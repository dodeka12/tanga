# Phase 4 — Viz: serializers, `curve.js` renderer, styles, factory

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`, in particular
> `viz-architecture.md` and `viz-controls-and-interactions.md`) for the
> subsystem(s) this work touches, so the new code aligns with the documented
> architecture.  If this work introduces or changes architecture, update the
> developer docs.

## Goal

Make `PlaneConicPair` and `Curve` renderable: serializers that sample them into
polylines in Python, one `curve.js` frontend renderer that draws a 3D polyline,
two styles, and factory/bootstrap registration.

## Files

- Edit: `py/pytanga/viz/serializer.py`
- Edit: `py/pytanga/viz/_styles/_entity_styles.py`
- Edit: `py/pytanga/viz/_styles/__init__.py`
- Edit: `py/pytanga/viz/__init__.py`
- New: `py/pytanga/viz/templates/renderers/curve.js`
- Edit: `py/pytanga/viz/templates/renderers/factory.js`
- Edit: `py/pytanga/viz/export/_bootstrap/_html.py`
- Edit: `py/tests/viz/test_serializer.py`

## Steps

- [x] **4.1 — Serializers**
  - `_serialize_plane_conic_pair`: sample each `PlaneConic` with
    `_sample_conic_2d` (phase 2) and map `(s, t)` → 3D via the canonical frame
    (`_plane_frame`); emit `{"kind": "PlaneConicPair", "paths": [[[x,y,z],…], [[x,y,z],…]]}`
    plus the resolved color/opacity/style.
  - `_serialize_curve`: emit `{"kind": "Curve", "paths": [[[x,y,z],…]]}` from
    `ent.points` (one path).
  - Dispatch both in the entity dispatcher (`ParallelPlanePair`-style ordering is
    not needed; both are leaf types) and import the entities at the top.
- [x] **4.2 — Styles**
  - `CurveStyle(VizStyle)` and `PlaneConicPairStyle(VizStyle)` with `thickness`
    (and `opacity` inherited from the base), `style_type` in `to_dict()`.
  - Defaults in `_styles/__init__.py::_DEFAULT_STYLE_FOR_KIND`:
    `"PlaneConicPair"` and `"Curve"` (e.g. `color="#44ff44", opacity=0.9, thickness=0.02`).
  - Export both from `viz/__init__.py` (`import` + `__all__`).
- [x] **4.3 — `curve.js` renderer**
  - `createCurve(ent)`: for each path in `ent.paths`, build a `THREE.BufferGeometry`
    line (or `THREE.Line` with a `LineBasicMaterial`) using the path points;
    `tagEntity` the group.
  - `updateCurve(mesh, ent, prev)`: `contentChanged(ent, prev, ['paths'])` →
    rebuild; else `applyStyleUpdate`.
- [x] **4.4 — Factory + bootstrap registration**
  - `factory.js`: import `createCurve, updateCurve`; add `case 'PlaneConicPair':`
    `case 'Curve':` to the create and update dispatches.
  - `export/_bootstrap/_html.py`: add `"curve.js"` to `_RENDERER_FILES`.
- [x] **4.5 — Serializer tests**
  - `PlaneConicPair` round-trips to two non-empty `paths` with 3-vectors, and the
    serialized points lie in the respective planes.
  - `Curve` round-trips its points to one `path`.
  - JSON-serializable (covered by the existing `test_all_json_serializable`).

## Validation

`uv run pytest py/tests/viz/test_serializer.py -q`

## Notes

- The renderer draws plain 3D polylines (no tubes) — simplest correct render;
  a tube/`LineBasicMaterial`-thickness upgrade is out of scope.
- Keep `_sample_conic_2d` / `_plane_frame` in `quadric/_intersection.py` and
  import them (lazily, if needed) from the serializer to avoid duplication.
- `node --check` the new `curve.js` before committing.
