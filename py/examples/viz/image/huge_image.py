# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""huge_image.py — Display a large image as an on-demand tile pyramid.

Generates a large programmatic noise image, registers it with
:meth:`~pytanga.viz.Visualizer.register_image_pyramid`, and shows it in an
:class:`~pytanga.viz.ImageCanvas`.  The frontend fetches only the tiles it
needs from ``/image/{id}/{level}/{x}/{y}`` instead of the whole array.

Run with:  uv run python py/examples/viz/image/huge_image.py

Keywords: image, pyramid, tiles, noise, register_image_pyramid, large image
"""

import numpy as np

from pytanga.viz import ImageCanvas, ImageData, Visualizer

WIDTH, HEIGHT = 8192, 4096


def main() -> None:
    rng = np.random.default_rng(0)
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    noise = rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8)
    pyramid = viz.register_image_pyramid("noise", noise, tile_size=256)
    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("noise", tiled=pyramid))
    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
