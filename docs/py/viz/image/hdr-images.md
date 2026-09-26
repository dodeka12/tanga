# HDR images (EXR / Radiance)

Load floating-point HDR images without Pillow or the `OpenEXR` package — the
readers use only numpy plus the standard library:

```python
import numpy as np
from pytanga.viz import ImageCanvas, ImageData, Visualizer
from pytanga.viz.image import read_exr, read_hdr

hdr = read_hdr("studio.hdr")       # Radiance RGBE (.hdr / .pic)
exr = read_exr("render.exr")       # OpenEXR (.exr)

viz = Visualizer(add_default_axes=False, space_dim=2)
canvas = ImageCanvas(viz)
canvas.set_image(ImageData("image", data=exr))
```

Both return a **linear** `float32` array of shape `(H, W, C)` with **no tone
mapping and no colour-space conversion** — the raw stored values, exactly what
you want for quantitative work, compositing, or a custom shader.

## `read_exr`

- **Codecs** — `NONE`, `RLE`, `ZIPS`, `ZIP`, and `PIZ` (the common HDRI codec).
- **Channel types** — `UINT`/`HALF`/`FLOAT`, decoded to `float32`; the `R, G, B`
  channels are selected (plus `A` when present).
- **PIZ fast path** — large PIZ EXRs decode through the compiled `binding_piz`
  extension when available, transparently falling back to a pure-numpy decode
  (no `OpenEXR` dependency either way).
- **Scope** — single-part, scanline images with 1×1 channel sampling.
  Tiled/deep/multi-part files and subsampled channels raise `ValueError`.
- The `dataWindow` extent is returned; `displayWindow` cropping is ignored.

## `read_hdr`

- **Pixel encoding** — flat RGBE and the standard new (adaptive) RLE
  (`32-bit_rle_rgbe`).
- **Orientation** — honours the `-Y/+Y` and `+X/-X` resolution-line signs.
- **Values** — `v = (m + 0.5) / 256 · 2^(e − 128)`, with a shared zero exponent
  mapping to `0.0`.

## Loading progress

Both readers decode chunk-by-chunk / scanline-by-scanline, so they can report
progress to a callback — useful for large HDRIs:

```python
from pytanga.viz.image import read_exr, register_loading_progress_handler

register_loading_progress_handler(lambda frac: print(f"{int(frac * 100)}%"))
img = read_exr("render.exr")            # calls the handler as it decodes
register_loading_progress_handler(None)  # clear it again
```

A per-call `on_progress=` argument overrides the registered handler:

```python
img = read_exr("render.exr", on_progress=lambda frac: update_ui(frac))
```

## Displaying HDR values

`ImageCanvas` normalises its image to `[u_value_min, u_value_max]` for display.
Because HDR pixels routinely exceed `1.0`, the default range clamps them to
white — set a wider range (or a custom shader) to see the full dynamic range:

```python
canvas.set_uniform("u_value_max", 8.0)   # e.g. show up to 8.0
```

See [Custom Shaders](custom-shaders.md) for replacing the fragment shader
entirely, and [Image transport](image-transport.md) for how the `float32`
buffer travels to the browser losslessly.

## Large images

A `float32` HDR frame is large, so `ImageData` automatically converts an array
whose longest side exceeds 4096 px (or whose byte size exceeds 32 MB) into an
**on-demand tile pyramid** — the frontend then fetches only the tiles it needs.
Pass `tile_max_dim=None, tile_max_bytes=None` to `ImageData` to opt out.  See
[Tiled images](tiled-images.md).
