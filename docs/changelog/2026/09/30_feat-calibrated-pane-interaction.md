# Changes since version 2.13.0

## New Features

- **`CoordinateMapper`** — a pixel↔world mapping protocol in `pytanga.viz.camera`
  (`to_world(u, v)` / `to_pixel(point)`) with a `PlanarMapper` (the previous
  `z = 0` "pixel == world XY" behavior) and a `CalibratedPlaneMapper` (casts a
  pinhole ray and intersects a plane perpendicular to the optical axis at a fixed
  `depth`).  `LabelMeStore(mapper=…)` threads it through every pixel↔world call
  site, so labelme shapes can live in a calibrated 3D scene instead of a flat
  pixel plane.
- **Robust labelme loading** — `LabelMeStore.load`/`loads` now return a
  `LabelMeLoadResult` and `add_shapes`/`iter_objects` return `(result, errors)`;
  malformed shapes (e.g. a one-point `"rectangle"`) are skipped and reported
  instead of crashing or silently dropping.
- **Lossless labelme round-trip** — `dumps`/`save` emit labelme's own key order
  with `indent=4` and no coordinate rounding (opt in via
  `LabelMeStore(coordinate_precision=…)`); the `mask` field is now preserved.
- **`LabelShape` unification** — the example app's `LabeledShape` (`act`/`style`/
  `label`) is folded into `LabelShape`, with `mask` round-tripped and `style`/
  `act` kept in memory only.
- **Calibrated labeling example** — `py/examples/apps/calibrated_labeling_app.py`
  labels a bundled T-LESS image in two panes of one world scene (calibrated
  camera view on the left, frustum + shapes on the right) via a
  `CalibratedPlaneMapper`.
