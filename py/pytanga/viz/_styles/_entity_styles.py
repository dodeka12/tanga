# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Visualization style dataclasses for geometric entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle, WireframeDashPattern


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
    """

    color: str | None = None
    opacity: float | None = None
    extent: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None

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
    """

    color: str | None = None
    opacity: float | None = None
    wireframe: bool | None = None
    wireframe_dash: WireframeDashPattern | None = None
    wireframe_color: str | None = None
    wireframe_opacity: float | None = None

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
        line_thickness: Uniform line thickness when not using per-vertex
            thickness.  Due to WebGL limitations, ``THREE.Line`` thickness
            is capped at 1px on most platforms.  Per-vertex thickness
            requires a custom geometry approach (future).
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
