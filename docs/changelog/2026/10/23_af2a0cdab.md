# Changes since version 2.23.2 (2.24.0-rc1)

## Bug Fixes

- **Legacy 3-point ellipses wrap in an act again** — `LabelMeStore` builds
  legacy `[center, rim_u, rim_v]` ellipses with an orthonormal basis and a
  consistent plane normal, so `to_act`/`from_entity` no longer raise
  `ValueError` for old label files; a non-perpendicular `rim_v` contributes
  only its perpendicular component to `radius_v`.
