# Display a numpy image and draw pixel-coordinate overlays

**Keywords:** image · ImageCanvas · shader · uniform · brightness · contrast · overlay · pixels

Shows a synthetic RGB gradient in an `~pytanga.viz.ImageCanvas` (a
dedicated 2D scene with a y-down pixel frame, 1 unit = 1 pixel), draws a
rectangle overlay in pixel coordinates, and binds a ctrl+left-drag handler that
maps the cursor position to the image's brightness/contrast uniforms.

The ctrl+left-drag is registered as a `~pytanga.viz.DragBinding` (a
mouse-button + modifier combination) via the canvas's `drag_handlers` list.

## Run

```bash
uv run python py/examples/viz/image/image_canvas.py
```

## Source

[`viz/image/image_canvas.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/image_canvas.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_canvas.py — Display a numpy image and draw pixel-coordinate overlays.

Shows a synthetic RGB gradient in an :class:`~pytanga.viz.ImageCanvas` (a
dedicated 2D scene with a y-down pixel frame, 1 unit = 1 pixel), draws a
rectangle overlay in pixel coordinates, and binds a ctrl+left-drag handler that
maps the cursor position to the image's brightness/contrast uniforms.

The ctrl+left-drag is registered as a :class:`~pytanga.viz.DragBinding` (a
mouse-button + modifier combination) via the canvas's ``drag_handlers`` list.

Run with:  uv run python py/examples/viz/image/image_canvas.py

Keywords: image, ImageCanvas, shader, uniform, brightness, contrast, overlay, pixels
"""

import numpy as np

from pytanga.geometry import Line, Point
from pytanga.viz import (
    ActRectangle2D,
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
    corners = [
        Point(float(x0), float(y0), 0.0),
        Point(float(x1), float(y0), 0.0),
        Point(float(x1), float(y1), 0.0),
        Point(float(x0), float(y1), 0.0),
    ]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        canvas.add(Line.from_points(a, b), color="#ff4444")


def main() -> None:
    width, height = 320, 200
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    async def on_drag(event: DragEvent, canvas: ImageCanvas) -> bool:
        # ctrl+left drag: horizontal position → contrast, vertical → brightness.
        px, py = event.world_position.x, event.world_position.y
        canvas.set_uniform("u_contrast", 0.5 + 1.5 * px / width)
        canvas.set_uniform("u_brightness", (py / height - 0.5) * 2.0)
        return True

    canvas = ImageCanvas(
        viz,
        drag_handlers=[DragBinding(MouseButton.LEFT, on_drag, ModifierKey.CTRL)],
    )
    canvas.set_image(ImageData("gradient", data=_gradient(width, height)))
    _rectangle(canvas, 40, 30, 160, 120)

    def on_rect(rect: ActRectangle2D) -> None:
        print(f"Rectangle drawn: {rect.rectangle}")

    # Drag on the image to draw a rectangle; it becomes an interactive
    # ActRectangle2D (drag corners to resize, the centre handle to translate).
    # While this draw mode is active, the ctrl+left brightness drag above is
    # paused and resumes once the rectangle is finalized.
    canvas.draw_rectangle(on_done=on_rect)

    viz.show(layout=canvas.scene_view())
    viz.wait()


if __name__ == "__main__":
    main()
````
