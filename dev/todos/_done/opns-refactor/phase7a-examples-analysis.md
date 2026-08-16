# Phase 7a — Example File Analysis

Per-file scan of every script under `py/examples/` for Phase 7
(removal of `opns=` keyword arguments and the Phase 4-removed basis
geometry factories). Each entry lists the keywords found and what, if
anything, needs changing.

Legend for the two change categories:

- **`opns=` kwargs** — `Geometry(alg, opns=...)`, `geo.create(..., opns=...)`,
  `geo.which_entity(..., opns=...)`, `viz.add(..., opns=...)`,
  `Visualizer(opns=...)` must disappear; the MV's `algebra.opns` flag is now
  authoritative (set `BasisX(opns=False)` or flip `alg.opns`).
- **Removed basis factories** — Phase 4 removed `vector`, `rnd_vector`,
  `point`, `direction`, `rnd_point`, `rnd_direction`, `rotor`, `line`,
  `plane` (and demo-only `point_pair`/`line_from_*`/`circle`/`sphere`) from
  the `Basis*` classes. Replace with `geometry.create_entity` /
  `geometry.create_operator` / typed entities / raw `multivector`.

---

## `py/examples/` (top level)

### `binding_demo.py`
- **Keywords:** `pytanga.Algebra`, `lookup`, `generate`, `module_name`.
- **Changes:** none. No `opns` usage, no removed basis factories.

---

## `py/examples/algebra/`

### `algebra/algebra_demo.py`
- **Keywords:** raw `Algebra` usage (`multivector`, `gp`, `op`, `ip`, …).
- **Changes:** none.

### `algebra/modulus_algebra_multi.py`
- **Keywords:** `Algebra(...)`, modular products.
- **Changes:** none.

### `algebra/modulus_algebra_single.py`
- **Keywords:** `Algebra(...)`, modular products.
- **Changes:** none.

### `algebra/mv_demo.py`
- **Keywords:** `alg("e1")`, `alg.multivector`, `alg.vp`, `alg.op`.
- **Changes:** none. (`vp`/`op`/`ip` are still public `Algebra` methods.)

---

## `py/examples/basis/`

### `basis/base_e3_demo.py`
- **Keywords:** `E3.vector(1, 2, 3)` — **removed** (`vector` removed from `BasisE3`, Phase 4).
- **Changes:** replace the vector factory with a raw blade build, e.g.
  `v = E3.multivector({1: 1.0, 2: 2.0, 3: 3.0})` (or `Direction` via the
  `geometry` submodule). Update the "Vector factory" comment text accordingly.

### `basis/base_n3_demo.py`
- **Keywords:** `N3.op`, `N3.ip`, `N3.multivector`, `einf`, `eo`.
- **Changes:** none. Raw basis naming only; no `opns`, no removed factories.

### `basis/base_p3_demo.py`
- **Keywords:** `P3.point(1, 0, 0)`, `P3.point(0, 1, 0)`, `P3.point(0, 0, 1)` — **removed** (`point` removed from `BasisP3`, Phase 4). `P3.op`, `P3.multivector` remain valid.
- **Changes:** replace each point factory. For a basis-level demo, raw
  homogeneous blades read best, e.g.
  `A = P3.multivector({1: 1.0, 8: 1.0})` (equivalently `P3("e1 + e4")`);
  or use `create_entity(P3, Point(...))`. Update the "Point factory" wording.

### `basis/base_pga3_demo.py`
- **Keywords:** `PGA.point(1, 2, 3)`, `PGA.point(-1, 0, 1)` — **removed** (`point` removed from `BasisPGA3`, Phase 4); `PGA.vector(0, 0, 1)` — **removed** (`vector` removed from `BasisPGA3`, Phase 4). `PGA.op`, `PGA.ip`, `PGA.multivector` remain valid.
- **Changes:** replace `PGA.point(...)` with `create_entity(PGA, Point(...))`
  (or raw `PGA("x e1 + y e2 + z e3 + e0")`); replace `PGA.vector(0, 0, 1)`
  with `create_entity(PGA, Direction(0, 0, 1))` or raw
  `PGA.multivector({4: 1.0})`. Update the comments that name the factories.

