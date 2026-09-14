# Add and drag rectangles on an image via a toolbar

**Keywords:** image · rectangle · ActRectangle2D · split view · toolbar · icon · drag · cursor

Shows a synthetic RGB gradient in an `~pytanga.viz.ImageCanvas` inside a
`~pytanga.viz.SplitView`.  A `~pytanga.viz.ToolbarView` with an
icon-only button sits above the image.  The canvas registers a left-mouse drag
handler **disabled**; pressing the button toggles a mode flag that enables the
handler and switches the scene cursor to `crosshair`.  Dragging then draws a
preview `~pytanga.geometry.Rectangle2D`; on release it is finalized into
an `~pytanga.viz.ActRectangle2D` (corner handles resize, the centre
handle translates) and stored in a list.

## Run

```bash
uv run python py/examples/viz/image/rectangle_labeling.py
```

## Source

[`viz/image/rectangle_labeling.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/viz/image/rectangle_labeling.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""rectangle_labeling.py — Add and drag rectangles on an image via a toolbar.

Shows a synthetic RGB gradient in an :class:`~pytanga.viz.ImageCanvas` inside a
:class:`~pytanga.viz.SplitView`.  A :class:`~pytanga.viz.ToolbarView` with an
icon-only button sits above the image.  The canvas registers a left-mouse drag
handler **disabled**; pressing the button toggles a mode flag that enables the
handler and switches the scene cursor to ``crosshair``.  Dragging then draws a
preview :class:`~pytanga.geometry.Rectangle2D`; on release it is finalized into
an :class:`~pytanga.viz.ActRectangle2D` (corner handles resize, the centre
handle translates) and stored in a list.

Run with:  uv run python py/examples/viz/image/rectangle_labeling.py

Keywords: image, rectangle, ActRectangle2D, split view, toolbar, icon, drag, cursor
"""

import numpy as np
from pytanga.geometry import Point, Rectangle2D
from pytanga.viz import (
    ActRectangle2D,
    ButtonView,
    ControlEvent,
    DragBinding,
    DragEvent,
    EIconMaterial,
    ImageCanvas,
    ImageData,
    MouseButton,
    Rectangle2DStyle,
    Size,
    SplitView,
    SquarePointStyle,
    ToolbarView,
    Visualizer,
)

_WIDTH, _HEIGHT = 320, 200


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 128)
    return np.stack([r, g, b], axis=-1)


class RectangleLabeler:
    """Draws rectangles on an ``ImageCanvas`` by left-dragging (when armed)."""

    def __init__(self, viz: Visualizer) -> None:
        self.adding = False
        self.rectangles: list[ActRectangle2D] = []
        self._anchor: Point | None = None
        self._preview_id: str | None = None
        self._style = Rectangle2DStyle(color="#ff4444", fill=True, fill_opacity=0.15)
        # Registered disabled: left-drag does nothing until the mode is armed.
        self._binding = DragBinding(MouseButton.LEFT, self._on_drag, enabled=False)

        self.canvas = ImageCanvas(
            viz,
            drag_handlers=[self._binding],
            on_drag_start=self._on_drag_start,
            on_drag_end=self._on_drag_end,
        )
        self.canvas.set_image(ImageData("gradient", data=_gradient(_WIDTH, _HEIGHT)))

    def set_adding(self, adding: bool) -> None:
        """Arm/disarm draw mode: toggles the left-drag handler and the cursor."""
        self.adding = adding
        self._binding.enabled = adding
        self.canvas.refresh_interaction()
        self.canvas.set_cursor("crosshair" if adding else None)
        if not adding:
            self._discard_preview()

    async def _on_drag_start(self, event: DragEvent, _canvas: ImageCanvas) -> None:
        self._anchor = event.world_position

    async def _on_drag(self, event: DragEvent, _canvas: ImageCanvas) -> bool:
        if self._anchor is None:
            self._anchor = event.world_position
        rect = Rectangle2D.between(self._anchor, event.world_position)
        if self._preview_id is None:
            self._preview_id = self.canvas.handle.add(rect, style=self._style)
        else:
            self.canvas.handle.update_entity(self._preview_id, rect)
        self.canvas.handle.flush()
        return True

    async def _on_drag_end(self, event: DragEvent, _canvas: ImageCanvas) -> None:
        if self._anchor is None:
            return
        rect = Rectangle2D.between(self._anchor, event.world_position)
        self._anchor = None
        self._discard_preview()
        act = ActRectangle2D(
            center=rect.center,
            size=rect.size,
            handle_style=SquarePointStyle(size=1.0, thickness=2.0),
        )
        self.canvas.handle.add(act, style=self._style)
        self.rectangles.append(act)
        self.canvas.handle.flush()

    def _discard_preview(self) -> None:
        if self._preview_id is not None:
            self.canvas.handle.remove(self._preview_id)
            self._preview_id = None


def main() -> None:
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)
    labeler = RectangleLabeler(viz)

    async def on_add(_value: None, _event: ControlEvent) -> None:
        labeler.set_adding(not labeler.adding)

    toolbar = ToolbarView(
        [
            ButtonView(
                "add_rect",
                icon=EIconMaterial.ADD,
                icon_only=True,
                tooltip="Add rectangle (toggle draw mode)",
                on_click=on_add,
            ),
        ],
        border=False,
    )

    layout = SplitView(
        "vertical",
        sizes=[Size.px(40), Size.fr(1)],
        children=[toolbar, labeler.canvas.scene_view()],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
````
