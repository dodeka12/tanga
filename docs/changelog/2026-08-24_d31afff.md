# Changes since version 1.0.1

## New Features

- **Split views** — show multiple scenes (or control groups) in a single browser
  page via nestable, draggable `SplitView` panes with horizontal/vertical
  splits, fixed or user-movable splitters, and per-axis min/max sizes. New
  `View`/`SplitView`/`SceneView`/`SpacerView`/`Size` classes;
  `viz.show(layout=...)` / `viz.run(layout=...)` open a layout at a single
  `/?view=<name>` URL while the existing per-scene URLs keep working unchanged.

- **Stacks and control views** — `StackView` (vertical/horizontal/wrap flow
  container) and HTML-only control views (`SliderView`/`ButtonView`/
  `DropdownView`) compose recursively with `SplitView`; `GroupView` is a titled
  stack usable as a pane or a `SceneView` overlay. Control handlers
  (`on_change`/`on_click`) are registered automatically when a layout is set.

- **Server multi-scene subscription** — a browser can now subscribe to many
  scenes over one WebSocket connection, so a layout tab receives `view_layout`
  plus per-scene `scene_config`/`scene_update`/controls, routed to the matching
  pane.

- **Per-pane scene camera** — `SceneView(scene, camera=…)` gives a single pane a
  different initial camera (a `CameraConfig`, or `View2DConfig`/`View3dConfig`),
  so the same scene can appear in multiple panes from different viewpoints while
  each pane keeps its own orbit/zoom.  A pane (identified by an optional `id`,
  auto-assigned when omitted) can also be re-aimed at runtime via
  `Visualizer.set_view_camera(view, camera)`.

- **Viz-only geometry entities** — `Cylinder` and `Arc` (an arcing cylinder /
  partial torus with an optional cone arrow tip and a radians angle) that exist
  purely for visualization and have no multivector representation. Each gets a
  default style class (`CylinderStyle`/`ArcStyle`) and a Three.js renderer wired
  through the shared `createEntityMesh` pipeline, so live viewing and static
  HTML export both work out of the box.

- **Coordinate system plotting** — a `CoordinateSystem` helper builds a complete
  2D/3D plotting coordinate system (grid, axes with value labels, an optional
  background plane, and plotted `PointPath`s) inside a single `VizGroup`.
  Supports logarithmic scales for any base (`Scale`/`LinearScale`/`LogScale`),
  an external `size` independent of the data range, `align` (which point of the
  plane sits at `position`), `axis_origin` (where the axes cross), 2D manual
  placement via `position`/`up` without touching the camera, and registered live
  plots (`add_plot`/`update_plots`) with an auto-scaling time axis
  (`min_x_span`). `Axis`/`Grid` gained explicit `ticks`/`line_positions_*`
  placement; the `Plane` renderer now honors `span_u`/`span_v`; and
  `position`/`normal`/`up` accept `Point()`/`Direction()` objects.

## Bug Fixes

- **Standalone HTML export no longer crashes with a duplicate-declaration
  syntax error** — the `cylinder` and `arc` renderers reused the private
  helper names `resolveLength`/`resolveRadius` from the `line`/`arc`
  renderers. Because the export pipeline concatenates every renderer module
  into a single module scope, the colliding top-level declarations threw
  ``Identifier 'resolveLength' has already been declared``. The helpers are
  now uniquely named (`resolveLineLength`, `resolveCylinderLength`,
  `resolveCylinderRadius`, `resolveArcRadius`), and a regression test guards
  the bundle against future name collisions.

## Refactor

- **`ThreeJsView` extraction** — pulled the single-scene render/object/message
  logic out of `viewer.js` into a reusable `ThreeJsView` (backed by a new
  `View` base class with a `ResizeObserver` and per-axis constraints); `viewer.js`
  is now a thin bootstrap.