### `basis/basis_usage.py`
- **Keywords:** `b.vector(1, 2, 3)`, `b.vector(1, 0, 0)`, `b.vector(0, 1, 0)` — **removed** (`vector` removed from `BasisE3`, Phase 4).
- **Changes:** replace `b.vector(...)` with raw `b.multivector({...})`
  (or `create_entity` with `Direction`); keep the three-method demonstration
  intact otherwise.

---

## `py/examples/geometry/`

### `geometry/e3_entities.py`
- **Keywords:** `geo.which_entity(vec, opns=False)`, `geo.which_entity(biv, opns=False)` — **`opns=` kwarg**; `e3.vector(3, 4, 0)` — **removed**; docstring references to "``opns=False`` flag".
- **Changes:**
  - `e3.vector(3, 4, 0)` → `e3.multivector({1: 3.0, 2: 4.0})`.
  - For the IPNS section, flip `e3.opns = False` around the two
    `which_entity` calls (then restore), or build a bound IPNS view
    `geo_ipns = Geometry(BasisE3(opns=False))` and call `geo_ipns.which_entity(...)`.
  - Remove the `opns=False` argument from both `which_entity` calls.
  - Update module docstring/comment wording ("opns=False flag" → "opns flag").

### `geometry/n3_entities.py`
- **Keywords:** `geo.create(sphere, opns=False)`, `geo.which_entity(mv_sp_ipns, opns=False)`, `geo.create(Point(5, 0, 0), opns=False)`, `geo.which_entity(mv_pt_ipns, opns=False)` — **`opns=` kwarg**.
- **Changes:** in section 7 (IPNS), use `n3.opns = False` before the IPNS
  create/analyze calls (restore afterwards), or a separate
  `geo_ipns = Geometry(BasisN3(opns=False))`. Drop all `opns=` args.
  Sections 1–6 and 8–9 need no functional change.

### `geometry/n3_operators.py`
- **Keywords:** `Geometry(n3)`, `geo.create`, `geo.which_operator`, `create_operator`, `analyze_operator`.
- **Changes:** none. No `opns=` kwargs, no removed factories. Verify only.

### `geometry/p3_entities.py`
- **Keywords:** `geo.which_entity(mv_p, opns=False)` — **`opns=` kwarg**.
- **Changes:** section 5 (IPNS) — flip `p3.opns = False` around the call or
  use an IPNS-bound `Geometry`; drop the `opns=False` argument.
  All other sections are already `opns`-free.

### `geometry/pga3_entities.py`
- **Keywords:** `geo.create(p, opns=False)`, `geo.create(d, opns=False)`,
  `geo.which_entity(mv_d, opns=False)`, `geo.create(Point(3, 0, 0), opns=False)`,
  `geo.which_entity(mv_pt, opns=False)` — **`opns=` kwarg**; docstring
  "default ``opns=True`` mode".
- **Changes:** for the IPNS sections (3, 4, 7), set `pga.opns = False` around
  the IPNS create/analyze calls (restore afterwards), or use an IPNS-bound
  `Geometry(BasisPGA3(opns=False))`. Drop every `opns=` argument. Update
  docstring/comment wording to refer to the algebra flag.

---

## `py/examples/numerics/`

### `numerics/solver_basics_01.py`
- **Keywords:** solver/matrix usage.
- **Changes:** none.

### `numerics/solver_basics_02.py`
- **Keywords:** solver/matrix usage.
- **Changes:** none.

### `numerics/solver_basics_03.py`
- **Keywords:** solver/matrix usage.
- **Changes:** none.

### `numerics/solver_line_fitting_p2.py`
- **Keywords:** P2 solver usage.
- **Changes:** none (no removed P2 factories invoked here — verify no
  `P2.point`/`P2.direction`/`P2.rnd_*` remain).

### `numerics/solver_point_line_p3.py`
- **Keywords:** `P3.rnd_point(...)`, `P3.point(0, 0, 0)`,
  `P3.point(0, 0, 1) ^ P3.point(1, 0, 1) ^ P3.point(0, 1, 1)`,
  `P3.rotor(theta_true, rot_axis)`, `P3.rnd_direction(...)` — **removed**
  (`point`, `rnd_point`, `rnd_direction`, `rotor` removed from `BasisP3`, Phase 4).
  `P3("e1 + e2 + e3")`, `P3.op`, `BladeMask`, matrix/tensor helpers remain valid.
