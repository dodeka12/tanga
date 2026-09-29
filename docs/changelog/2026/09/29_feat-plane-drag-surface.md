# Changes since version 2.12.1

## New Features

- **Plane-aware `ActImagePlane`** — the interactive image plane is generalized to
  draw on any plane defined by a `CoordinateMapper` (`CoordinateMapper.plane()`
  exposes the plane's point + normal).  Its drag anchor is a generic ray↔plane
  intersection and its drag mode is `VIEW_PLANE`, so drag-to-draw works on a
  calibrated camera plane (perpendicular to the optical axis) as well as the flat
  image canvas — with no frontend change.
- **Calibrated drag-to-draw** — `calibrated_labeling_app.py` gains a toolbar +
  `DragPreview` that draws rectangle/circle/line shapes on the calibrated pane,
  adding them to the shared world scene (visible in both the calibrated and world
  views).
