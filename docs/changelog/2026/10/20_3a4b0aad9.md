# Changes since version 2.21.1 (2.22.0-rc1)

## New Features
- **Depth-image grazing-angle filter** — `DepthImageStyle(max_grazing_angle=…)`
  (degrees) discards surface that is more edge-on than that angle to the viewing
  ray, removing the stretched border triangles at depth jumps; the threshold is
  the live `u_max_stretch` uniform (`tan(angle)`), changed at runtime via
  `ref.set_uniform("u_max_stretch", …)` without a rebuild or pixel re-send.

## Bug Fixes
- **Background image layers no longer lose their textures after rapid
  `set_layer` updates** — the viewer only re-binds a background layer when its
  image `version` changed, and it sizes data textures from the decoded frame's
  own header instead of the possibly-stale metadata, so a stale one-shot frame
  consumer can no longer decode a large frame into a 1×1 placeholder-sized
  texture and overwrite the correct one.
