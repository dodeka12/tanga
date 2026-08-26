# Changes since version 1.5.0

## New Features
- **Extra visualization-only geometry entities** — added `Disk`, `PartialDisk`,
  `Box`, `Ellipsoid`, `Ellipse`, and `RegularPolygon` (plus a `regular_polygon()`
  factory) to `pytanga.geometry`.  Like `Cylinder`/`Arc`, they have no
  multivector representation and exist purely as rendering hints.  Planar
  shapes default to the xy-plane (`normal = +z`), so they work in both the 2D
  and 3D viewers.
- **Mesh styles for the new entities** — added `DiskStyle`, `PartialDiskStyle`,
  `BoxStyle`, `EllipsoidStyle`, `EllipseStyle`, and `RegularPolygonStyle` with
  canonical defaults and per-entity slab `thickness` knobs, wired through the
  standard Three.js viewer and static HTML export.
- **SDF support for the new entities** — `Disk`→`cappedCylinder`,
  `Box`→`box`, `Ellipsoid`/`Ellipse`→`ellipsoid`, and two new SDF primitives
  (`partialDisk`, `regularPolygon`) with matching GLSL and JS emitters.  Added
  per-entity `SdfDiskStyle`, `SdfPartialDiskStyle`, `SdfBoxStyle`,
  `SdfEllipsoidStyle`, `SdfEllipseStyle`, and `SdfRegularPolygonStyle`, so every
  new solid renders as a ray-marched SDF object via `SdfObject(...)`.
