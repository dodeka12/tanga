# Phase 5 — `CoordinateMapper.pixel_axes()`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` (the `CoordinateMapper` bullet) and
> `viz-controls-and-interactions.md` (the "Interaction surface" section).  This
> **extends** the documented `CoordinateMapper` protocol — update both docs in
> step 5.4.

## Goal

Expose the unit world directions of pixel `+u`/`+v` on the mapper's plane, so
`LabelMeStore` can build and export shapes in the mapper's plane basis.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/tests/viz/test_coordinate_mapper.py`
- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/dev/architecture/viz-controls-and-interactions.md`

## Steps

- [x] **5.1 — Protocol method.**
  - Add `def pixel_axes(self) -> tuple[Direction, Direction]: ...` to the
    `CoordinateMapper` protocol (`camera.py:637`), documented as "unit world
    directions of image pixel +u and +v on the annotation plane".

- [x] **5.2 — `PlanarMapper.pixel_axes`.**
  - Return `(Direction(1.0, 0.0, 0.0), Direction(0.0, 1.0, 0.0))`.

- [x] **5.3 — `CalibratedPlaneMapper.pixel_axes`.**
  - Return `normalize(self._c2w @ [1,0,0,0])[:3]` and
    `normalize(self._c2w @ [0,1,0,0])[:3]` as `Direction`s — the world images of
    the camera `+x`/`+y` axes (the directions `to_world` moves under increasing
    `u`/`v`), consistent with the OpenCV frame already baked into `camera_to_world()`.

- [x] **5.4 — Architecture docs.**
  - `viz-architecture.md` `CoordinateMapper` bullet: list `pixel_axes()` alongside
    `to_world`/`to_pixel`/`plane()`/`world_units_per_pixel()`.
  - `viz-controls-and-interactions.md` surface section: note the surface can
    expose its plane basis via `pixel_axes()`.

- [x] **5.5 — Tests.**
  - `PlanarMapper.pixel_axes()` == `((1,0,0),(0,1,0))`.
  - `CalibratedPlaneMapper.pixel_axes()`: both unit length, mutually orthogonal,
    each perpendicular to `plane()[1]`; for the identity-pose camera they equal
    `(1,0,0)`/`(0,1,0)`.

## Validation

`uv run pytest py/tests/viz/test_coordinate_mapper.py -q`

## Notes

- `pixel_axes` is additive; the existing `plane()` (point + normal) is unchanged.
- Phase 6 consumes `pixel_axes()` for rectangle/ellipse build/export and the
  circle rim direction.