- **Changes:**
  - `P3.point(x, y, z)` → `create_entity(P3, Point(x, y, z))` (import from
    `pytanga.geometry`).
  - `P3.rnd_point(...)` → generate via `P3.rng.uniform(...)` wrapped in
    `create_entity(P3, Point(x, y, z))` (or raw `multivector`).
  - `P3.rnd_direction(...)` → `create_entity(P3, Direction(...))` using
    `P3.rng.uniform(...)`.
  - `P3.rotor(theta, axis)` → `create_operator(P3, Rotor(angle=theta, axis=Direction(...)))`
    (or raw `P3.multivector(...)` for the rotor blades).
  - `origin`/`plane` joins built from `P3.point` still work, but are better
    expressed via `Line`/`Plane` entities or raw blades
    (`origin ^ pnt` becomes two MVs from `create_entity`).

### `numerics/solver_rotor_estimation.py`
- **Keywords:** `alg.nvp`, `alg.rev`, `alg.gp` — all still valid `Algebra` methods.
- **Changes:** none.

---

## `py/examples/tensor/`

### `tensor/basics_01.py`
- **Keywords:** tensor basics.
- **Changes:** none.

### `tensor/basics_02.py`
- **Keywords:** tensor basics.
- **Changes:** none.

### `tensor/rotor_01.py`
- **Keywords:** rotor tensor usage.
- **Changes:** none (confirm no `P*.rotor(...)` factory is called; use
  `create_operator` if one is).

### `tensor/rotor-point-on-ray_01.py`
- **Keywords:** `P3.rnd_point(...)`, `P3.point(...)`, `P3.rotor(...)`,
  `P3.rnd_direction(...)` — **removed** (same set as `solver_point_line_p3.py`).
  `P3("e1 + e2 + e3")`, tensor/matrix helpers remain valid.
- **Changes:** mirror `numerics/solver_point_line_p3.py`:
  - points/directions via `create_entity(P3, Point(...))` /
    `create_entity(P3, Direction(...))` with `P3.rng.uniform(...)` for randomness;
  - rotors via `create_operator(P3, Rotor(angle=..., axis=Direction(...)))`;
  - keep the `rot_mask`/BladeMask machinery unchanged.

---

## `py/examples/viz/`

### `viz/demo_act_point.py`
- **Keywords:** `Line.from_points(p, Point(...))` — valid; `PointPath`-free.
- **Changes:** none. (Optionally showcase `Line.from_points` MV auto-conversion
  in the Phase 7 pass.)

### `viz/demo_all_entities.py`
- **Keywords:** `Visualizer`, `viz.add(Point(...), ...)`.
- **Changes:** none.

### `viz/demo_animated_export.py`
- **Keywords:** `Visualizer` animation export.
- **Changes:** none.

### `viz/demo_animation_orbit.py`
- **Keywords:** `Visualizer` animation.
- **Changes:** none.

### `viz/demo_animation_timeline.py`
- **Keywords:** `Visualizer` keyframes.
- **Changes:** none.

### `viz/demo_axes_custom.py`
- **Keywords:** `Visualizer` axes/grid.
- **Changes:** none.

### `viz/demo_camera_2d.py`
- **Keywords:** `BasisN3()`, `Visualizer(camera=View2DConfig(...))`.
- **Changes:** none.

### `viz/demo_camera_3d_plane.py`
- **Keywords:** `Visualizer(camera=View3dConfig(...))`.
- **Changes:** none.

### `viz/demo_camera_axes_grid_2d.py`
- **Keywords:** `Visualizer` 2D camera/axes/grid.
- **Changes:** none.

### `viz/demo_camera_config.py`
- **Keywords:** `Visualizer(...)` camera configs.
- **Changes:** none.

### `viz/demo_custom_defaults.py`
- **Keywords:** `Visualizer` style defaults.
- **Changes:** none.

### `viz/demo_drag_point.py`
- **Keywords:** `Line.from_points(p, Point(...))` — valid; `PointPath`.
- **Changes:** none. (Optionally showcase `Line.from_points` MV auto-conversion.)

### `viz/demo_export_figure.py`
- **Keywords:** `Visualizer` figure export.
- **Changes:** none.

### `viz/demo_export_html.py`
- **Keywords:** `Visualizer`, `viz.add(Point(...), ...)`.
- **Changes:** none.

### `viz/demo_labels.py`
- **Keywords:** `Visualizer` labels.
- **Changes:** none.

