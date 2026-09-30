# Changes since version 2.12.1

## New Features
- **Calibrated image labeling** — `calibrated_labeling_app.py` now supports
  drag-to-draw rectangle, circle, line, ellipse, and polygon, plus
  click-to-place point, on a calibrated pinhole-camera pane.
- **Shape selection** — clicking a shape reveals its translate/rotate handles;
  clicking elsewhere hides them (mirroring the image labeler).

## Bug Fixes
- **Screen-space point markers** — circle/icon point markers no longer apply a
  pixel-unit `size·0.1` z-lift, which had displaced them off the image plane
  onto the camera plane.
- **Zoom-correct drag scale** — pixel→world drag deltas now use the pinhole
  frustum (`screenWorldScale`) instead of the stale `camera.fov`.
- **Toolbar mode highlight** — the calibrated app's toolbar reflects the active
  draw mode.
- **Scale-correct resize limits** — circle/ellipse radius and rectangle size
  clamps are expressed in image pixels (0.5 px minimum) and converted to world
  units via the mapper, so resizing behaves identically in the 2D image labeler
  and the calibrated labeler.
- **Polygon auto-close tolerance** — the endpoint-snap tolerance is derived
  from the handle size in world units instead of raw pixel values, so endpoints
  no longer snap together at calibrated scales.
- **Hidden handles are inert** — hiding the translate/rotate handle also
  disables its interaction.

## Refactor
- **`CoordinateMapper.world_units_per_pixel()`** — the image-pixel↔world size
  scale now lives on the mapper (`PlanarMapper` → 1.0, `CalibratedPlaneMapper`
  → `depth/fx`), replacing the ad-hoc `depth/fx` literals in the label apps.
