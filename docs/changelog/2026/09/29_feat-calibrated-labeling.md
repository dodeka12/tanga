# Changes since version 2.12.1

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

## Breaking Changes

- **`LabelMeStore.load`/`loads`** now return `LabelMeLoadResult` (was
  `LabelMeDocument`); `add_shapes`/`iter_objects` return `(result, errors)`.
- **`LabelMeStore.dumps`/`save`** no longer round coordinates to 2 decimals or
  sort keys, and indent with 4 spaces.
