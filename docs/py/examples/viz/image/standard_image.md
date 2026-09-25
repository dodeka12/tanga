# Display an 8-bit image over the default (JPEG) transport

**Keywords:** image · ImageCanvas · ImageData · jpeg · codec · uint8

Shows a synthetic RGB pattern in an `~pytanga.viz.ImageCanvas`.  By
default 8-bit 1/3-channel images are transmitted as JPEG (in-band over the
WebSocket); pass `ImageData(codec=EImageCodec.RAW)` / `codec=EImageCodec.ZLIB`
to force a lossless codec instead.

## Run

```bash
uv run python py/examples/viz/image/standard_image.py
```

## Source

[`viz/image/standard_image.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/standard_image.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""standard_image.py — Display an 8-bit image over the default (JPEG) transport.

Shows a synthetic RGB pattern in an :class:`~pytanga.viz.ImageCanvas`.  By
default 8-bit 1/3-channel images are transmitted as JPEG (in-band over the
WebSocket); pass ``ImageData(codec=EImageCodec.RAW)`` / ``codec=EImageCodec.ZLIB``
to force a lossless codec instead.

Run with:  uv run python py/examples/viz/image/standard_image.py

Keywords: image, ImageCanvas, ImageData, jpeg, codec, uint8
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer


def _pattern(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("standard", data=_pattern(320, 200)))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
````
