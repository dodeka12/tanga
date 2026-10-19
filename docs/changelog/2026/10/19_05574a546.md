# Changes since version 2.20.0

## New Features

- **8-layer image views, configured dynamically** — `ImageView` supports up to
  8 layers by default (the WebGL 1 fragment-texture-unit floor) instead of 4,
  and the count is serialized as `max_layers` so the frontend builds exactly that
  many samplers/uniforms — a later change can adopt the runtime
  `MAX_TEXTURE_IMAGE_UNITS` with no wire change.
- **Background images push their own updates** — a
  `CameraView.background_image` `ImageView` is bound to its pane when the layout
  is registered, so `set_image`/`add_layer`/`set_layer`/`set_layer_style`/
  `set_uniform` emit granular `view_background_image`/`view_background_uniforms`
  updates themselves (per-layer pixel changes re-send only the changed layer's
  frame), and `remove_layer(i)` / `set_layer(i, None)` clears a layer in place
  with stable indices.
- **Per-layer colormap + RGBA alpha compositing** — `ImageLayerStyle.colormap`
  (`gray`/`viridis`/`turbo`) colors scalar (1-channel) layers, and 4-channel
  layers now respect their texture alpha when composited with the layer opacity
  and blend mode.
- **Pinhole depth mode** — `DepthImageStyle(camera=…, depth_kind=…,
  apply_pose=…)` renders a calibrated depth map as camera-frame vertices
  (`X = (u−cx)/fx·z`, `Y = (v−cy)/fy·z`, `Z = z`), accepting a
  `CameraCalibration` or `PinholeCamera` and optionally auto-applying the
  calibration pose, so the surface aligns with other calibrated entities.
- **`look_at_matrix` geometry helper** — `pytanga.geometry.transforms.look_at_matrix`
  returns a 4×4 rotation whose +z axis points along a given forward direction,
  with an `up` reference and a least-aligned-axis fallback when they are
  (anti-)parallel, so callers no longer hand-roll look-at rotations; the pinhole
  depth example now uses it with an explicit `OpenCVFrame` conversion.
- **Surface texture mapping** — solid surface entities (`Plane`, `Sphere`,
  `Ellipsoid`, `Disk`, `Box`, `Cylinder`, `Cone`) now accept a `surface` material
  (an image, a custom GLSL program, or both) via `viz.add`/`viz.new`/`viz(...)`
  or the per-kind style.  Texture pixels travel as binary image frames with an
  optional codec (JPEG by default for `uint8` images), and surface materials are
  opaque by default.
- **Standard surface shaders** — a new `pytanga.viz.surface` subpackage ships
  `checkerboard`, `sphere_coloring`, `grid`, and `gradient` shaders.  The
  standard texture shader and custom surface shaders use the shared global scene
  lighting uniforms (`uLightCount`/`uLightDir[]`/`uLightColor[]`/`uAmbientColor`),
  which are documented for custom shaders.
- **In-place surface shader uniform updates** — shader parameters can be changed
  at runtime without re-adding the entity.
  `Visualizer.set_surface_uniform(...)` and `VizObjectRef.set_surface_uniform(...)`
  queue the change and it is applied in one batched `object_update` on `flush()`,
  while also being stored back into the surface style for later re-serialization.
- **Shader compile error reporting** — the viewer now reports shader compile/link
  failures to the backend over the client-log channel (`source: "shader"`).
  `Visualizer.on_shader_error(handler)` lets apps surface the driver's error in a
  banner.
- **Scrollable banners** — `viz.show_banner(..., scrollable=True)` renders the
  title pinned at the top with the markdown body as a dedicated scroll region
  filling most of the banner, for long-form output such as shader compile errors.
- **Examples** — `py/examples/viz/surface/texture_mapping.py` (switch a sphere,
  plane, box, and cylinder between a standard texture map and a custom twirl
  shader, with a twirl-amount slider) and
  `py/examples/viz/surface/shader_errors.py` (capture a shader compile error and
  show it in a scrollable banner).

