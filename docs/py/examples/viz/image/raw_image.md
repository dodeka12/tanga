# Display a 16-bit image over the lossless (zlib) transport

**Keywords:** image · ImageCanvas · ImageData · uint16 · lossless · codec · zlib

Shows a uint16 ramp in an `~pytanga.viz.ImageCanvas`.  uint16/float32
images are never JPEG-compressed (JPEG is 8-bit), so they stay lossless by
default; pass `codec="raw"` to disable even the zlib step.

## Run

```bash
uv run python py/examples/viz/image/raw_image.py
```

## Source

[`viz/image/raw_image.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/raw_image.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""raw_image.py — Display a 16-bit image over the lossless (zlib) transport.

Shows a uint16 ramp in an :class:`~pytanga.viz.ImageCanvas`.  uint16/float32
images are never JPEG-compressed (JPEG is 8-bit), so they stay lossless by
default; pass ``codec="raw"`` to disable even the zlib step.

Run with:  uv run python py/examples/viz/image/raw_image.py

Keywords: image, ImageCanvas, ImageData, uint16, lossless, codec, zlib
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer


def _ramp(width: int, height: int) -> np.ndarray:
    """A single-channel uint16 horizontal ramp of shape (H, W)."""
    ys, xs = np.mgrid[0:height, 0:width]
    return (xs / max(width - 1, 1) * 65535).astype(np.uint16)


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("raw", data=_ramp(320, 200)))
    # Normalize the 16-bit range for display (the pixels stay lossless on the
    # wire — only the shader's value range changes).
    canvas.set_uniform("u_value_min", 0)
    canvas.set_uniform("u_value_max", 65535)
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
````
