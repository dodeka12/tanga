# Changes since version 2.23.2 (2.24.0-rc2)

## Bug Fixes

- **`Ellipse.angle` is serialized to the frontend** — `_serialize_ellipse` now
  emits `angle`, so an ellipse with a non-zero `angle` is drawn rotated about its
  normal (previously it was always drawn with `angle = 0`).
