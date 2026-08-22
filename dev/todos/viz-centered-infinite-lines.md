# Centered Infinite Lines in the Visualizer (and glTF line fix)

**Created:** 2026-08-22 | **Status:** Plan — do not implement yet

## Goal

When drawing an MV that represents an *infinite* line (not a segment from
`Line.from_points`), the line is currently drawn starting at its closest point
to the origin and extending in one direction only. It should instead be drawn
**centered** on the point of the line closest to the origin. The same check is
performed for planes (which turn out to already be centered).

## Background / analysis

### Serialized contract

- `_serialize_line` (`py/pytanga/viz/serializer.py`) emits `origin`, `direction`
  and a resolved `length` (default `20.0` for infinite lines, or the explicit
  segment length).
- `Line.length is None` distinguishes an infinite line (from analysis) from a
  segment (from `Line.from_points`, where `length = |end - start|`).

### Line (bug — the one reported)

Web frontend `py/pytanga/viz/templates/renderers/line.js`:
```js
const start = new THREE.Vector3(origin);
const end = start.clone().addScaledVector(d, length);   // one direction only
```
For an infinite line `origin` is the closest point to the origin, so the line is
drawn one-directionally from there instead of centered.

**Fix:** in `_serialize_line`, for infinite lines emit the *start point*
`origin − d̂·length/2` (with `d̂` the unit direction). The frontend stays
unchanged and then draws `origin → origin + d̂·length`, which is centered.

### Plane (no change)

`plane.js` builds `PlaneGeometry(extent*2, extent*2)` and centers it on `point`
(`mesh.position.set(point)`). `Plane.point` is always on the plane (closest point
from analysis, or the user's point). Same for the glTF plane
(`_prims.plane(e*2, e*2)` centered at `point`). Already correct. ✅

### glTF line (separate pre-existing bug — fix for consistency)

`_gltf.py` draws a `Line` as `_prims.cylinder(0.03, length, 8)` — a Y-axis
cylinder centered at `origin` — and `_get_rotation` has **no** `Line` branch, so
the direction is ignored (every glTF line renders as a vertical segment). The
glTF exporter consumes the *same* serialized dict, so shifting `origin` in the
serializer would also move the glTF line off-center. Therefore the serializer
fix needs a companion glTF fix.

## Files

- `py/pytanga/viz/serializer.py` — center infinite lines in `_serialize_line`.
- `py/pytanga/viz/export/_gltf.py` — apply direction rotation + midpoint for
  `Line` (companion fix).
- `py/tests/viz/test_serializer.py` — update/add line centering tests.
- `py/tests/viz/test_node_serialization.py` — verify infinite-line length tests.
- `docs/changelog/2026-08-22_fix-viz.md` — Bug Fixes bullet.

## Steps

### Phase 1 — Serializer: center infinite lines

- [x] In `_serialize_line`, after resolving `length`:
  ```python
  origin = ent.origin
  if ent.length is None:                    # infinite line → center on closest point
      unit = ent.direction.normalized()
      origin = ent.origin - unit * (length / 2.0)
  ```
  and emit `"origin": [origin.x, origin.y, origin.z]` (keep `direction`/`length`
  unchanged). Segments (`length` set) keep `origin` as the segment start.

### Phase 2 — glTF line: direction + midpoint

- [x] `_gltf.py::_get_rotation`: add a `Line` branch that rotates the Y-axis
  cylinder to `ent["direction"]` (a Y→direction rotation; the existing helper
  rotates Z→normal, so add a small dedicated path).
- [x] `_gltf.py::_get_position` (or `_make_primitives`): position the centered
  cylinder at the segment midpoint `origin + d̂·length/2` so the line spans
  `origin → origin + d̂·length`, consistent with the new `origin`-as-start-point
  semantics.

### Phase 3 — Tests

- [x] Update `test_serializer.py::test_line`: infinite `Line((0,0,0), (1,0,0))`
  now serializes `origin == [-10, 0, 0]` with `direction == [1,0,0]`,
  `length == 20.0`.
- [x] Add `test_infinite_line_centered`: assert `origin == closest − d̂·length/2`
  for an offset line (e.g. line through `(0,1,0)` dir `(1,0,0)` → closest
  `(0,1,0)`, start `(-10,1,0)`).
- [x] Keep `test_line_from_points_respects_length` and
  `test_infinite_line_resolves_default_length` green (update only if they assert
  `origin`).
- [x] Add a glTF line direction assertion if none exists; run the viz + export
  test suites.

### Phase 4 — Changelog

- [x] Add a Bug Fixes bullet: infinite lines are drawn centered on their closest
  point to the origin (previously one-directional); glTF lines now honor
  direction and center consistently. Planes were already centered (no change).

## Verification

- [ ] `uv run pytest py/tests/viz -q` green.
- [ ] `uv run pytest -q` full suite green.
- [ ] `uv run ruff check` / `uv run ruff format --check` on touched files.
- [ ] Manual: serialize an infinite line and confirm `origin` is the start point;
  confirm `Line.from_points` segments are unchanged.

## Non-goals / follow-ups

- Changing the `Plane` renderer — it is already centered.
- Changing the wire format to add a `centered`/`segment` flag — the serializer
  pre-computes the start point instead, per the requested approach.
