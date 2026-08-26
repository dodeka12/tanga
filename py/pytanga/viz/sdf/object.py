# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""SdfObject element + geometry-entity → SdfNode conversion.

An :class:`SdfObject` wraps a geometry entity (``Sphere``, ``Cylinder``, ``Line``,
``Circle``, ``Plane``, ``Point``, ``Disk``, ``PartialDisk``, ``Box``,
``Ellipsoid``, ``Ellipse``, ``RegularPolygon``) plus an optional id and a
per-entity SDF style, and lowers to a low-level
:class:`~pytanga.viz.sdf.primitives.SdfNode` tree at construction time (never
deep in the serializer).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from pytanga.geometry.entities import (
    Box,
    Circle,
    Cylinder,
    Disk,
    Ellipse,
    Ellipsoid,
    Line,
    PartialDisk,
    Plane,
    Point,
    RegularPolygon,
    Sphere,
)

from ._compose import ECompose, SdfElement
from .primitives import (
    SdfNode,
    _as_rotation,
    _basis_rotation,
    _normalize,
    _rotate_about,
    _rotation_align,
    box,
    capped_cylinder,
    combine,
    ellipsoid,
    partial_disk,
    regular_polygon,
    sphere,
    torus,
)
from .._styles._sdf_style import SDF_STYLE_BY_KIND, SdfStyle

__all__ = ["SdfObject"]

_DEFAULT_LINE_LENGTH = 20.0
_DEFAULT_PLANE_EXTENT = 10.0


@dataclass(init=False)
class SdfObject(SdfElement):
    """A single SDF drawable: a geometry entity + optional id + per-entity style.

    ``entity`` may be a geometry entity (``Sphere``, ``Cylinder``, ``Line``,
    ``Circle``, ``Plane``, ``Point``) or an already-SDF drawable
    (``SdfNode``/``Combine``/``Composed``/``SdfGroup``).
    """

    entity: Any
    id: str | None
    style: SdfStyle | None

    def __init__(
        self,
        entity: Any,
        id: str | None = None,
        style: SdfStyle | None = None,
        *,
        combine: ECompose = ECompose.UNION,
    ) -> None:
        object.__setattr__(self, "entity", entity)
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "style", style)
        object.__setattr__(self, "combine", combine)

    def to_sdf_node(self) -> SdfNode:
        node = _entity_to_sdf(self.entity, self.style)
        if self.id is not None:
            node.id = self.id
        return node


def _entity_to_sdf(entity: Any, style: SdfStyle | None = None) -> SdfNode:
    """Convert a geometry entity (or SDF descriptor) to a low-level ``SdfNode``.

    Applies the style's shape params (``thickness``/``tube_radius``/``size``).
    ``SdfNode`` inputs pass through; ``SdfElement`` inputs lower recursively.
    """
    if isinstance(entity, SdfNode):
        return entity
    if isinstance(entity, SdfElement):
        return entity.to_sdf_node()

    if isinstance(entity, Sphere):
        return sphere(entity.radius, position=_xyz(entity.center))
    if isinstance(entity, Cylinder):
        return _cylinder_node(entity)
    if isinstance(entity, Line):
        return _line_node(entity, style)
    if isinstance(entity, Circle):
        return _circle_node(entity, style)
    if isinstance(entity, Plane):
        return _plane_node(entity)
    if isinstance(entity, Disk):
        return _disk_node(entity, style)
    if isinstance(entity, PartialDisk):
        return _partial_disk_node(entity, style)
    if isinstance(entity, Box):
        return _box_node(entity)
    if isinstance(entity, Ellipsoid):
        return _ellipsoid_node(entity)
    if isinstance(entity, Ellipse):
        return _ellipse_node(entity, style)
    if isinstance(entity, RegularPolygon):
        return _regular_polygon_node(entity, style)
    if isinstance(entity, Point):
        size = _style_attr(style, "Point", "size", 0.08)
        return sphere(size, position=(entity.x, entity.y, entity.z))

    raise TypeError(f"SDF object model does not support {type(entity).__name__!r}")


def _xyz(p: Any) -> tuple[float, float, float]:
    return (float(p.x), float(p.y), float(p.z))


def _style_for(style: SdfStyle | None, kind: str) -> SdfStyle | None:
    if style is not None:
        return style
    cls = SDF_STYLE_BY_KIND.get(kind)
    return cls() if cls is not None else None


def _style_attr(style: SdfStyle | None, kind: str, attr: str, default: float) -> float:
    resolved = _style_for(style, kind)
    return float(getattr(resolved, attr, default)) if resolved is not None else float(default)


def _cylinder_node(entity: Cylinder) -> SdfNode:
    axis = _normalize(_xyz(entity.axis))
    half = float(entity.length) / 2.0
    offset = half * (0.5 - float(entity.align_center))
    midpoint = (
        entity.origin.x + axis[0] * offset,
        entity.origin.y + axis[1] * offset,
        entity.origin.z + axis[2] * offset,
    )
    rotation = _rotation_align((0.0, 1.0, 0.0), axis)
    return capped_cylinder(half, float(entity.radius), position=midpoint, rotation=rotation)


