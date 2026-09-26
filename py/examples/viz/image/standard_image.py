# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""standard_image.py — Display an 8-bit image over the default (JPEG) transport.

Shows a synthetic RGB pattern in an :class:`~pytanga.viz.ImageCanvas`.  By
default 8-bit 1/3-channel images are transmitted as JPEG (in-band over the
WebSocket); pass ``ImageData(codec=EImageCodec.RAW)`` / ``codec=EImageCodec.ZLIB``
to force a lossless codec instead.

The pattern is a red→green→blue ramp along the diagonal from top-left to
bottom-right, so any vertical flip is immediately visible.

Run with:  uv run python py/examples/viz/image/standard_image.py

Keywords: image, ImageCanvas, ImageData, jpeg, codec, uint8
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8.

    Red at top-left → green at the centre → blue at bottom-right.
    """
    ys, xs = np.mgrid[0:height, 0:width]
    t = (xs + ys) / max(width + height - 2, 1)  # 0 at TL, 1 at BR
    r = np.zeros_like(t)
    g = np.zeros_like(t)
    b = np.zeros_like(t)
    lo = t <= 0.5
    r[lo] = (1.0 - 2.0 * t[lo]) * 255
    g[lo] = (2.0 * t[lo]) * 255
    hi = ~lo
    g[hi] = (2.0 - 2.0 * t[hi]) * 255
    b[hi] = (2.0 * t[hi] - 1.0) * 255
    return np.stack([r, g, b], axis=-1).astype(np.uint8)


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("standard", data=_gradient(320, 200)))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
