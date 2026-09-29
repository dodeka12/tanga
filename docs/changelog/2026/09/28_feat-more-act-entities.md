# Changes since version 2.12.1

## New Features

- **`ActEllipse` active element** — an interactive `Ellipse` with radius,
  translate, and rotate handles; rotation is encoded in `Ellipse.dir_u`/`dir_v`.
- **`ActPolygon` active element** — an editable open/closed `PointPath` with
  per-vertex handles; Ctrl+drag extends the start/end, Ctrl+right-click trims
  it, and `auto_close=True` fuses the two endpoints into one and closes the
  path when one is dragged onto the other.
- **Body `on_click` on active composites** — `ActRectangle2D`/`ActEllipse`/
  `ActPolygon` accept `on_click`, making their body clickable (selectable).
- **`ActPoint` drag/click bindings** — `ActPoint` accepts `drag_bindings`/
  `click_bindings` for button + modifier-specific triggers.
- **Keyboard shortcuts** — `Visualizer.on_key` / `VizSceneHandle.on_key` /
  `ImageCanvas.on_key` register per-scene key handlers (per-pane focus, the
  `interaction:key` protocol, and `SceneConfig.keyboard`).
- **Multi-shape labeling example** — `py/examples/viz/image/image_labeling.py`
  (renamed from `rectangle_labeling.py`) draws, selects, and deletes rectangles,
  ellipses, polygons, and points.
- **`EllipseStyle` fill** — `EllipseStyle(fill=True, fill_opacity=…)` draws a
  semi-transparent fill disc under the outline (so an ellipse body is easy to
  click/select, like a filled `Rectangle2D`).
- **Control `selected` state** — `Control.selected` / `ControlView.set_selected`
  highlight a button as active (toggle-button style); the labeling example uses
  it to mark the armed toolbar tool.
- **`CirclePointStyle` + `IconPointStyle`** — new point marker variants: a flat
  filled/outline circle and a canvas-textured icon glyph (any `material:*`
  glyph), dispatched in `factory.js` like `CrossHairPointStyle`/`SquarePointStyle`.
- **Per-role handle styles** — the composites gain `translate_handle_style` /
  `rotate_handle_style` and default to circle vertex/corner/radius handles and
  icon translate/rotate handles.
- **`ActRectangle2D` rotation + `min_size`** — `ActRectangle2D` now stores
  `angle`, renders rotation-aware corners/resize, adds a rim rotate handle, and
  clamps corner resize with `min_size`.
- **`ActCircle` active element** — an interactive `Circle` (center + radius) with
  a centre translate handle and one radius handle (`min_radius` clamp).
- **`ActLine` active element** — an interactive two-point `Line` segment with
  endpoint + midpoint-translate handles.
- **`ActPolygon` vertex editing** — Ctrl+drag **any** vertex inserts a new vertex
  after it; Ctrl+right-click deletes any vertex (a closed polygon stays closed
  while ≥3 vertices remain); Ctrl+Shift+right-click also opens a closed polygon.
- **`ShapeFromPoints` protocol + `DragPreview`** — a protocol unifying the
  composites' `create_from_points(a, b)` classmethods, and a `DragPreview` helper
  that drives the transient-entity lifecycle for any factory implementing it.
- **`pytanga.viz.labelme`** — dataclasses (`LabelShape`/`LabelMeDocument`), a
  `LabelMeStore` (load/loads/save/dumps, `add_shapes`, `shapes_from_objects`),
  mapping every labelme shape type to an entity or active composite; the
  non-standard `ellipse` type is gated by `allow_extensions`.
- **Image labeling app** — the example moved to
  `py/examples/apps/image_labeling_app.py` (a `VisualizerApp` with rect/ellipse/
  circle/line/polygon/point tools, a File menu, and CLI load/save of labelme
  JSON).

## Bug Fixes

- **Image-plane click anchor** — clicking an `ImageCanvas` no longer re-derives
  the world position from the event's view-relative `screen_position` (which
  offset points/polygon vertices by the pane's top-left position); the raw
  raycast hit is kept.
- **Scene-config camera reset** — `set_cursor` (and other `scene_config`
  re-pushes) no longer re-applies the stale camera, so pan/zoom is preserved.
- **Per-pane key focus** — the pane now gains keyboard focus on pointer-down
  even when a drag handler calls `stopPropagation`, so Delete/Escape shortcuts
  fire.
- **Image-plane depth** — the image plane no longer writes depth, so overlay
  lines (polygons, ellipse outlines) drawn at the image's `z=0` render on top
  instead of z-fighting with the image.
- **Image-plane raycast shadowing** — the raycast now sorts the image plane
  last, so shape bodies drawn at the image's `z=0` win equal-distance hits
  instead of being shadowed; the last-drawn shape is selectable without first
  exiting the draw mode.
- **Quadric spaces now precompiled** — `BasisQ2`/`BasisQ3` (`G(6,0)`/`G(10,0)`
  float64) were missing from the precompiled binding set, so importing them
  fell back to JIT compilation (requiring the `[compile]` extra); they now
  ship precompiled.
