# Changes since version 1.10.0

## New Features
- **Projective quadric space (`pytanga.quadric`)** — Euclidean-rescaled
  `BasisQ2` / `BasisQ3` bases, point embedding, symmetric-matrix coefficient
  maps, and conic/quadric reconstruction from points.
- **Conic / quadric geometry entities** — `Conic` (`Quadric2D`) and `Quadric3D`
  with rank/signature classification, plus `Hyperbola`, `Parabola`,
  `LinePair`, `ParallelLinePair`, `PointSet`, and `Cone`.
- **Two-level analysis + creation** — `analyze()` returns the raw
  `Conic`/`Quadric3D`; `refine()` (and `Geometry.refine`) recovers the specific
  entity (circle, ellipse, ellipsoid, sphere, cylinder, cone, plane, …), and
  `create()` inverts the round-trip.
- **2D two-conic intersection** — thesis pencil method intersecting two conic
  matrices into a `PointSet`.
- **Analytic quadric ray renderer** — `RayStyle` / `RayQuadricStyle` opt
  entities into analytic ray rendering (`kind:"ray"`), with a bounding-box
  proxy shader that writes `gl_FragDepth`; `Quadric3D` renders via this path by
  default.
- **2D conic curve renderers** — `Hyperbola`, `Parabola`, `LinePair`, and
  `PointSet` frontend renderers.
