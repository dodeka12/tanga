# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_canvas.py — Display a numpy image and draw pixel-coordinate overlays.

Shows a synthetic RGB gradient in an :class:`~pytanga.viz.ImageCanvas` (a
dedicated 2D scene with a y-down pixel frame, 1 unit = 1 pixel), draws a
:class:`~pytanga.geometry.Rectangle2D` overlay (via
:meth:`~pytanga.geometry.Rectangle2D.between`) in pixel coordinates, and binds
a ctrl+left-drag handler that adjusts the image's brightness/contrast uniforms
by the relative drag distance.

The ctrl+left-drag is registered as a :class:`~pytanga.viz.DragBinding` (a
mouse-button + modifier combination) via the canvas's ``drag_handlers`` list.

Run with:  uv run python py/examples/viz/image/image_canvas.py

Keywords: image, ImageCanvas, rectangle, Rectangle2D, shader, uniform, overlay, pixels
"""

import numpy as np

from pytanga.geometry import Point, Rectangle2D
from pytanga.viz import (
    DragBinding,
    DragEvent,
    ImageCanvas,
    ImageData,
    ModifierKey,
    MouseButton,
    Visualizer,
)


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


def _rectangle(canvas: ImageCanvas, x0: int, y0: int, x1: int, y1: int) -> None:
    """Draw a rectangle outline in pixel coordinates (y down)."""
    canvas.add(
        Rectangle2D.between(
            Point(float(x0), float(y0), 0.0),
            Point(float(x1), float(y1), 0.0),
        ),
        color="#ff4444",
    )


def main() -> None:
    width, height = 320, 200
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
        # ctrl+left drag: horizontal movement → contrast, vertical → brightness.
        dx, dy = event.delta_pixels
        u = canvas.image_view.uniforms
        canvas.set_uniform("u_contrast", max(0.0, u["u_contrast"] + 0.005 * dx))
        canvas.set_uniform("u_brightness", u["u_brightness"] + 0.005 * dy)
        return True

    canvas = ImageCanvas(
        viz,
        drag_handlers=[DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)],
    )
    canvas.set_image(ImageData("gradient", data=_gradient(width, height)))
    _rectangle(canvas, 40, 30, 160, 120)

    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
