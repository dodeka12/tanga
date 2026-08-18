# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Visualization style dataclasses for geometric entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import VizStyle, WireframeDashPattern
from ._overlay_styles import LabelStyle
from ._tex_label_style import TextureLabelStyle


@dataclass
class PointStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Point`.

    Serves as the base class for future extended point styles
    (e.g. ``CrossHairPointStyle``).
    """

    color: str | None = None
    opacity: float | None = None
    size: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PointStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.size is not None:
            result["size"] = self.size
        return result


@dataclass
class DirectionStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Direction`."""

    color: str | None = None
    opacity: float | None = None
    length: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "DirectionStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.length is not None:
            result["length"] = self.length
        return result


@dataclass
class HPointStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.HPoint`."""

    color: str | None = None
    opacity: float | None = None
    size: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "HPointStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.size is not None:
            result["size"] = self.size
        return result


@dataclass
class PointPairStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.PointPair`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over each
            point sphere.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
    """

    color: str | None = None
    opacity: float | None = None
    point_size: float | None = None
    line_thickness: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PointPairStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.point_size is not None:
            result["point_size"] = self.point_size
        if self.line_thickness is not None:
            result["line_thickness"] = self.line_thickness
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        return result


@dataclass
class LineStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Line`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            cylinder surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
    """

    color: str | None = None
    opacity: float | None = None
    length: float | None = None
    thickness: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "LineStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.length is not None:
            result["length"] = self.length
        if self.thickness is not None:
            result["thickness"] = self.thickness
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        return result


@dataclass
class CylinderLineStyle(LineStyle):
    """LineStyle variant that renders :class:`~pytanga.geometry.Line` as a
    solid 3D cylinder instead of a screen-space fat line.

    ``thickness`` is interpreted in **world units** (the cylinder radius),
    unlike the base :class:`LineStyle`, whose ``thickness`` is a screen-space
    pixel width.
    """

    thickness: float = 0.03

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["style_type"] = "CylinderLineStyle"
        return result


@dataclass
class PlaneStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Plane`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            plane surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
        texture_label: Optional :class:`TextureLabelStyle` for a text
            or formula label rendered onto the plane surface.  When
            ``None``, no texture is applied.  Use ``align`` to control
            layout (``"stretch"``, ``"fit"``, ``"repeat"``).
    """

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None
    texture_label: TextureLabelStyle | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PlaneStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.extent is not None:
            result["extent"] = self.extent
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        if self.texture_label is not None:
            result["texture_label"] = self.texture_label.to_dict()
        return result


@dataclass
class CircleStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Circle`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            torus surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
    """

    color: str | None = None
    opacity: float | None = None
    tube_radius: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "CircleStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.tube_radius is not None:
            result["tube_radius"] = self.tube_radius
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        return result


@dataclass
class SphereStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Sphere`.

    Attributes:
        wireframe: When ``True``, a wireframe cage is drawn over the
            sphere surface.
        wireframe_dash: Optional :class:`WireframeDashPattern` for dashed
            wireframe lines.  ``None`` defaults to solid lines.
        wireframe_color: Optional override color for wireframe lines.
            ``None`` uses the entity's main color.
        wireframe_opacity: Optional opacity for wireframe lines (0..1).
            ``None`` defaults to fully opaque.
        texture_label: Optional :class:`TextureLabelStyle` for a text
            or formula label rendered onto the sphere surface.  When
            ``None``, no texture is applied.  Use ``offset_v=0.25`` to
            center the label at the equator.
    """

    color: str | None = None
    opacity: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None
    texture_label: TextureLabelStyle | None = None
    double_sided: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "SphereStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.wireframe is not None:
            result["wireframe"] = self.wireframe
        if self.wireframe_dash is not None:
            result["wireframe_dash"] = self.wireframe_dash.to_dict()
        if self.wireframe_color is not None:
            result["wireframe_color"] = self.wireframe_color
        if self.wireframe_opacity is not None:
            result["wireframe_opacity"] = self.wireframe_opacity
        if self.texture_label is not None:
            result["texture_label"] = self.texture_label.to_dict()
        if self.double_sided is not None:
            result["double_sided"] = self.double_sided
        return result


@dataclass
class SpaceStyle(VizStyle):
    """Visual style for :class:`~pytanga.geometry.Space`."""

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "SpaceStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.extent is not None:
            result["extent"] = self.extent
        return result


@dataclass
class PointPathStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz._point_path.PointPath`.

    Attributes:
        color: Fallback uniform color when per-point colors are ``None``.
        opacity: Global opacity (0..1).
        line_thickness: Uniform line width in screen-space pixels (three.js
            ``Line2`` fat lines).  Per-vertex thickness still requires a
            custom geometry approach (future).
    """

    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "PointPathStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.line_thickness is not None:
            result["line_thickness"] = self.line_thickness
        return result


