# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Arc visualization-only entity data class."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from ._util import _compute_start_direction
from .direction import Direction
from .point import Point

_FULL_TURN = 2.0 * math.pi


@dataclass(frozen=True)
class Arc:
    """An arcing cylinder (partial torus) in 3D space, purely for visualization.

    Unlike the other entities in this package, an :class:`Arc` has **no**
    multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    The arc lies in the plane perpendicular to ``axis``, centered on ``origin``.
    Its centerline is a circle of radius ``radius``; the swept angular extent is
    ``angle`` (in **radians**, default ``2π`` = a full torus).  The cylinder
    representing the arc has cross-section radius ``tube_radius``.

    ``start_direction`` is the unit vector from ``origin`` to the arc's start
    point.  When omitted it is computed automatically (deterministic) so the
    frontend always receives a valid start direction.

    Parameters
    ----------
    origin:
        Center of the arc circle.
    axis:
        Rotation axis; the arc lies in the plane perpendicular to it.
    radius:
        Radius of the arc centerline (distance from ``origin``).
    tube_radius:
        Radius of the cylinder cross-section representing the arc.
    angle:
        Swept angular extent in radians (default ``2π`` — a full torus).
    start_direction:
        Optional unit direction from ``origin`` to the arc start.  Computed
        automatically (perpendicular to ``axis``) when ``None``.
    show_arrow:
        When ``True``, draw a cone arrow tip at the arc's end.
    arrow_length:
        Length of the arrow cone.  Defaults to ``3 * tube_radius`` when
        ``show_arrow`` is ``True``.
    arrow_radius:
        Radius of the arrow cone base.  Defaults to ``2 * tube_radius`` when
        ``show_arrow`` is ``True``.
    """

    origin: Point
    axis: Direction
    radius: float
    tube_radius: float
    angle: float = _FULL_TURN
    start_direction: Direction | None = None
    show_arrow: bool = False
    arrow_length: float | None = None
    arrow_radius: float | None = None

    def __init__(
        self,
        origin=None,
        axis=None,
        radius=None,
        tube_radius=None,
        angle=None,
        start_direction=None,
        show_arrow=False,
        arrow_length=None,
        arrow_radius=None,
    ):
        origin = Point(0.0, 0.0, 0.0) if origin is None else to_point(origin)
        axis = Direction(0.0, 0.0, 1.0) if axis is None else to_direction(axis)
        radius = 1.0 if radius is None else to_float(radius)
        tube_radius = 0.05 if tube_radius is None else to_float(tube_radius)
        angle = _FULL_TURN if angle is None else to_float(angle)

        if start_direction is None:
            start_direction = _compute_start_direction(axis)
        else:
            start_direction = to_direction(start_direction).normalized()

        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "tube_radius", tube_radius)
        object.__setattr__(self, "angle", angle)
        object.__setattr__(self, "start_direction", start_direction)
        object.__setattr__(self, "show_arrow", bool(show_arrow))
        object.__setattr__(
            self,
            "arrow_length",
            None if arrow_length is None else to_float(arrow_length),
        )
        object.__setattr__(
            self,
            "arrow_radius",
            None if arrow_radius is None else to_float(arrow_radius),
        )

    def __repr__(self) -> str:
        return (
            f"Arc(org={self.origin}, axis={self.axis}, r={self.radius:.2f}, "
            f"tube={self.tube_radius:.2f}, angle={self.angle:.3f})"
        )
