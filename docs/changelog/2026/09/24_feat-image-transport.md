# Changes since version 2.10.0 (2.11.0-rc1)

## New Features

- **Image transport codecs** — binary image frames now carry a versioned
  `codec` byte (`raw`/`jpeg`/`zlib`), auto-selecting JPEG for 8-bit 1/3-channel
  images and lossless zlib otherwise, overridable per image via
  `ImageData(codec=…, jpeg_quality=…)`.
- **Tiled images** — `Visualizer.register_image_pyramid` serves very large
  images as an on-demand `/image/{id}/{level}/{x}/{y}` tile pyramid with a
  server-side LRU, so the frontend fetches only the visible region.
- **Image streams** — `Visualizer.register_camera_stream` streams 15–30 Hz
  camera feeds as MJPEG over `/stream/{id}`.
- **JPEG-by-default HTML export** — the export asset store embeds eligible
  8-bit images as JPEG data URLs instead of raw base64, with a lossless
  fallback for 16-bit/float/4-channel data.
