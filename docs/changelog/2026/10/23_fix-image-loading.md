# Changes since version 2.24.1

## New Features
- **Image load events** — `Visualizer.on_image_loaded`,
  `Visualizer.on_image_tile_load`, and `Visualizer.on_image_tile_loaded` let a
  backend handler react when an image first becomes ready in the browser or when
  a tiled-pyramid level starts / finishes loading (a "loading…" / "ready"
  indicator driven by the frontend).  Handlers are typed via
  `ImageStatusHandler` and receive an `ImageStatusRecord`; the
  `huge_image_background.py` (log view) and `image_load_events.py` (banner)
  examples demonstrate the flow.

## Bug Fixes
- **Pyramid LOD toggle** — a tiled image no longer flips between two resolution
  levels at a power-of-two zoom boundary: `levelForScreen` now applies a
  hysteresis dead-band and `updateImageLod` tracks a generation token so a stale
  fetch cannot overwrite a newer texture.
