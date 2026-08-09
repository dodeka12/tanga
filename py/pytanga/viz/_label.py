# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Label dataclass and anchor-position calculation for the Tanga 3D viewer.

Labels are first-class viz objects that exist independently of entities.
They can be positioned at absolute world coordinates or attached to an
entity via ``parent_id``.
"""

from __future__ import annotations

from dataclasses import dataclass

from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPoint,
    ReflectionPlane,
    Rotor,
    Translator,
)

from ._styles import LabelStyle

EntityLike = (
    Point
    | Direction
    | HPoint
    | PointPair
    | Line
    | Plane
    | Circle
    | Sphere
    | Space
    | ReflectionLine
    | ReflectionPlane
    | ReflectionPoint
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
)


@dataclass
class Label:
    """A text annotation positioned in 3D space.

    Can be added to the scene independently, or created automatically
    by ``Visualizer.add()`` when a ``label`` string is provided.
    """

    text: str
    position: tuple[float, float, float]
    parent_id: str | None = None
    style: LabelStyle | None = None


def get_label_anchor(entity: EntityLike) -> tuple[float, float, float]:
    """Return the natural anchor position for a label — no margin added.

    The anchor is the geometric center of the entity.  The ``offset_local``
    from ``LabelStyle`` is applied on top by ``compute_label_position()``.
    """

    if isinstance(entity, Point):
        return (entity.x, entity.y, entity.z)

    if isinstance(entity, HPoint):
        p = entity.point
        return (p.x, p.y, p.z)

    if isinstance(entity, Direction):
        return (0.0, 0.0, 0.0)

    if isinstance(entity, PointPair):
        pa, pb = entity.point_a, entity.point_b
        return ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2, (pa.z + pb.z) / 2)

    if isinstance(entity, (Line, ReflectionLine)):
        return (entity.origin.x, entity.origin.y, entity.origin.z)

    if isinstance(entity, (Plane, ReflectionPlane)):
        return (entity.point.x, entity.point.y, entity.point.z)

    if isinstance(entity, (Circle, Sphere, Inversion)):
        return (entity.center.x, entity.center.y, entity.center.z)

    if isinstance(entity, Space):
        return (0.0, 0.0, 0.0)

    # Operators — all rendered at origin
    return (0.0, 0.0, 0.0)
