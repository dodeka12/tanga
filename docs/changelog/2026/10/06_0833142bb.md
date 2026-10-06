# Changes since version 2.15.0

## New Features

- **`image_codec` export option** — `export_snapshot` / `export_figure` /
  `display_snapshot` / `start_animation_recording` accept
  `image_codec: EImageCodec | None = None`.  `None` auto-selects JPEG
  (honoring `ImageData.jpeg_quality`) for uint8 1/3-channel images and
  lossless zlib otherwise; `RAW` / `JPEG` / `ZLIB` force a codec.  Non-JPEG
  images (uint16/float32/RGBA) are now zlib-compressed instead of raw base64,
  and `JPEG` on a non-eligible image raises a clear error.

## Bug Fixes

- **Image-bearing HTML export now renders images** — the export bootstrap
  called `storeImageFrame` without it being exposed on the `window.__tanga`
  bridge, so static and animated image exports threw
  `ReferenceError: storeImageFrame is not defined`.  The frame-store helpers
  (`storeImageFrame`, `takeImageFrame`, `hasImageFrame`,
  `registerImageFrameConsumer`) are now part of the bridge.

- **Compressed animated exports no longer race the decompression** —
  `compress=True` decompressed the animation JSON in an async module while the
  bootstrap read it synchronously, which could leave the animation empty.  The
  decompression now exposes a `window.__tangaAnimReady` promise that the
  bootstrap awaits before reading the data.

- **2D HTML exports no longer throw `applyOrthoFrustum is not defined`** — the
  2D resize handler referenced `applyOrthoFrustum` (from `camera-fit.js`)
  without it being exposed on the `window.__tanga` bridge; it is now part of
  the bridge.

- **`delivery="offline"` works on Linux again** — the offline export ran
  esbuild through Node.js unconditionally, which fails on Unix where
  `bin/esbuild` is a native ELF/Mach-O binary (Node chokes on it with a
  `SyntaxError`).  esbuild is now invoked directly on Unix and via Node only
  on Windows (where `bin/esbuild` is a JS launcher).
