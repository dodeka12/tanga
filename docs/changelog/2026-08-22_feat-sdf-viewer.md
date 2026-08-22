# Changes since version 0.13.0

## New Features
- **SDF viewer implementation plan (container entry)** — initial branch
  changelog for the signed-distance-function viewer; planning structure lives in
  `dev/todos/viz-sdf-viewer/` (README overview plus phase plans, including the
  Phase 6a first-vertical-slice milestone for a Line + Sphere example with
  manual user confirmation). This entry records implementation changes as they
  land on the branch.
- **SDF primitive + combinator GLSL library (Phase 1)** — added the base
  inigo-quilez signed-distance primitives (`sdSphere`, `sdEllipsoid`, `sdBox`,
  `sdRoundBox`, `sdPlane`, `sdSegment`, `sdCapsule`, `sdCylinder`,
  `sdCappedCylinder`, `sdCone`, `sdCappedCone`, `sdTorus`), Boolean/smooth
  combinators (`opUnion`, `opSubtract`, `opIntersect`, `opSmoothUnion`,
  `opSmoothSubtract`, `opSmoothIntersect`), and a shared constant/rotation
  header under `py/pytanga/viz/templates/sdf/shaders/`.
- **WebGL2 raymarcher core (Phase 2)** — added the SDF viewer entry module
  (`sdf_viewer.js`) with a WebGL2 gate (in-page error banner, no WebGL1
  fallback), a fullscreen-quad `ShaderMaterial` ray-marcher, gradient normals,
  IQ-style shading with soft shadows/fog, and a `raymarch.glsl` fragment body.
  The raymarcher reuses the standard viewer's `view_mode.js` camera and
  `controls.js` OrbitControls so the default/custom camera matches the
  non-SDF viewer 1:1; camera position/matrices/near/far are plumbed in as
  uniforms. Structural shader-assembly smoke tests live in
  `py/tests/viz/sdf/test_raymarch_shader.py`. *(The hardcoded-sphere visual
  smoke check and real GLSL compile are deferred to the Phase 6/6a browser
  slice — no local `glslangValidator`/`glslc`/Node-`three` is available.)*
- **Distance-function registry (Phase 3)** — added the Python
  `DistanceFunction` enum (`scalar_pseudo` default, plus `magnitude`, `scalar`,
  `grade`, `component`) with params metadata in `sdf/distance.py`, a matching
  name-keyed GLSL snippet registry in `templates/sdf/algebra/distances.js`, and
  unit tests in `py/tests/viz/sdf/test_distance.py`. This is the shared
  function-registry mechanism the opacity transfer axis (Phase 12) reuses.
- **Analytic entity SDF serializer (Phase 4)** — added the Python SDF
  primitive/combinator descriptor model (`sdf/primitives.py`) and the entity →
  SDF-tree serializer (`sdf/serializer.py`) for the six supported entities
  (`Point`/`Line`/`Plane`/`Sphere`/`Circle`/`PointPair`), plus the frontend
  `scene-builder.js` and `objects/*` GLSL emitters that dispatch a serialized
  tree to a single distance expression. Infinite lines/planes carry an explicit
  finite `bound`; unsupported kinds raise `TypeError`. Unit tests in
  `py/tests/viz/sdf/test_primitives.py` and `test_sdf_serializer.py`.
- **Composed global SDF + material table (Phase 5)** — added the per-object
  composer (`templates/sdf/composer.js`) that folds all object distances into
  one `vec2 map(vec3 p)` returning `(distance, materialId)`, and the material
  table (`templates/sdf/material-table.js`) packing per-object color/opacity
  into a uniform array with a `materialColor(matId)` GLSL sampler. The raymarch
  body now resolves the hit material for lighting (injected `map` +
  `materialColor` contract). Signed combine modes / smooth-blend / signedness
  gate / AABB pruning are deferred to Phase 11 (CSG booleans). A headless Node
  smoke test (`dev/src/sdf_composer_smoke.mjs`) exercises the composed map.
- **`SdfVisualizer` facade + HTML bootstrap (Phase 6)** — added the
  `SdfVisualizer` facade (`sdf/visualizer.py`) mirroring the standard
  viewer's `add`/`show`/`wait` API, the `sdf_viewer.html` entry page, and a
  WebSocket + camera-parity wiring in `sdf_viewer.js`. The shared `VizServer`
  gains an opt-in `entry_page` parameter (default unchanged) so the SDF viewer
  serves `sdf_viewer.html` while the standard viewer still serves
  `viewer.html`. Camera parity is verified against the standard viewer in
  `py/tests/viz/sdf/test_visualizer.py`.
