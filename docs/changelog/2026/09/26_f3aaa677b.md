# Changes since version 2.11.0

## New Features

- **Dependency-free HDR image readers** — `pytanga.viz.image.read_exr` and
  `pytanga.viz.image.read_hdr` load OpenEXR (`NONE`/`RLE`/`ZIPS`/`ZIP`/`PIZ`;
  `UINT`/`HALF`/`FLOAT` channels) and Radiance RGBE (`.hdr`/`.pic`) images into
  linear `float32` arrays using only numpy plus the standard library — no
  Pillow or `OpenEXR` package.  `load_image_from_disk.py` now dispatches
  `.exr`/`.hdr`/`.pic` to them.
- **Automatic tiling + load progress** — `ImageData` now converts any pixel
  array whose longest side exceeds 4096 px (or whose byte size exceeds 32 MB)
  into an on-demand tile pyramid (`tile_max_dim`/`tile_max_bytes`/`tile_size`;
  pass `None` to opt out), registered automatically by `ImageCanvas`.
  `read_exr`/`read_hdr` report progress via a per-call `on_progress` callback or
  a `register_loading_progress_handler` handler.
- **Fast PIZ decoding for large EXRs** — the PIZ codec's Huffman/wavelet/range
  decode is now vectorized in numpy and accelerated by a compiled `binding_piz`
  extension (with a pure-numpy fallback, `PYTANGA_FORCE_PURE_PYTHON=1`), so
  multi-megapixel PIZ EXRs load in seconds instead of minutes.
- **Tiled float images keep their full dynamic range** — `float32`/`uint16`
  pyramid tiles now stream as lossless zlib-compressed raw pixels and are
  assembled into a float texture, so `u_value_min`/`u_value_max` and
  brightness/contrast operate on the full range instead of an 8-bit canvas.
- **File-chooser dialog** — `FileChooserDialog` (via `Visualizer.show_dialog`)
  opens a modal directory listing with a path line and OK/Cancel: `file_filter`
  accepts glob patterns, `folders_only` restricts to directories, and a single
  click selects (double-click or OK confirms) via `on_accept`/`on_close`.

## Bug Fixes

- **Tiled float32/uint16 images no longer crash in PNG encoding** — the tile
  pyramid's PNG encoder passed `float32` and multi-channel `uint16` tiles
  straight to Pillow, which has no such mode, so large HDR (e.g. 4-channel
  `float32` EXR) tiles raised `TypeError` and rendered black.  Those tiles are
  now normalized to 8-bit (float32 → `[0, 1]`, uint16 → `[0, 65535]`, matching
  `default_value_range`) before encoding.
- **Tiled images render the correct pyramid level** — `makeTiledTexture` picked
  the coarsest pyramid level because its selection loop compared the original
  full-resolution dimensions every iteration instead of the current level's own
  dimensions.  It now walks down the pyramid tracking each level's size and
  stops at the finest level whose long side fits the texture budget, so both
  tiled `ImageCanvas` layers and tiled `CameraView.background_image` images
  display at full detail.
- **JPEG images no longer render upside-down** — the JPEG decode path created a
  `THREE.Texture` directly from an `ImageBitmap`, which renders vertically
  flipped because `ImageBitmap` uploads don't honor `flipY` the way raw pixel
  data does.  The renderer now draws the decoded bitmap into a 2D canvas and
  returns a `CanvasTexture` (matching the tiled/stream paths), so JPEG, lossless
  (`uint16`/`float32`/raw), URL, tiled, and MJPEG all render row 0 at the top.
- **Image value range resets when the primary image is replaced** —
  `ImageView.set_image` seeded `u_mode`/`u_value_min`/`u_value_max` with
  `setdefault`, so replacing the primary image with a different dtype kept the
  old normalization range (a `uint16` image loaded after a `uint8` placeholder
  clamped to white).  `set_image` now re-derives those defaults from the new
  image.
- **Images minify smoothly** — image textures now use mipmaps + trilinear
  minification (8-bit) or bilinear minification (`uint16`/`float32`), and the
  default fragment shader samples via `texture2D(uImage0, vUv)`, so a large
  image scaled down no longer aliases/flickers.
- **Image brightness/contrast drag is relative, not absolute** — the example
  `on_drag` handlers mapped the cursor's absolute pixel position to the
  `u_brightness`/`u_contrast` (and `u_angle`) uniforms, so the value jumped to
  the clicked pixel instead of changing by the drag amount.  They now
  accumulate `event.delta_pixels` onto the current value.
