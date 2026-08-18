# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Overlay style dataclasses — labels, annotations, figures, animations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle


@dataclass
class LabelStyle(VizStyle):
    """Visual style for text labels.

    Inherits from ``VizStyle`` to fit into the style hierarchy,
    but labels have their own serialization path since they are not entities.
    """

    font_size: float | None = None
    font_family: str | None = None
    color: str | None = None
    background: str | None = None
    font_weight: str | None = None
    text_transform: str | None = None

    # ── 3D offset in entity's local frame (scaled by entity scale) ──
    offset_local: tuple[float, float, float] | None = None

    # ── 2D screen-space pixel offset (after 3D → 2D projection) ──
    offset_2d: tuple[float, float] | None = None

    # ── Alignment of label text relative to anchor ──
    align: tuple[float, float] | None = None
    # (0.5, 0.5) = centered, (0, 0) = top-left, (1, 1) = bottom-right

    # ── Anchor position along the entity's extent ──
    # Scalar or 2-/3-tuple of fractions parameterizing where on the entity the
    # label anchors.  Interpreted per entity kind:
    #   1D (Line/Direction/PointPair): u = fraction along the extent
    #   2D (Plane/Circle): u, v
    #   3D (Sphere/Inversion): u, v, w
    along: float | tuple[float, float] | tuple[float, float, float] | None = None

    # ── Screen-plane rotation about the final anchor (degrees, clockwise) ──
    rotation: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "LabelStyle"}
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.font_family is not None:
            result["font_family"] = self.font_family
        if self.color is not None:
            result["color"] = self.color
        if self.background is not None:
            result["background"] = self.background
        if self.font_weight is not None:
            result["font_weight"] = self.font_weight
        if self.text_transform is not None:
            result["text_transform"] = self.text_transform
        if self.offset_local is not None:
            result["offset_local"] = list(self.offset_local)
        if self.offset_2d is not None:
            result["offset_2d"] = list(self.offset_2d)
        if self.align is not None:
            result["align"] = list(self.align)
        if self.along is not None:
            result["along"] = (
                list(self.along)
                if isinstance(self.along, (tuple, list))
                else self.along
            )
        if self.rotation is not None:
            result["rotation"] = self.rotation
        return result


@dataclass
class AnimStyle(VizStyle):
    """Playback style for animated HTML exports.

    All fields default to ``None``.  The ``SceneExporter`` stores a
    fully-initialized ``_default_anim_style`` instance; user-supplied
    instances merge their non-``None`` fields on top of the default.
    """

    fps: int | None = None
    loop: bool | None = None
    show_controls: bool | None = None
    compress: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "AnimStyle"}
        if self.fps is not None:
            result["fps"] = self.fps
        if self.loop is not None:
            result["loop"] = self.loop
        if self.show_controls is not None:
            result["show_controls"] = self.show_controls
        if self.compress is not None:
            result["compress"] = self.compress
        return result


@dataclass
class FigureStyle(VizStyle):
    """Visual style for figure exports and live "figure mode".

    Controls the appearance of the 3D canvas container — dimensions,
    background, auto-rotation, and which overlays to show.
    Grid and axes are now explicit scene objects, not figure-style toggles.
    """

    width: int | None = None  # px (default 800)
    height: int | None = None  # px (default 600)
    background: str | None = None  # CSS background (default "transparent")
    auto_rotate: bool | None = None  # auto-rotate the camera (default False)
    show_title: bool | None = None  # show title overlay (default True)
    show_annotation: bool | None = None  # show annotation panel (default True)
    border_radius: str | None = None  # CSS border-radius (default "0")
    responsive: bool | None = None  # fill parent container, resize with window

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "FigureStyle"}
        if self.width is not None:
            result["width"] = self.width
        if self.height is not None:
            result["height"] = self.height
        if self.background is not None:
            result["background"] = self.background
        if self.auto_rotate is not None:
            result["auto_rotate"] = self.auto_rotate
        if self.show_title is not None:
            result["show_title"] = self.show_title
        if self.show_annotation is not None:
            result["show_annotation"] = self.show_annotation
        if self.border_radius is not None:
            result["border_radius"] = self.border_radius
        if self.responsive is not None:
            result["responsive"] = self.responsive
        return result


@dataclass
class AnnotationStyle(VizStyle):
    """Visual style for the markdown annotation panel.

    The annotation panel is a fixed-position overlay at the bottom of the
    viewport that renders markdown text (with LaTeX math via KaTeX).
    """

    width: str | None = None
    max_width: str | None = None
    max_height: str | None = None
    font_size: float | None = None
    font_family: str | None = None
    color: str | None = None
    background: str | None = None
    link_color: str | None = None
    code_background: str | None = None
    padding: str | None = None
    border_radius: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "AnnotationStyle"}
        if self.width is not None:
            result["width"] = self.width
        if self.max_width is not None:
            result["max_width"] = self.max_width
        if self.max_height is not None:
            result["max_height"] = self.max_height
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.font_family is not None:
            result["font_family"] = self.font_family
        if self.color is not None:
            result["color"] = self.color
        if self.background is not None:
            result["background"] = self.background
        if self.link_color is not None:
            result["link_color"] = self.link_color
        if self.code_background is not None:
            result["code_background"] = self.code_background
        if self.padding is not None:
            result["padding"] = self.padding
        if self.border_radius is not None:
            result["border_radius"] = self.border_radius
        return result


@dataclass
class TitleStyle(VizStyle):
    """Visual style for the viewport title overlay.

    The title is a fixed-position heading at the top of the viewport.
    """

    font_size: float | None = None
    color: str | None = None
    background: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "TitleStyle"}
        if self.font_size is not None:
            result["font_size"] = self.font_size
        if self.color is not None:
            result["color"] = self.color
        if self.background is not None:
            result["background"] = self.background
        return result
