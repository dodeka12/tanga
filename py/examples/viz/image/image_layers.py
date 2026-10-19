# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""image_layers.py — Mix multiple image layers (image, depth, segmentation).

Builds three synthetic layers — an RGB gradient image, a uint16 depth map, and a
uint8 segmentation mask — at different resolutions, uploads them into a single
:class:`~pytanga.viz.ImageCanvas`, and exposes per-layer controls (enable /
opacity / blend mode) in a side panel.  Each control change drives the layer's
uniforms directly, so layers can be toggled or blended live.

Run with:  uv run python py/examples/viz/image/image_layers.py

Keywords: image, ImageCanvas, layers, blend, opacity, segmentation, depth, controls
"""

from __future__ import annotations

from typing import Any

import numpy as np

from pytanga.viz import (
    CheckboxView,
    ControlEvent,
    ControlHandler,
    DropdownView,
    GroupView,
    ImageCanvas,
    ImageData,
    ImageLayerStyle,
    LayerBlendMode,
    SliderView,
    SplitView,
    Visualizer,
)

#: Layer resolutions (depth and segmentation are coarser than the image).
_IMAGE_W, _IMAGE_H = 320, 240
_DEPTH_W, _DEPTH_H = 160, 120
_SEG_W, _SEG_H = 80, 60

#: Dropdown labels → `LayerBlendMode` codes.
_BLEND_OPTIONS = ["normal", "add", "multiply", "screen"]
_BLEND_CODES = {
    "normal": LayerBlendMode.NORMAL,
    "add": LayerBlendMode.ADD,
    "multiply": LayerBlendMode.MULTIPLY,
    "screen": LayerBlendMode.SCREEN,
}


def _gradient(width: int, height: int) -> np.ndarray:
    """A 3-channel RGB gradient of shape (H, W, 3), dtype uint8."""
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.uint8)
    g = (ys / max(height - 1, 1) * 255).astype(np.uint8)
    b = np.full_like(r, 64)
    return np.stack([r, g, b], axis=-1)


def _depth(width: int, height: int) -> np.ndarray:
    """A uint16 depth gradient of shape (H, W)."""
    ys, xs = np.mgrid[0:height, 0:width]
    return ((xs + ys) / max(width + height - 2, 1) * 65535).astype(np.uint16)


def _segmentation(width: int, height: int) -> np.ndarray:
    """Integer regions scaled to visible grey levels as a uint8 mask (H, W)."""
    ys, xs = np.mgrid[0:height, 0:width]
    seg = np.zeros((height, width), dtype=np.uint8)
    top = ys < height // 2
    left = xs < width // 2
    seg[top & left] = 1
    seg[top & ~left] = 2
    seg[~top & left] = 3
    # uint8 textures sample in [0, 1], so scale labels into visible greys.
    return (seg * 80).astype(np.uint8)


def _enable_handler(canvas: ImageCanvas, index: int) -> ControlHandler:
    async def handler(value: Any, _event: ControlEvent) -> None:
        canvas.set_layer_style(index, ImageLayerStyle(enabled=bool(value)))

    return handler


def _opacity_handler(canvas: ImageCanvas, index: int) -> ControlHandler:
    async def handler(value: Any, _event: ControlEvent) -> None:
        canvas.set_layer_style(index, ImageLayerStyle(opacity=float(value)))

    return handler


def _blend_handler(canvas: ImageCanvas, index: int) -> ControlHandler:
    async def handler(value: Any, _event: ControlEvent) -> None:
        canvas.set_layer_style(index, ImageLayerStyle(blend=_BLEND_CODES[str(value)]))

    return handler


def _colormap_handler(canvas: ImageCanvas, index: int) -> ControlHandler:
    async def handler(value: Any, _event: ControlEvent) -> None:
        canvas.set_layer_style(index, ImageLayerStyle(colormap=str(value)))

    return handler


#: Dropdown labels for the per-layer colormap (scalar layers only).
_COLORMAP_OPTIONS = ["gray", "viridis", "turbo"]


def build() -> tuple[Visualizer, ImageCanvas, SplitView]:
    """Build the canvas + per-layer control panel (without showing it)."""
    viz = Visualizer(add_default_axes=False, add_default_grid=False, space_dim=2)

    canvas = ImageCanvas(viz)
    canvas.set_image(ImageData("rgb", data=_gradient(_IMAGE_W, _IMAGE_H)))
    canvas.add_layer(
        ImageData("depth", data=_depth(_DEPTH_W, _DEPTH_H)),
        ImageLayerStyle(enabled=False, opacity=0.5),
    )
    canvas.add_layer(
        ImageData("seg", data=_segmentation(_SEG_W, _SEG_H)),
        ImageLayerStyle(enabled=False, opacity=0.5),
    )

    # The RGB image is the visible base; the depth and segmentation overlays
    # start disabled at half opacity so enabling them blends over the image.
    layer_specs: list[tuple[str, bool, float]] = [
        ("Image", True, 1.0),
        ("Depth", False, 0.5),
        ("Segmentation", False, 0.5),
    ]

    controls: list[Any] = []
    for index, (name, enabled, opacity) in enumerate(layer_specs):
        layer_controls: list[Any] = [
            CheckboxView(
                f"layer{index}_enabled",
                label=f"{name} enabled",
                value=enabled,
                on_change=_enable_handler(canvas, index),
            ),
            SliderView(
                f"layer{index}_opacity",
                label=f"{name} opacity",
                min=0.0,
                max=1.0,
                step=0.05,
                value=opacity,
                on_change=_opacity_handler(canvas, index),
            ),
            DropdownView(
                f"layer{index}_blend",
                label=f"{name} blend",
                options=_BLEND_OPTIONS,
                value="normal",
                on_change=_blend_handler(canvas, index),
            ),
        ]
        if index == 1:  # the uint16 depth layer supports a colormap
            layer_controls.append(
                DropdownView(
                    f"layer{index}_colormap",
                    label=f"{name} colormap",
                    options=_COLORMAP_OPTIONS,
                    value="gray",
                    on_change=_colormap_handler(canvas, index),
                )
            )
        controls.extend(layer_controls)

    layout = SplitView(
        orientation="horizontal",
        children=[GroupView("Layers", controls), canvas.scene_view()],
    )
    return viz, canvas, layout


def main() -> None:
    viz, _canvas, layout = build()
    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
