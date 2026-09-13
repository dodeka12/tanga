# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""rectangle_labeling.py — Add and drag rectangles on an image via a toolbar.

Shows a synthetic RGB gradient in an :class:`~pytanga.viz.ImageCanvas` inside a
:class:`~pytanga.viz.SplitView`.  A :class:`~pytanga.viz.ToolbarView` with an
icon-only button sits above the image; pressing it arms a
:meth:`~pytanga.viz.ImageCanvas.draw_rectangle` drag — the next drag on the
image draws a rectangle that is finalized into an
:class:`~pytanga.viz.ActRectangle2D` (drag its corner handles to resize, its
centre handle to translate).

Run with:  uv run python py/examples/viz/image/rectangle_labeling.py

Keywords: image, rectangle, ActRectangle2D, split view, toolbar, icon, drag
"""

import numpy as np

from pytanga.viz import (
    ActRectangle2D,
    ButtonView,
    ControlEvent,
    EIconMaterial,
    ImageCanvas,
    ImageData,
    Size,
    SplitView,
    ToolbarView,
    Visualizer,
)


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


def main() -> None:
    width, height = 320, 200
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("gradient", data=_gradient(width, height)))

    def on_rect(rect: ActRectangle2D) -> None:
        print(f"Rectangle drawn: {rect.rectangle}")

    async def on_add(_value: None, _event: ControlEvent) -> None:
        # Arm the draw flow: the next drag on the image draws a rectangle.
        canvas.draw_rectangle(on_done=on_rect)

    toolbar = ToolbarView(
        [
            ButtonView(
                "add_rect",
                icon=EIconMaterial.ADD,
                icon_only=True,
                tooltip="Add rectangle (drag on the image)",
                on_click=on_add,
            ),
        ],
        border=False,
    )

    # A vertical split: the toolbar on top, the image filling the rest.
    layout = SplitView(
        "vertical",
        sizes=[Size.px(40), Size.fr(1)],
        children=[toolbar, canvas.scene_view()],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
