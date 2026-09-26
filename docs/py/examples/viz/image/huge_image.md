# Display a large image as an on-demand tile pyramid

**Keywords:** image · pyramid · tiles · register_image_pyramid · large image

Generates a large programmatic image, registers it with
`~pytanga.viz.Visualizer.register_image_pyramid`, and shows it in an
`~pytanga.viz.ImageCanvas`.  The frontend fetches only the tiles it
needs from `/image/{id}/{level}/{x}/{y}` instead of the whole array.

The image is a red→green→blue ramp along the diagonal from top-left to
bottom-right, so any vertical flip (or wrong pyramid level) is immediately
visible.

## Run

```bash
uv run python py/examples/viz/image/huge_image.py
```

## Source

[`viz/image/huge_image.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/huge_image.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""huge_image.py — Display a large image as an on-demand tile pyramid.

Generates a large programmatic image, registers it with
:meth:`~pytanga.viz.Visualizer.register_image_pyramid`, and shows it in an
:class:`~pytanga.viz.ImageCanvas`.  The frontend fetches only the tiles it
needs from ``/image/{id}/{level}/{x}/{y}`` instead of the whole array.

The image is a red→green→blue ramp along the diagonal from top-left to
bottom-right, so any vertical flip (or wrong pyramid level) is immediately
visible.

Run with:  uv run python py/examples/viz/image/huge_image.py

Keywords: image, pyramid, tiles, register_image_pyramid, large image
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer

WIDTH, HEIGHT = 8192, 4096


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8.

    Red at top-left → green at the centre → blue at bottom-right.  Uses float32
    intermediates so an 8k×4k pyramid stays within a modest memory budget.
    """
    xs = np.arange(width, dtype=np.float32)
    ys = np.arange(height, dtype=np.float32)
    t = (xs[None, :] + ys[:, None]) / max(width + height - 2, 1)
    out = np.zeros((height, width, 3), dtype=np.uint8)
    lo = t <= 0.5
    out[..., 0][lo] = ((1.0 - 2.0 * t[lo]) * 255).astype(np.uint8)
    out[..., 1][lo] = ((2.0 * t[lo]) * 255).astype(np.uint8)
    hi = ~lo
    out[..., 1][hi] = ((2.0 - 2.0 * t[hi]) * 255).astype(np.uint8)
    out[..., 2][hi] = ((2.0 * t[hi] - 1.0) * 255).astype(np.uint8)
    return out


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    pyramid = viz.register_image_pyramid(
        "gradient", _gradient(WIDTH, HEIGHT), tile_size=256
    )
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("gradient", tiled=pyramid))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
````