### `viz/demo_mv_visualization.py`
- **Keywords:** `pga.plane(0, 0, 1, 3)` — **removed** (`plane` removed from `BasisPGA3`);
  `pga.point(5, 0, 0)` — **removed**; `pga.line_from_direction(...)` — **removed**;
  `n3.point(...)`, `n3.point_pair(...)`, `n3.line_from_origin_direction(...)`,
  `n3.circle(...)`, `n3.plane(...)`, `n3.sphere(...)` — **removed / never defined**
  (all Phase 4 / demo-only); `opns=True` and `opns=False` on `viz.add(...)` —
  **`opns=` kwarg**.
- **Changes:** rewrite entirely through the `geometry` submodule:
  - `pga.plane(0,0,1,3)` → `geo_pga.create(Plane(point=Point(0,0,3), normal=Direction(0,0,1)))`.
  - `pga.point(5,0,0)` OPNS → `geo_pga(Point(5,0,0))` (or `geo_pga.create`).
  - `pga.point(5,0,0)` IPNS → create via `geo_pga_ipns = Geometry(BasisPGA3(opns=False))`
    then `geo_pga_ipns(Point(5,0,0))`; drop the `opns=True/False` args from both calls.
  - N3 entities (point, point_pair, line, circle, plane, sphere) → typed entity
    constructors via `geo_n3 = Geometry(n3)`:
    `Point`, `PointPair`, `Line`, `Circle`, `Plane`, `Sphere`.
  - `mv_sphere = n3.sphere(...)` → `geo_n3.create(Sphere(...))`; the explicit
    `analyze(mv_sphere)` call stays.

### `viz/demo_operators.py`
- **Keywords:** `Visualizer` operators.
- **Changes:** none.

### `viz/demo_point_path_trail.py`
- **Keywords:** `PointPath`, `viz.add(trail, style=PointPathStyle(...))`, `PointStyle`.
- **Changes:** none. (Optionally showcase `PointPath.add(mv)` MV auto-conversion.)

### `viz/demo_screenshot.py`
- **Keywords:** `Visualizer` screenshot.
- **Changes:** none.

### `viz/demo_texture_label_plane.py`
- **Keywords:** `BasisN3()`, `Visualizer(port=..., open_browser=...)`.
- **Changes:** none.

### `viz/demo_texture_label_sphere.py`
- **Keywords:** `Visualizer(port=..., open_browser=...)`.
- **Changes:** none.

### `viz/demo_title_annotation.py`
- **Keywords:** `Visualizer(title=...)`.
- **Changes:** none.

### `viz/two_body_gravity.py`
- **Keywords:** `Visualizer` interaction.
- **Changes:** none.

### `viz/two_spheres_interact.py`
- **Keywords:** `super().__init__(title=..., opns=False)` — **`opns=` kwarg**
  (`VisualizerApp.__init__` no longer accepts `opns`); `Geometry(b, opns=False)` —
  **`opns=` kwarg**; `Geometry.__call__`/`create`/`which_entity`, `viz.add`/`update_entity`.
- **Changes:**
  - Drop `opns=False` from `super().__init__(...)` (keep `title`).
  - `b = BasisN3()` → `b = BasisN3(opns=False)` (so it creates IPNS spheres),
    then `self._geo = Geometry(b)`.
  - `viz.add(...)` / `viz.update_entity(...)` calls carry no `opns=` args and
    need no other change.

---

## Summary

| Category | Files |
|----------|-------|
| `opns=` kwarg removal | `geometry/e3_entities.py`, `geometry/n3_entities.py`, `geometry/p3_entities.py`, `geometry/pga3_entities.py`, `viz/demo_mv_visualization.py`, `viz/two_spheres_interact.py` |
| Removed basis factories | `basis/base_e3_demo.py`, `basis/base_p3_demo.py`, `basis/base_pga3_demo.py`, `basis/basis_usage.py`, `geometry/e3_entities.py` (`e3.vector`), `numerics/solver_point_line_p3.py`, `tensor/rotor-point-on-ray_01.py` |
| Both | `viz/demo_mv_visualization.py`, `geometry/e3_entities.py` |
| No change | all other files under `py/examples/` (see individual entries above) |

After the Phase 7 edits, `rg "opns" py/examples` must return only comments/flag
usage (no `opns=` kwargs), and all removed basis factories must be gone.