- **Plane-aware `ActImagePlane`** — the interactive image plane is generalized to
  draw on any plane defined by a `CoordinateMapper` (`CoordinateMapper.plane()`
  exposes the plane's point + normal).  Its drag anchor is a generic ray↔plane
  intersection and its drag mode is `VIEW_PLANE`, so drag-to-draw works on a
  calibrated camera plane (perpendicular to the optical axis) as well as the flat
  image canvas — with no frontend change.
- **Calibrated drag-to-draw** — `calibrated_labeling_app.py` gains a toolbar +
  `DragPreview` that draws rectangle/circle/line shapes on the calibrated pane,
  adding them to the shared world scene (visible in both the calibrated and world
  views).

- **Per-pane `InteractionSurface`** — a reusable interaction primitive: a
  `SceneView` pane plus a `CoordinateMapper` (which defines a plane via
  `plane()`) plus pane-level `on_drag_start`/`on_drag`/`on_drag_end`/`on_click`
  handlers, with **no scene entity**.  The frontend emits drag/click events for
  the pane's empty space by intersecting the mouse ray with the serialized
  `{point, normal}`, and the backend resolves world positions on the plane.
  `SceneView(surface=…)` binds it; `SceneView(read_only=True)` suppresses
  surface + `Act*` interaction on a pane while navigation keeps working.
- **`CalibratedSurface`** — an `InteractionSurface` on the ⟂-optical-axis plane
  at a fixed `depth` (`CalibratedPlaneMapper`).
- **Calibrated image labeling** — `calibrated_labeling_app.py` now supports
  drag-to-draw rectangle, circle, line, ellipse, and polygon, plus
  click-to-place point, on a calibrated pinhole-camera pane.
- **Shape selection** — clicking a shape reveals its translate/rotate handles and
  recolors it yellow; clicking elsewhere hides the handles and restores the
  color.  Delete/Backspace removes the selected shape and Escape deselects
  (mirroring the image labeler).
- **3D orbit zoom limits** — `CameraConfig3d` gains optional
  `min_distance`/`max_distance` (world units) bounding the orbit dolly; when
  unset, the frontend derives them from the camera's initial distance to its
  target, so small (e.g. metre-scale) scenes can zoom in instead of being
  clamped by the old fixed `minDistance = 1`.
- **File-chooser filename entry + save mode** — the `FileChooserDialog` footer
  is now an editable filename field: typing it filters the selected folder's
  listing with a case-insensitive glob, and a new `existing_only` flag (default
  true) turns off the must-exist requirement for Save As… (which appends `.json`
  to a filename with no extension).

## Breaking Changes

- **`LabelMeStore.load`/`loads`** now return `LabelMeLoadResult` (was
  `LabelMeDocument`); `add_shapes`/`iter_objects` return `(result, errors)`.
- **`LabelMeStore.dumps`/`save`** no longer round coordinates to 2 decimals or
  sort keys, and indent with 4 spaces.
- **`ImageCanvas.act_plane` → `ImageCanvas.surface`** — the flat image canvas is
  refactored onto an `InteractionSurface`; the `ImageView` is now visual-only
  (no longer raycastable), and the interactive surface is `ImageCanvas.surface`.

## Bug Fixes

- **Calibrated drag-to-draw** — the calibrated labeling example no longer drops
  an interactive `Plane` into the shared world scene (which broke navigation and
  was interactive in both panes).  Drag-to-draw is bound to the image pane's
  surface only, and the overview pane is read-only.
- **Screen-space point markers** — circle/icon point markers no longer apply a
  pixel-unit `size·0.1` z-lift, which had displaced them off the image plane
  onto the camera plane.
- **Icon handle glyphs** — translate/rotate (and other icon-point) handles now
  wait for the Material Symbols ligature font to finish loading before drawing
  their canvas texture, so they render as move/rotate glyphs instead of the raw
  ligature text (`open_with`, `rotate_right`).
- **Zoom-correct drag scale** — pixel→world drag deltas now use the pinhole
  frustum (`screenWorldScale`) instead of the stale `camera.fov`.
- **Toolbar mode highlight** — the calibrated app's toolbar reflects the active
  draw mode.
- **Scale-correct resize limits** — circle/ellipse radius and rectangle size
  clamps are expressed in image pixels (0.5 px minimum) and converted to world
  units via the mapper, so resizing behaves identically in the 2D image labeler
  and the calibrated labeler.
- **Polygon auto-close tolerance** — the endpoint-snap tolerance is derived
  from the handle size in world units instead of raw pixel values, so endpoints
  no longer snap together at calibrated scales.
- **Hidden handles are inert** — hiding the translate/rotate handle also
  disables its interaction.
- **Ellipse degenerate radius** — the ellipse renderer no longer treats a zero
  radius as "unset" (which had rendered a huge default ellipse at the start of
  a drag); a zero radius now clamps to the minimum.
- **Click-created point offset** — click events now carry the picking ray and
  `screen_position` in a common canvas-local pixel frame, and the backend
  resolves the click anchor from that ray (instead of `pixel_ray`), so a
  click-to-place point lands exactly under the cursor, like drag-created shapes.

## Refactor

- **`CoordinateMapper.world_units_per_pixel()`** — the image-pixel↔world size
  scale now lives on the mapper (`PlanarMapper` → 1.0, `CalibratedPlaneMapper`
  → `depth/fx`), replacing the ad-hoc `depth/fx` literals in the label apps.
- **`LabelMeStore` is a pure data store** — it no longer creates
  `ActSceneObject` composites (`_act_from_shape` and the `active=` flag are
  gone); `iter_objects(doc)` / `add_shapes(handle, doc)` map JSON ↔ plain
  geometry (`Point`, `Line`, `Circle`, `Ellipse`, `Rectangle2D`, `PointPath`),
  and the label apps wrap those entities into interactive acts via their own
  `_act_from_entity`.
- **`pixel_scale` on the base** — `_pixel_scale`/`set_pixel_scale` moved from
  `_ActWithHandles` to `ActSceneObject` (every act, including `ActPoint`, now
  carries the world-units-per-pixel scale), removing the `hasattr` guard in the
  label apps.
