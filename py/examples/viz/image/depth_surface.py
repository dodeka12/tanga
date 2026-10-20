# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""depth_surface.py — A 2.5D depth surface from phase-shifted 2D sines.

Builds a synthetic depth map from a product of phase-shifted sines of different
frequencies (``sin(2π·f1·u + φ1) · sin(2π·f2·v + φ2)``), a higher-resolution
color image overlaid with high-frequency pixel noise (so the ``image_scale``
downscale is visible), and **selectable segmentation masks** — the whole surface
(default), the positive-valued region, or the negative-valued region — then
renders them as a textured, filterable :class:`~pytanga.viz.DepthImage` surface
in the 3D viewer.

A horizontal :class:`~pytanga.viz.SplitView` shows a control panel on the left
(a :class:`~pytanga.viz.GroupView` of ``DepthImageStyle`` and segmentation
controls) and the 3D surface on the right.  Press **Update view** to re-build the
surface with the selected segmentation, render mode, colormap,
mesh/image/world/depth scale, opacity, and Blinn-Phong ``shininess`` (the
``"plain"`` render mode is lit by the scene lighting, with a white specular
highlight).

Run with:  uv run python py/examples/viz/image/depth_surface.py

Keywords: depth image, surface, segmentation, split view, controls, numpy
"""

from __future__ import annotations

from typing import Any

import numpy as np
from pytanga.viz import (
    ButtonView,
    ControlEvent,
    DepthImage,
    DepthImageData,
    DepthImageStyle,
    DropdownView,
    GroupView,
    SceneView,
    SliderView,
    SplitView,
    Visualizer,
)

#: Depth-map resolution (the mesh grid is decimated independently).
_DEPTH_W, _DEPTH_H = 128, 96
#: Color image resolution (higher than the depth map).
_IMAGE_W, _IMAGE_H = 512, 384


def _signed_surface(width: int, height: int) -> np.ndarray:
    """The raw signed surface value in [-1, 1].

    Uses different frequencies and phase shifts along x and y so the surface is
    visibly 2D rather than a separable 1D ripple.
    """
    ys, xs = np.mgrid[0:height, 0:width]
    u = xs / max(width - 1, 1)
    v = ys / max(height - 1, 1)
    f1, f2 = 3.0, 5.0
    p1, p2 = 0.3, 1.1
    return np.sin(2.0 * np.pi * f1 * u + p1) * np.sin(2.0 * np.pi * f2 * v + p2)


def _surface(width: int, height: int) -> np.ndarray:
    """A normalized [0, 1] depth surface from the signed surface value."""
    return ((_signed_surface(width, height) + 1.0) / 2.0).astype(np.float32)


def _color_image(width: int, height: int) -> np.ndarray:
    """A synthetic RGB gradient overlaid with high-frequency pixel noise.

    The per-pixel noise is visible at full resolution and gets smoothed away as
    ``image_scale`` is reduced (bilinear averaging), making the downscale effect
    easy to see.
    """
    rng = np.random.default_rng(0)
    ys, xs = np.mgrid[0:height, 0:width]
    r = (xs / max(width - 1, 1) * 255).astype(np.float64)
    g = (ys / max(height - 1, 1) * 255).astype(np.float64)
    b = np.full_like(r, 64.0)
    noise = rng.uniform(-100.0, 100.0, size=(height, width, 3))
    rgb = np.stack([r, g, b], axis=-1) + noise
    return np.clip(rgb, 0.0, 255.0).astype(np.uint8)


def _positive_segmentation(width: int, height: int) -> np.ndarray:
    """A uint8 mask labeling the positive-valued surface region (label 1)."""
    return (_signed_surface(width, height) > 0.0).astype(np.uint8)


def _negative_segmentation(width: int, height: int) -> np.ndarray:
    """A uint8 mask labeling the negative-valued surface region (label 1)."""
    return (_signed_surface(width, height) < 0.0).astype(np.uint8)


def main() -> None:
    image = _color_image(_IMAGE_W, _IMAGE_H)
    depth = _surface(_DEPTH_W, _DEPTH_H)
    seg_w, seg_h = _IMAGE_W // 2, _IMAGE_H // 2
    # Segmentation options: (mask, selected segment ids).  A ``None`` mask with
    # an empty selection disables filtering and shows the whole surface.
    segmentations: dict[str, tuple[np.ndarray | None, list[int]]] = {
        "all": (None, []),
        "positive": (_positive_segmentation(seg_w, seg_h), [1]),
        "negative": (_negative_segmentation(seg_w, seg_h), [1]),
    }

    viz = Visualizer(
        reuse_existing=False,
        title="Tanga — 2.5D depth surface",
        add_default_grid=False,
    )

    def _add(
        seg: np.ndarray | None, selected: list[int], style: DepthImageStyle
    ) -> None:
        """Add (or replace) the depth surface with the given segmentation + style."""
        viz.add(
            DepthImage(
                DepthImageData(image=image, depth=depth, segmentation=seg),
                selected_segments=selected,
            ),
            entity_id="depth_surface",
            style=style,
        )

    # Initial surface (whole surface), lit plain mode ready.
    seg, selected = segmentations["all"]
    _add(
        seg,
        selected,
        DepthImageStyle(
            mesh_scale=0.5,
            world_scale=0.01,
            depth_scale=2.0,
            shininess=32.0,
            specular="#ffffff",
        ),
    )

    segmentation = DropdownView(
        "segmentation",
        label="Segmentation",
        options=["all", "positive", "negative"],
        value="all",
    )
    render_mode = DropdownView(
        "render_mode",
        label="Render mode",
        options=["depth", "image", "plain"],
        value="depth",
    )
    colormap = DropdownView(
        "colormap",
        label="Colormap",
        options=["turbo", "viridis", "gray"],
        value="turbo",
    )
    mesh_scale = SliderView(
        "mesh_scale", label="Mesh scale", min=0.05, max=1.0, step=0.05, value=0.5
    )
    image_scale = SliderView(
        "image_scale", label="Image scale", min=0.05, max=1.0, step=0.05, value=1.0
    )
    depth_scale = SliderView(
        "depth_scale", label="Depth scale", min=0.0, max=5.0, step=0.1, value=2.0
    )
    world_scale = SliderView(
        "world_scale",
        label="World scale",
        min=0.002,
        max=0.05,
        step=0.001,
        value=0.01,
    )
    opacity = SliderView(
        "opacity", label="Opacity", min=0.1, max=1.0, step=0.05, value=1.0
    )
    shininess = SliderView(
        "shininess", label="Shininess", min=1.0, max=128.0, step=1.0, value=32.0
    )

    async def _on_apply(_value: Any, _event: ControlEvent) -> None:
        seg, selected = segmentations[segmentation.value]
        _add(
            seg,
            selected,
            DepthImageStyle(
                render_mode=render_mode.value,
                colormap=colormap.value,
                mesh_scale=mesh_scale.value,
                image_scale=image_scale.value,
                depth_scale=depth_scale.value,
                world_scale=world_scale.value,
                opacity=opacity.value,
                shininess=shininess.value,
                specular="#ffffff",
            ),
        )
        viz.flush()

    layout = SplitView(
        orientation="horizontal",
        children=[
            GroupView(
                "Depth image",
                [
                    segmentation,
                    render_mode,
                    colormap,
                    mesh_scale,
                    image_scale,
                    depth_scale,
                    world_scale,
                    opacity,
                    shininess,
                    ButtonView("apply", label="Update view", on_click=_on_apply),
                ],
            ),
            SceneView(""),
        ],
    )

    viz.show(layout=layout)
    viz.wait()


if __name__ == "__main__":
    main()
