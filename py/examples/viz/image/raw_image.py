# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""raw_image.py — Display a 16-bit image over the lossless (zlib) transport.

Shows a uint16 RGB gradient in an :class:`~pytanga.viz.ImageCanvas`.  uint16
images are never JPEG-compressed (JPEG is 8-bit), so they stay lossless by
default; pass ``codec="raw"`` to disable even the zlib step.

The gradient is a red→green→blue ramp along the diagonal from top-left to
bottom-right, so any vertical flip is immediately visible.

Run with:  uv run python py/examples/viz/image/raw_image.py

Keywords: image, ImageCanvas, ImageData, uint16, lossless, codec, zlib
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel uint16 RGB gradient of shape (H, W, 3).

    Red at top-left → green at the centre → blue at bottom-right, scaled to the
    full 0..65535 uint16 range.
    """
    xs = np.arange(width, dtype=np.float32)
    ys = np.arange(height, dtype=np.float32)
    t = (xs[None, :] + ys[:, None]) / max(width + height - 2, 1)
    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)
    lo = t <= 0.5
    r[lo] = (1.0 - 2.0 * t[lo]) * 65535
    g[lo] = (2.0 * t[lo]) * 65535
    hi = ~lo
    g[hi] = (2.0 - 2.0 * t[hi]) * 65535
    b[hi] = (2.0 * t[hi] - 1.0) * 65535
    return np.stack([r, g, b], axis=-1).astype(np.uint16)


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    # The default uint16 value range is 0..65535, which matches the data.
    canvas.set_image(ImageData("raw", data=_gradient(320, 200)))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
