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