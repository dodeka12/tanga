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
  entity (circle, ellipse, hyperbola, parabola, line pair, ellipsoid, sphere,
  cylinder, cone, plane, …); `create()` inverts the round-trip.
- **Point-set analysis + 2D two-conic intersection** — OPNS point-joins analyze
  to a `PointSet`, and the thesis pencil method intersects two conic matrices
  into a `PointSet`.
- **Analytic ray renderer** — `RayStyle` / `RayQuadricStyle` opt entities into
  analytic ray rendering (`kind:"ray"`), with a bounding-box proxy shader that
  writes `gl_FragDepth`; `Quadric3D` renders via this path by default.
- **2D conic curve renderers** — `Hyperbola`, `Parabola`, `LinePair`
  (`ParallelLinePair`), and `PointSet` frontend renderers.

## Bug Fixes
- **Ray renderer one-sided quadrics** — the analytic ray proxy now rasterizes
  its back faces (`side: THREE.BackSide`) so it keeps rendering when the camera
  is inside the proxy box (unbounded quadrics use a large ±10 cube), and shades
  two-sided with `|n·L|` diffuse so open quadrics (cone, paraboloid,
  hyperboloid) stay lit from every viewpoint instead of flipping to a dark
  one-sided view.
- **Ray/quadric intersection clipped to the proxy box** — the analytic
  intersection now returns the nearest root inside `[tNear, tFar]` rather than
  the nearest root on the unbounded ray, so unbounded quadrics no longer pop
  out of view when their closest intersection sits just outside the ±10 cube.