def _line_node(entity: Line, style: SdfStyle | None) -> SdfNode:
    thickness = _style_attr(style, "Line", "thickness", 1.0)
    direction = _normalize(_xyz(entity.direction))
    if direction == (0.0, 0.0, 0.0):
        direction = (0.0, 0.0, 1.0)
    length = float(entity.length) if entity.length is not None else _DEFAULT_LINE_LENGTH
    half = length / 2.0
    midpoint = (
        entity.origin.x + direction[0] * half,
        entity.origin.y + direction[1] * half,
        entity.origin.z + direction[2] * half,
    )
    rotation = _rotation_align((0.0, 1.0, 0.0), direction)
    node = capped_cylinder(half, thickness, position=midpoint, rotation=rotation)
    if entity.length is None:
        bound = box((half, half, half), position=midpoint, rotation=rotation)
        return combine("intersect", node, bound)
    return node


def _circle_node(entity: Circle, style: SdfStyle | None) -> SdfNode:
    tube = _style_attr(style, "Circle", "tube_radius", 0.03)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    rotation = _rotation_align((0.0, 1.0, 0.0), normal)
    return torus(float(entity.radius), tube, position=_xyz(entity.center), rotation=rotation)


def _plane_node(entity: Plane) -> SdfNode:
    if entity.span_u is not None and entity.span_v is not None:
        hu = float(entity.span_u.mag()) / 2.0
        hv = float(entity.span_v.mag()) / 2.0
    else:
        extent = float(entity.extent) if entity.extent is not None else _DEFAULT_PLANE_EXTENT
        hu = extent
        hv = extent
    eps = max(0.02, min(hu, hv) * 0.01)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    rotation = _rotation_align((0.0, 0.0, 1.0), normal)
    return box((hu, hv, eps), position=_xyz(entity.point), rotation=rotation)


def _disk_node(entity: Disk, style: SdfStyle | None) -> SdfNode:
    thickness = _style_attr(style, "Disk", "thickness", 0.02)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    rotation = _rotation_align((0.0, 1.0, 0.0), normal)
    return capped_cylinder(
        thickness / 2.0,
        float(entity.radius),
        position=_xyz(entity.center),
        rotation=rotation,
    )


def _partial_disk_node(entity: PartialDisk, style: SdfStyle | None) -> SdfNode:
    thickness = _style_attr(style, "PartialDisk", "thickness", 0.02)
    half = thickness / 2.0
    radius = float(entity.radius)
    angle = float(entity.angle)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    center = _xyz(entity.center)

    # A full disk (angle >= 2π) is a plain capped cylinder.
    if angle >= 2.0 * math.pi - 1e-9:
        return capped_cylinder(half, radius, position=center, rotation=_rotation_align((0.0, 1.0, 0.0), normal))

    start = _xyz(entity.start_direction)
    bisector = _rotate_about(start, normal, angle / 2.0)
    rotation = _basis_rotation(normal, bisector)
    return partial_disk(radius, angle, half_height=half, position=center, rotation=rotation)


def _box_node(entity: Box) -> SdfNode:
    rotation = _as_rotation(entity.rotation) if entity.rotation is not None else None
    half_extents = (entity.size[0] / 2.0, entity.size[1] / 2.0, entity.size[2] / 2.0)
    return box(half_extents, position=_xyz(entity.center), rotation=rotation)


def _ellipsoid_node(entity: Ellipsoid) -> SdfNode:
    rotation = _as_rotation(entity.rotation) if entity.rotation is not None else None
    return ellipsoid(entity.radii, position=_xyz(entity.center), rotation=rotation)


def _ellipse_node(entity: Ellipse, style: SdfStyle | None) -> SdfNode:
    thickness = _style_attr(style, "Ellipse", "thickness", 0.02)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    rotation = _rotation_align((0.0, 0.0, 1.0), normal)
    return ellipsoid(
        (entity.radius_u, entity.radius_v, thickness / 2.0),
        position=_xyz(entity.center),
        rotation=rotation,
    )


def _regular_polygon_node(entity: RegularPolygon, style: SdfStyle | None) -> SdfNode:
    thickness = _style_attr(style, "RegularPolygon", "thickness", 0.02)
    normal = _normalize(_xyz(entity.normal))
    if normal == (0.0, 0.0, 0.0):
        normal = (0.0, 0.0, 1.0)
    # The primitive's first vertex sits on local +Z.  The mesh renderer first
    # aligns +Y → normal (shortest arc, Q1) and then rotates by `angle` about
    # the normal, so the vertex lands at Q1(sin(angle), 0, cos(angle)).  Reproduce
    # that world direction (never `rotate(+Z, normal, angle)`, which collapses
    # onto `normal` when `normal` is ±Z).
    q1 = _rotation_align((0.0, 1.0, 0.0), normal)
    local_vertex = (math.sin(entity.angle), 0.0, math.cos(entity.angle))
    vertex_dir = (
        _rotate_about(local_vertex, q1[0], q1[1]) if q1 is not None else local_vertex
    )
    rotation = _basis_rotation(normal, vertex_dir)
    return regular_polygon(
        float(entity.radius),
        int(entity.sides),
        half_height=thickness / 2.0,
        position=_xyz(entity.center),
        rotation=rotation,
    )
