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
- **2D conic visualization** — `Ellipse` renders as a 2D line, and the viewer
  auto-refines a raw `Conic` to its specific 2D entity; `ParallelLinePair` and
  `Cone` gained serializers + frontend renderers, and circles can be drawn as a
  thick line via `CircleStyle`.
- **`Vec3` fundamental vector type (`pytanga.entity`)** — a dependency-free
  `Vec3` with component-wise `+`/`-`, scalar and element-wise `*`, `dot`,
  `cross`, `mag`, `normalized`, and `to_point()`/`to_direction()` conversions;
  `Point` and `Direction` now subclass it.
- **`geo()` accepts `.entity` objects; `VizObjectRef.entity` resolves MVs** —
  `Geometry.__call__` now delegates objects exposing an `entity` attribute
  (e.g. a viz `ActPoint`), and setting `VizObjectRef.entity` resolves a raw MV
  (`analyze` → `Conic` → `refine`) before storing it, so
  `conic_viz.entity = conic_mv` updates a conic from its raw MV.
- **Quadric-space rotation rotor (`geo(Rotor(...))` in `BasisQ2`/`BasisQ3`)** —
  `Rotor` maps to Perwass's conic-space rotor (GAConicSpc eqn.
  GAGeo:C2:RotorDef1): in `BasisQ2`, ``R = R₂ R₁`` with
  ``R₁ = cos θ − (√2/2) sin θ (b₄∧b₆ − b₅∧b₆)`` and
  ``R₂ = cos(θ/2) − sin(θ/2) b₁∧b₂``; in `BasisQ3` it is a rotation about an
  arbitrary axis, built as three commuting factors (linear, mixed-quadratic,
  traceless-quadratic) — see `dev/notes/quadric-rotor-derivation.md`.
- **Quadric-space rotor analysis** — `analyze_operator` / `analyze_rotor` recover
  the rotation `Rotor(angle, axis)` from a Q2/Q3 rotor MV, and `analyze()` returns
  the `Rotor` for rotor MVs (mixed grades).
- **`quadric3d_demo.py`** — reconstructs a quadric from 9 points (3 draggable)
  and rotates it with three sliders (axis azimuth/polar + angle), visualizing the
  effective rotor; `conic_demo.py` also visualizes its rotation rotor.
- **Degenerate quadric → plane pair** — `refine()` recovers `PlanePair` /
  `ParallelPlanePair` from rank-2 quadrics via Perwass's degenerate-conic method
  (eigen-decomposition → `√λ₊·v₊ ± √(−λ₋)·v₋`, mirrored from `LinePair`), and
  `create()` inverts the round-trip; both gain serializers, styles
  (`PlanePairStyle` / `ParallelPlanePairStyle`), and a `plane_pair.js` renderer.
- **Two-quadric intersection** — `intersect_quadrics(Q1, Q2)` and the deferred
  IPNS grade-2 `analyze()` path recover the intersection curve via the pencil's
  degenerate members: a `PlaneConicPair` (two plane-conics, plane-pair member)
  or a sampled `Curve` (cone member); the smooth-elliptic case (no real
  degenerate member) raises `NotImplementedError` for now.  Both render as 3D
  polylines (`curve.js`).

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
- **Silent scene-push failure now logged** — a failed full-state WebSocket push
  logs the exception instead of leaving the viewer blank with no diagnostics.
- **Conic curves stop updating / draw incorrectly** — `Hyperbola` and `Parabola`
  (and `Ellipse`, `Circle`, `LinePair`, `ParallelLinePair`, `PointSet`, `Cone`)
  now rebuild from their own content fields via per-kind `update*` functions, so
  a live geometry change re-samples the curve instead of showing a stale mesh;
  hyperbolas draw **both** branches, and hyperbola/parabola sampling is clipped
  to a spatial `extent` rather than an unbounded parameter range.
- **Line pairs drawn off-center** — `LinePair` / `ParallelLinePair` member lines
  are now centered on their point (`origin - d̂·length/2`) like standalone
  infinite lines, with the member length backend-driven via
  `LinePairStyle.length` / `ParallelLinePairStyle.length`.
- **Quartic intersection curves too short near the origin** — the cone-member
  `Curve` sampler now finds the quartic's unbounded asymptotes analytically (a
  quartic in `tan(θ/2)` on the base conic) and samples the tentacles out to the
  `[-extent, extent]³` box with a few extra rulings, instead of brute-force
  sampling thousands of rulings; a cube whose centre is dragged near the origin
  draws long curves toward the box edges instead of tiny loops hugging the
  origin, and in milliseconds rather than seconds.

## Refactor
- **Quadric style hierarchy** — new `ConicStyle` / `Quadric3DStyle` base classes
  with `EllipseStyle`, `HyperbolaStyle`, `ParabolaStyle`, `LinePairStyle`,
  `ParallelLinePairStyle`, `PlanePairStyle`, `ParallelPlanePairStyle`, and
  `ConeStyle`; `SphereStyle` / `EllipsoidStyle` / `CylinderStyle` / `PlaneStyle`
  now subclass `Quadric3DStyle`.
- **Circle style split** — the tube (torus) style is renamed
  `CylinderCircleStyle` (default for `Circle`); `CircleStyle` is now the
  thick-line variant.
- **Wireframe params removed from thick-line styles** — `LineStyle` no longer
  carries wireframe fields (they moved to the solid `CylinderLineStyle`).
- **Object-oriented rebuild detection** — the flat, kind-agnostic
  `entityRequiresRebuild` field list is replaced by per-renderer
  `update<Kind>(mesh, ent, prev)` functions that own their geometry fields
  (via a shared `contentChanged` helper), shrinking `entityRequiresRebuild` to
  the kind-agnostic kind/style checks.
- **Geometry / quadric module layering** — the fundamental `Point`/`Direction`
  primitives (with `Vec3` and the `Refinable` protocol) moved into a leaf
  `pytanga.entity` package, `Conic`/`Quadric3D` moved into `pytanga.quadric`,
  and `pytanga.geometry.refine` became a duck-typed dispatcher over the
  `Refinable` protocol; the old import paths keep working via re-export shims.
- **Quadric MV creation + analysis consolidated** — the Q2/Q3 entity→MV
  creation (`_create.py`), MV→entity analysis (`_analysis.py`), and point
  recovery (`_pointset.py`) moved into `pytanga.quadric`; `pytanga.geometry`
  keeps thin re-export shims (`create_q2`/`create_q3`, `analysis_q2`/`analysis_q3`,
  `_pointset`), and `geometry.entities` is imported lazily by the quadric modules.


