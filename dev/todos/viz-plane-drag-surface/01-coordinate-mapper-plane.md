# Phase 1 — `CoordinateMapper.plane()`

## Goal

Add a `plane()` accessor to the `CoordinateMapper` protocol and both mappers, so
a drag surface can recover the geometric plane (point + normal) from any mapper.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.

## Files

- Edit: `py/pytanga/viz/camera.py`
- Edit: `py/tests/viz/test_coordinate_mapper.py`

## Steps

- [ ] **1.1 — `plane()` on the protocol**
  - Add `def plane(self) -> tuple[Point, Direction]` to `CoordinateMapper`.
- [ ] **1.2 — `PlanarMapper.plane()`**
  - Return `(Point(0.0, 0.0, 0.0), Direction(0.0, 0.0, 1.0))`.
- [ ] **1.3 — `CalibratedPlaneMapper.plane()`**
  - `point = self.to_world(self._cx, self._cy)`; normal = normalized
    `point - camera_center()` (the optical axis). Return `(point, normal)`.
- [ ] **1.4 — Tests**
  - `PlanarMapper.plane()` is the `z = 0` plane with `+z` normal.
  - `CalibratedPlaneMapper.plane()`: the point is `depth` from the camera center,
    and the normal is a unit vector along the camera→point direction.

## Validation

```
uv run pytest py/tests/viz/test_coordinate_mapper.py -q && uv run ruff check . && uv run ty check
```

## Notes

- `Direction.normalized()` and `Point`/`Direction` arithmetic are already used in
  `_interaction.py`; reuse the same style.
