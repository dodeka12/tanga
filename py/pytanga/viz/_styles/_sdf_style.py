# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SDF rendering style marker for the standard viewer.

:class:`SdfStyle` is a *marker* style: applying it to an entity opts that
entity into smooth ray-marched signed-distance-field rendering in the standard
viewer (emitted as ``kind:"sdf"`` on the wire) instead of the normal
vertex/mesh pipeline.

``color``/``opacity`` still resolve through the normal priority chain
(per-entity props > style > canonical > builtin); the remaining fields are
SDF-specific knobs with concrete defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._base import VizStyle


@dataclass
class SdfStyle(VizStyle):
    """Opt an entity into ray-marched SDF rendering in the standard viewer.

    Attributes:
        color: Optional override color (CSS hex string or tuple).  ``None``
            uses the normal priority chain.
        opacity: Optional override opacity (0..1).  ``None`` uses the normal
            priority chain.
        soft_shadows: Enable soft self-shadowing in the ray-marcher.
        max_steps: Ray-march step budget.
        bound_padding: Inflate the proxy AABB by this absolute amount so the
            marching volume always covers the surface (any over-estimate is
            safe; under-estimates clip the surface).
        antialias: Enable the analytic ~1px silhouette edge fade in the
            ray-marcher (default on; disable for a hard, exact silhouette).
    """

    color: str | None = None
    opacity: float | None = None
    soft_shadows: bool = True
    max_steps: int = 256
    bound_padding: float = 0.05
    antialias: bool = True

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "style_type": type(self).__name__,
            "soft_shadows": self.soft_shadows,
            "max_steps": self.max_steps,
            "bound_padding": self.bound_padding,
            "antialias": self.antialias,
        }
        if self.color is not None:
            result["color"] = self.color
        if self.opacity is not None:
            result["opacity"] = self.opacity
        return result


@dataclass
class SdfSphereStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Sphere`.

    A sphere has no entity-specific SDF knobs beyond the common base.
    """


@dataclass
class SdfLineStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Line`.

    Attributes:
        thickness: Radius of the SDF line's capped-cylinder body (the SDF
            equivalent of the mesh ``LineStyle.thickness``).
    """

    thickness: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["thickness"] = self.thickness
        return result


@dataclass
class SdfCircleStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Circle`.

    Attributes:
        tube_radius: Radius of the torus tube used for the circle's SDF.
    """

    tube_radius: float = 0.03

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["tube_radius"] = self.tube_radius
        return result


@dataclass
class SdfPointStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Point`.

    Attributes:
        size: Radius of the SDF point's sphere.
    """

    size: float = 0.08

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["size"] = self.size
        return result


@dataclass
class SdfCylinderStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Cylinder` (no extra knobs)."""


@dataclass
class SdfPlaneStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Plane` (no extra knobs)."""


@dataclass
class SdfDiskStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Disk`.

    Attributes:
        thickness: Slab thickness of the SDF disk (a thin capped cylinder).
    """

    thickness: float = 0.02

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["thickness"] = self.thickness
        return result


@dataclass
class SdfPartialDiskStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.PartialDisk`.

    Attributes:
        thickness: Slab thickness of the SDF partial disk.
    """

    thickness: float = 0.02

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["thickness"] = self.thickness
        return result


@dataclass
class SdfBoxStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Box` (no extra knobs)."""


@dataclass
class SdfEllipsoidStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Ellipsoid` (no extra knobs)."""


@dataclass
class SdfEllipseStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.Ellipse`.

    Attributes:
        thickness: Slab thickness of the SDF ellipse (a thin ellipsoid).
    """

    thickness: float = 0.02

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["thickness"] = self.thickness
        return result


@dataclass
class SdfRegularPolygonStyle(SdfStyle):
    """SDF style for :class:`~pytanga.geometry.RegularPolygon`.

    Attributes:
        thickness: Slab thickness of the SDF regular polygon.
    """

    thickness: float = 0.02

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["thickness"] = self.thickness
        return result


#: Default per-entity SDF style class for a geometry entity kind. Used by
#: ``_entity_to_sdf`` (Phase 3) to pick a sensible style when a raw entity is
#: wrapped without an explicit style.
SDF_STYLE_BY_KIND: dict[str, type[SdfStyle]] = {
    "Sphere": SdfSphereStyle,
    "Line": SdfLineStyle,
    "Circle": SdfCircleStyle,
    "Point": SdfPointStyle,
    "Cylinder": SdfCylinderStyle,
    "Plane": SdfPlaneStyle,
    "Disk": SdfDiskStyle,
    "PartialDisk": SdfPartialDiskStyle,
    "Box": SdfBoxStyle,
    "Ellipsoid": SdfEllipsoidStyle,
    "Ellipse": SdfEllipseStyle,
    "RegularPolygon": SdfRegularPolygonStyle,
}

