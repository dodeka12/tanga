# Changes since version 2.19.1

## New Features
- **Depth image (2.5D surface) entity** — `DepthImage`/`DepthImageData` render a
  per-pixel depth map as a 3D heightfield surface via `viz.add(...)`, with a
  depth-colormap default shader, optional texture-mapped source image, plain or
  custom shaders, and a segmentation mask that discards non-selected segments.
  `DepthImageStyle` controls the mesh/texture downscaling (only the needed
  resolution is transmitted) and reuses `EImageCodec` for per-frame compression.
- **Multi-layer image canvas & calibrated background** — `ImageView` and
  `CameraView.background_image` now hold up to 4 layers, each with per-layer
  enable / opacity / blend mode (normal/add/multiply/screen) and per-layer
  value-range normalization via `u_layer{i}_*` uniforms; the default shader
  composites the layers bottom-up, and a new `image_layers.py` example exposes
  per-layer controls.
- **`ImageLayerStyle` layer descriptor** — `ImageView`/`ImageCanvas` accept an
  `ImageLayerStyle` (enabled / opacity / blend / channel / value range) on
  `set_image`/`add_layer`/`set_layer` and merge partial updates via
  `set_layer_style`; `add_layer` returns the new layer index.
- **Per-scene lighting (ambient + directional + specular)** — a single
  `SceneLighting` configuration now drives the standard `MeshPhongMaterial`
  entities, the ray-marched SDF renderer, and the depth-image surface from one
  setup.  Set it at build time via `SceneConfig(lighting=...)` or at runtime
  with `viz.set_scene_lighting(...)`, which re-lights everything without a scene
  rebuild.  The depth surface's `"plain"` render mode is now Blinn-Phong shaded
  in world space, exposed through the new `DepthImageStyle` `shininess` /
  `specular` knobs, and a new `py/examples/viz/lighting/scene_lighting.py`
  example switches lighting presets across a mesh sphere, an SDF cylinder, and a
  depth sine wave at once.

## Breaking Changes
- **Tiled image cache key renamed** — `ImagePyramid.meta()` now emits
  `tile_version` for the tile URL cache key (the `ImageData` uuid is emitted as
  `version`), so the two `version` concepts are no longer conflated.
- **`LayerBlendMode` is now a string enum** — values are `"normal"`/`"add"`/
  `"multiply"`/`"screen"` (`.code` gives the wire int); `ImageCanvas.add_image`
  is renamed `add_layer`; the granular `set_layer_enabled`/`set_layer_opacity`/
  `set_layer_blend`/`set_layer_value_range`/`set_layer_channel` setters are
  replaced by `set_layer_style`.

## Bug Fixes
- **SDF objects render again** — the per-object SDF serializer emitted its
  node transform rotation as a 3-element Euler triple, which the frontend reads
  as a 4-element quaternion (a missing `w` produced a NaN matrix and made the
  proxy invisible).  It now emits an identity quaternion `[0, 0, 0, 1]`.

## Refactor
- **Canonical per-image serialization** — `ImageData.layer_meta()` /
  `ImageView.serialized_images()` emit one per-image dict for `data`/`url`/
  `tiled`, so transport no longer changes the layer schema.
- **Animated HTML export stores per-frame entity deltas** — `AnimationRecording`
  now serializes an animated recording as frame 0 plus a per-frame list of only
  the entities that changed or were removed, instead of a full id-keyed snapshot
  per frame.  The playback bootstrap expands those deltas back to full frames at
  load before reconciling, so static entities are stored once and exported files
  are smaller; playback and scrubbing are unchanged.  `to_dict()` still emits the
  full `frames` list for backward compatibility.
