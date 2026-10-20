# Changes since version 2.21.0

## Bug Fixes

- **Solid-surface default opacity is now `1.0`** — `Plane`, `Sphere`,
  `Ellipsoid`, `Disk`, `PartialDisk`, `Box`, `Cylinder`, and `Cone` now default
  to fully opaque (previously `Plane` was `0.3` and the others `0.9`), and the
  frontend renderer fallbacks match.
- **Standard texture map honors the texture alpha channel** — the standard
  surface texture map now outputs `opacity × texel.a` (the entity opacity times
  the sampled texture alpha), so RGBA textures render their alpha instead of
  being forced opaque.
- **Surface shaders receive the entity opacity** — custom surface shaders now
  get the entity's resolved opacity as the `u_opacity` uniform (previously
  hard-coded to `1.0`), and `viz.update(..., opacity=…)` updates it in place.
- **Tiled background images register their pyramid on self-push** — a bound
  background `ImageView` now registers a changed layer's image pyramid (and
  unregisters it on `set_layer`/`remove_layer`), and `set_layout` registers the
  pyramids of every layer, so a large image swapped in later with `set_image`,
  `add_layer`, or `set_layer` no longer renders black.
- **Tiled background images re-resolve their pyramid level on zoom** — a
  `CameraView(…, navigation="2d", background_image=…)` pane now picks a
  higher-resolution tile level as its crop window shrinks (zoom in) instead of
  sampling a fixed level, so zooming shows the full image resolution.
- **Tiled background swaps survive a reconnect** — a bound background
  `ImageView` self-push now re-serializes the cached layout and prunes the stale
  binary frame, so a hard refresh rebuilds the swapped (tiled) image instead of
  the pre-swap placeholder.
