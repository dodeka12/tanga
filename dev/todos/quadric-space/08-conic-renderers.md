# Phase 8 — 2D conic curve renderers

## Goal

Render the specific 2D conic entities (Hyperbola, Parabola, LinePair,
ParallelLinePair) and `PointSet` as sampled curves/points in the standard viewer,
dispatched by `factory.js` and registered in the export bundle.

## Files

- New: `py/pytanga/viz/templates/renderers/hyperbola.js`
- New: `py/pytanga/viz/templates/renderers/parabola.js`
- New: `py/pytanga/viz/templates/renderers/line_pair.js`
- New: `py/pytanga/viz/templates/renderers/point_set.js`
- Modify: `py/pytanga/viz/serializer.py` (`_serialize_*`)
- Modify: `py/pytanga/viz/templates/renderers/factory.js`
- Modify: `py/pytanga/viz/export/_bootstrap/_html.py` (`_RENDERER_FILES`)
- New: `py/tests/viz/test_conic_renderers.py`

## Steps

- [x] **8.1 — serializers** — `_serialize_hyperbola` / `_serialize_parabola` /
  `_serialize_line_pair` / `_serialize_point_set`: flat JSON with resolved
  center/axes/vertices/lines/points (always concrete values, no frontend fallback).

- [x] **8.2 — renderers** — `hyperbola.js`/`parabola.js` sample the curve into a
  `Line`/`BufferGeometry` (bounded parameter range); `line_pair.js` draws two
  `Line`s; `point_set.js` draws a group of `Point`s.

- [x] **8.3 — factory + export** — add the four cases to `factory.js` and register
  the renderers in `_RENDERER_FILES`.

- [x] **8.4 — Tests**
  - Serializer wire contract for each entity (kind + resolved fields).
  - `node --input-type=module --check` on the new renderers + `factory.js`.
  - `uv run pytest py/tests/viz/test_conic_renderers.py
    py/tests/viz/test_export_renderers.py -q`.

- [x] **8.5 — Validate** — `uv run pytest py/tests/viz/test_conic_renderers.py
  py/tests/viz/test_export_renderers.py -q`.

## Validation

`uv run pytest py/tests/viz/test_conic_renderers.py py/tests/viz/test_export_renderers.py -q`

## Notes

- Parabola has no finite closed form — sample over a bounded `t` range from the
  style (add a `range`/`extent` knob if needed).
- `LinePair`/`ParallelLinePair` reuse the existing `Line` renderer per member;
  `PointSet` reuses the existing `Point` renderer.
