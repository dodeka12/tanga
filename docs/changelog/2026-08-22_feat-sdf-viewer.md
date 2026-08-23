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
- **First vertical slice example (Phase 6a)** — added `demo_sdf_entities.py`
  (`py/examples/viz/demo_sdf_entities.py`) drawing a Line + Sphere through the
  analytic path, as the gate for manual user confirmation in the browser before
  any algebra/CSG/opacity work continues.
- **Primitive object library + `Composed` objects (Phase 06b)** — exposed the
  SDF primitive library as first-class, directly addable objects (`sphere`,
  `box`, `cylinder`, `capped_cylinder`, `cone`, `capped_cone`, `torus`,
  `ellipsoid`, `round_box`, `capsule`, `segment`, `plane`) via named
  constructors in `pytanga.viz.sdf`, and added `Composed` to bundle constituents
  into a single object with one material and a per-constituent combine mode
  (`union`/`intersection`/`subtract`). `SdfNode` gains a `combine` field and a
  `group()` helper; `SdfVisualizer.add` and the serializer accept `SdfNode`/
  `Composed` directly; the frontend `group` fold and the previously-unwired
  primitive emitters were added. Tests in `py/tests/viz/sdf/test_composed.py`
  and `test_primitives.py`.
- **Entity/operator draw-style SDF mapping (Phase 06c)** — mapped every entity
  and operator kind to a basic or composed SDF tree with `style=` support
  (`Point`→sphere, crosshair point→3-axis crosshair, `Line`→segment,
  `Sphere`→sphere, `Rotor`→sector disc + rim ring + axis arrow,
  `Translator`/`Direction`→arrow, `Dilator`→rings, `Motor`→disc+arrow,
  `GeneralRotor`→sector disc+ring+axis at origin, etc.). Added the
  `demo_sdf_composed.py` example (sphere with a bored-out cylinder plus
  torus/box/rotor) and the `demo_sdf_arrowhead.py` diagnostic.
- **Configurable SDF lighting** — `SdfVisualizer` now accepts
  `DirectionalLight` objects through `add()`, has an `add_default_light` flag
  (mirroring the standard viewer's `add_default_axes`/`add_default_grid`), and
  exposes `set_ambient_light()` (plus an `ambient` property) to tune the
  ambient term. The raymarcher shades with a uniform-driven set of up to 8
  directional lights plus a vec3 ambient; the previous hardcoded single light
  is now the built-in default.
- **SDF object/light updates + animation loop** — `SdfVisualizer` gained
  `update_entity()` / `update_light()` (replace an object or light by id),
  `flush()`, and `sleep_ms()` so objects and lights can be modified after
  `add()` and animated. `DirectionalLight.direction` now normalizes on
  assignment. Added the `demo_sdf_light_animation.py` example (a light orbiting
  a sphere).
- **SDF viewer identity + version check parity** — the SDF frontend now sends a
  `viewer_name` (from the `?viewer=` URL param) in its `ready` message and
  compares the server-injected frontend build hash against the `browser_id`
  message's `frontend_version`, showing the standard "Reload now" version-
  mismatch banner on a stale cached copy (matching the standard viewer).
- **Shader-drawn grid overlays (`SdfOverlay` / `Grid`)** — `SdfVisualizer`
  gained `add_default_grid` (a default ground grid) and accepts `Grid` objects
  through `add()`: an arbitrary-plane, infinite grid drawn as a depth-composited
  `fract()`-based overlay rather than a raymarched volume (the grid draws over
  objects behind its plane and is hidden behind objects in front). A new
  `SdfOverlay` base class and a frontend `overlays/factory.js` dispatch
  (mirroring the standard viewer's `renderers/factory.js`) are the seam for
  future overlay kinds (axes, crosshair, …).

- **Shader-drawn coordinate axes overlays (`SdfOverlay` / `Axes`)** —
  `SdfVisualizer` gained `add_default_axes` (three default X/Y/Z axis lines
  from the origin) and accepts `Axes` objects through `add()`: three infinite
  red/green/blue lines drawn as depth-composited, `fwidth()`-AA'd overlays
  that extend only along their positive directions (like the standard
  viewer's `AxesHelper`), hidden behind objects in front and drawn over
  objects behind.

## Bug Fixes
- **Fixed inverted rotations in the SDF viewer** — `transform.js` passed
  `-angle` to IQ's `rotationAxisAngle`, which already negates the angle
  internally, so every rotation was applied with the wrong sign (cone apex
  pointed −Z, rotor sector handedness mirrored). Passing `+angle` now yields the
  intended inverse/local-space rotation.
- **Fixed patchy, direction-inconsistent SDF lighting** — the gradient normal
  used a finite-difference step of `0.5773` (the tetrahedral vertex coefficient
  `1/√3`) rather than a small epsilon, making normals patchy, lighting appear to
  come from different directions per object, and producing unmotivated soft
  shadows. The step is now `0.001`; the remaining subtractive-CSG soft-shadow
  penumbra is documented as a known limitation.
- **SDF viewer browser connect/reconnect parity** — the SDF viewer's frontend
  and backend now mirror the standard viewer's behaviour: the frontend
  auto-reconnects (2s interval, 60s window, connect watchdog, single-flight
  guard, reconnect button, visibility wake-up), and `SdfVisualizer` gained
  `reuse_existing`, `open_browser(wait_for_browser=…)`, `wait_for_browser()`,
  and the interactive connect prompt, so a script re-run reuses the already-open
  tab instead of opening a new one.