@dataclass
class GridStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz.Grid`.

    Attributes:
        color: Grid line color.
        opacity: Grid line opacity (0..1).
        line_thickness: Grid line width in screen-space pixels.
    """

    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "GridStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.line_thickness is not None:
            result["line_thickness"] = self.line_thickness
        return result


@dataclass
class AxisStyle(VizStyle):
    """Visual style for a single coordinate axis.

    Attributes:
        color: Axis line and value/name label color.
        opacity: Axis line opacity (0..1).
        line_thickness: Axis line width in screen-space pixels.
        label_style: Optional :class:`LabelStyle` controlling the axis
            *name* label (font size, color, alignment, ``along`` anchor, 2D
            pixel offset, 3D ``offset_local``, and rotation).
        value_style: Optional :class:`LabelStyle` controlling the numeric
            value labels at each major interval (font size, color, alignment,
            2D pixel offset, 3D ``offset_local``, and rotation).
    """

    color: str | None = None
    opacity: float | None = None
    line_thickness: float | None = None
    label_style: LabelStyle | None = None
    value_style: LabelStyle | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "AxisStyle"}
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        if self.line_thickness is not None:
            result["line_thickness"] = self.line_thickness
        if self.label_style is not None:
            result["label_style"] = self.label_style.to_dict()
        if self.value_style is not None:
            result["value_style"] = self.value_style.to_dict()
        return result


@dataclass
class Axes2DStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz.Axes2D`.

    Holds one :class:`AxisStyle` for each of the two axes directions.
    The same style is used for the positive and negative half of an axis.

    Attributes:
        u: :class:`AxisStyle` for the ``dir_u`` axis.
        v: :class:`AxisStyle` for the ``dir_v`` axis.
    """

    u: AxisStyle = field(default_factory=AxisStyle)
    v: AxisStyle = field(default_factory=AxisStyle)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "Axes2DStyle"}
        if self.u is not None:
            result["u"] = self.u.to_dict()
        if self.v is not None:
            result["v"] = self.v.to_dict()
        return result


@dataclass
class Axes3DStyle(VizStyle):
    """Visual style for :class:`~pytanga.viz.Axes3D`.

    Holds one :class:`AxisStyle` for each of the three axes directions.
    The same style is used for the positive and negative half of an axis.

    Attributes:
        u: :class:`AxisStyle` for the ``dir_u`` axis.
        v: :class:`AxisStyle` for the ``dir_v`` axis.
        w: :class:`AxisStyle` for the ``dir_w`` axis.
    """

    u: AxisStyle = field(default_factory=AxisStyle)
    v: AxisStyle = field(default_factory=AxisStyle)
    w: AxisStyle = field(default_factory=AxisStyle)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"style_type": "Axes3DStyle"}
        if self.u is not None:
            result["u"] = self.u.to_dict()
        if self.v is not None:
            result["v"] = self.v.to_dict()
        if self.w is not None:
            result["w"] = self.w.to_dict()
        return result
