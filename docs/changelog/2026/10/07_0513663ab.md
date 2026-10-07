# Changes since version 2.17.0

## Bug Fixes
- **Active shapes honor an explicit `normal` plane and edit in the view plane** —
  `ActRectangle2D`/`ActEllipse`/`ActCircle` accept a `normal` constructor
  parameter (default `+z`) and reconstruct their entity on that plane, and every
  composite's handles (`ActRectangle2D`/`ActEllipse`/`ActCircle`/`ActLine`/
  `ActPolygon`) drag in `DragMode.VIEW_PLANE` with full-3D resize/rotate/
  translate, so a shape no longer silently flattens to world-XY when drawn on a
  tilted `CalibratedSurface`.
