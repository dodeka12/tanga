# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Regular polygon visualization-only entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class RegularPolygon:
    """A filled regular polygon (a flat slab), purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`RegularPolygon` has
    **no** multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    The polygon lies in the plane perpendicular to ``normal``, centered on
    ``center``.  ``normal`` defaults to ``Direction(0, 0, 1)`` (the positive
    z-axis), the natural choice for 2D use cases where the polygon lies in the
    xy-plane.  The slab thickness is a style knob
    (``RegularPolygonStyle.thickness``), not a geometric field.

    Parameters
    ----------
    center:
        Center of the polygon (default ``(0, 0, 0)``).
    radius:
        Circumradius — distance from ``center`` to each vertex (default ``1.0``).
    sides:
        Number of sides, at least ``3`` (default ``6``).
    normal:
        Normal direction of the polygon plane (default ``+z``).
    angle:
        In-plane rotation of the polygon in radians (default ``0.0``).
    """

    center: Point
    radius: float
    sides: int
    normal: Direction | None = None
    angle: float = 0.0

    def __init__(self, center=None, radius=None, sides=None, normal=None, angle=None):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        radius = 1.0 if radius is None else to_float(radius)
        sides = 6 if sides is None else int(sides)
        if sides < 3:
            raise ValueError(f"RegularPolygon requires sides >= 3, got {sides}")
        normal = (
            Direction(0.0, 0.0, 1.0) if normal is None else to_direction(normal)
        )
        angle = 0.0 if angle is None else to_float(angle)

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "sides", sides)
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "angle", angle)

    def __repr__(self) -> str:
        return (
            f"RegularPolygon(c={self.center}, r={self.radius:.2f}, "
            f"sides={self.sides}, n={self.normal}, angle={self.angle:.3f})"
        )


def regular_polygon(
    sides: int,
    radius: float = 1.0,
    center=None,
    normal=None,
    angle: float = 0.0,
) -> RegularPolygon:
    """Create a :class:`RegularPolygon` entity (e.g. a hexagon with ``sides=6``).

    This is an ergonomic factory over :class:`RegularPolygon`:

    ```python
    hexagon = regular_polygon(6, radius=1.0, center=Point(0, 0, 0))
    ```
    """
    return RegularPolygon(
        center=center,
        radius=radius,
        sides=sides,
        normal=normal,
        angle=angle,
    )
