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

## When to use which

- **Standard / camera images** — leave the default; 8-bit images compress to
  JPEG automatically.
- **Scientific / HDR data** — use `uint16`/`float32` (lossless zlib) or pass
  `codec=EImageCodec.RAW` for an exact, uncompressed round-trip.
- **Very large images** — see [Tiled images](tiled-images.md).
- **Live camera feeds** — see [Image streams](image-stream.md).
