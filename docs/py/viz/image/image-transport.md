# Image transport (codecs)

Images travel from Python to the browser as **binary WebSocket frames** with a
small codec byte.  By default pytanga picks the codec for you; you can override
it per image.

## Codec selection

| Codec | Wire | Description |
|-------|------|-------------|
| `None` (default) | — | JPEG for `uint8` 1/3-channel, lossless zlib otherwise |
| `EImageCodec.JPEG` | 1 | Lossy 8-bit JPEG (display path) |
| `EImageCodec.ZLIB` | 2 | Lossless zlib-compressed raw pixels (`uint16`/`float32`) |
| `EImageCodec.RAW` | 0 | Uncompressed raw pixels (the pre-codec behaviour) |

```python
import numpy as np
from pytanga.viz import EImageCodec, ImageData

# uint8 RGB → JPEG by default (small, fast).
rgb = ImageData("photo", data=np.zeros((480, 640, 3), dtype=np.uint8))

# uint16 / float32 → lossless zlib by default (never JPEG, which is 8-bit).
depth = ImageData("depth", data=np.zeros((480, 640), dtype=np.uint16))

# Force a codec (or disable compression entirely):
exact = ImageData("raw", data=np.zeros((480, 640, 3), dtype=np.uint8), codec=EImageCodec.RAW)
```

- JPEG is **lossy and 8-bit** — use it for photos/camera frames, not for
  quantitative pixel inspection.
- `uint16`/`float32` and 4-channel images are **never** JPEG-compressed, so
  scientific/HDR data stays lossless out of the box.
- `jpeg_quality=…` (default `85`) tunes the JPEG quality.

## Version & in-place updates

Every `ImageData` instance carries a `version` — a fresh uuid string assigned at
construction — that identifies the image content.  pytanga uses it to avoid
re-sending an unchanged background image on a layout re-push: **reuse the same
`ImageData` instance** while the content is unchanged, and change the content
(and the version) only when the pixels actually change.

```python
img = ImageData("camera", data=frame0)
viz.set_background_image(view, img)

# later, new pixels: update the same instance in place (bumps `version`):
img.update(data=frame1)
viz.set_background_image(view, img)
```

`ImageData.update(data=…)` (or `update(url=…)`) replaces the content in place,
re-derives the dimensions/dtype and re-applies the auto-tile threshold, and
assigns a fresh `version`.  Passing neither (or both) `data`/`url` raises
`ValueError`.

## When to use which

- **Standard / camera images** — leave the default; 8-bit images compress to
  JPEG automatically.
- **Scientific / HDR data** — use `uint16`/`float32` (lossless zlib) or pass
  `codec=EImageCodec.RAW` for an exact, uncompressed round-trip.  Load EXR and
  Radiance HDR files directly with `read_exr`/`read_hdr` — see
  [HDR images](hdr-images.md).
- **Very large images** — see [Tiled images](tiled-images.md).
- **Live camera feeds** — see [Image streams](image-stream.md).
