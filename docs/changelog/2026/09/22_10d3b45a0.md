# Changes since version 2.9.0

## New Features

- **Pinhole camera from calibration** — `pinhole_camera(K, R, t, image_size=…)`
  builds a `PinholeCamera` from an OpenCV-style calibration, rendered with an
  off-center projection so the principal point is honored, with a `fit` policy
  (`"fit"` letterbox / `"fill"` stretch).
- **Camera view descriptor** — `CameraView` bundles a camera, a per-pane
  `lock` set (`CameraLock`), and an optional `background_image`, passed to
  `SceneView(camera_view=…)`.
- **Camera image background** — `CameraView(background_image=ImageData(...))`
  renders the image as a full-viewport NDC background behind the 3D scene,
  letterboxed to match the camera's `fit` policy.
- **Per-pane entity visibility** — `SceneView(hide=…)` / `SceneView(show=…)`
  filter which scene entities a pane renders, so e.g. a frustum shows only in an
  overview pane.
- **`Frustum` entity** — a visualization-only geometry entity (no multivector)
  with `Frustum.from_camera(camera)` and a `FrustumStyle` (fill, plane opacity,
  line thickness), rendered in the live viewer and HTML export.
- **2D viewport navigation** — `CameraView(navigation="2d", …)` switches a pane
  to dolly zoom + screen-space pan (no orbit) with cursor-anchored zoom and a
  per-pane `controls` button mapping.  An optional `viewport` (`ViewportConfig`)
  folds a `{zoom, pan}` crop window into the pinhole projection *and* its
  background image so they stay pixel-locked.  `Visualizer.set_viewport(view, …)`
  (per-pane) and `set_viewport(scene_name=…)` / `VizSceneHandle.set_viewport(...)`
  (scene default) set or reset it at runtime.
- **Calibrated-camera example (BOP T-LESS)** — `pinhole_calibrated.py` bundles
  one real T-LESS training image with its pinhole calibration and the
  ground-truth 6D pose of object 1 (CC BY 4.0), rendering the GT bounding box
  pixel-accurately over the photo (left) with a frustum + GT box overview and an
  attribution annotation (right).
- **Coordinate frames + camera calibration** — `Matrix` (a plain numeric square
  matrix) with a `MatrixProvider` protocol and a `Matrix.from_R_t(R, t)` rigid
  constructor, `CoordinateFrame`/`OpenCVFrame` axis conventions, and
  `CameraCalibration(K, R, t, image_size, frame, units)` which translate
  read-in OpenCV-style calibration into the right-handed internal world and a
  `PinholeCamera`, plus `world_to_camera()` / `camera_to_world()` transform
  matrices; frames satisfy `MatrixProvider`, so `set_transform(frame)` remaps
  OpenCV-frame data through the scene graph.

## Bug Fixes

- **Data background image orientation** — a data-path background image is no
  longer vertically flipped: `DataTexture` defaults to `flipY = false`, which the
  NDC background now flips so data and URL backgrounds line up with the 3D
  projection.
- **`Circle` center update** — moving a `Circle`'s center is now a `transform`
  patch applied to the entity's wrapping group (placement), not a content patch
  the renderer must re-apply; this fixes the stale-mesh bug where a center-only
  change was silently dropped.

## Refactor

- **Canonical frame + transform placement** — every scene entity now renders in
  a canonical frame (linear primitives along +Y, planar primitives in XY/+Z,
  volumes at the origin) with all placement and rotation carried by a single
  per-entity `Transform` whose rotation is a quaternion (the wire
  `transform.rotation: [x, y, z, w]`).  `Transform` and the transform math moved
  into `pytanga.geometry` (`transform.py` / `transforms.py`); `viz` keeps thin
  re-export shims and `Transform` gains `@`/`*` operator overloads for `Point`
  and `Direction`.
- **Shape-only serialization** — the serializer no longer emits
  `center`/`normal`/`axis`/`origin`/`direction`/`vertex`/`rotation`/
  `startDirection`; placement rides on the node `transform`, and `set_entity`
  diffs shape vs placement (configurable epsilon) so float noise doesn't
  recreate meshes.  The glTF exporter reads the node transform directly.
- **`Frustum` re-parameterization** — `Frustum` now carries intrinsic shape +
  placement (`origin`/`axis`/`horizontal`/`near`/`far`/`far_half_width`/
  `far_half_height`) instead of raw corner tuples, so it participates in
  transform placement and diffing like the other entities.
