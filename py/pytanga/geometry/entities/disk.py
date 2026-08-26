# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Disk and partial-disk visualization-only entity data classes."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from ._util import _compute_start_direction
from .direction import Direction
from .point import Point

_FULL_TURN = 2.0 * math.pi


@dataclass(frozen=True)
class Disk:
    """A filled disk (a flat, circular slab) in 3D space, purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`Disk` has **no**
    multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    The disk lies in the plane perpendicular to ``normal``, centered on
    ``center``.  ``normal`` defaults to ``Direction(0, 0, 1)`` (the positive
    z-axis), the natural choice for 2D use cases where the disk lies in the
    xy-plane.  The slab thickness is a style knob (``DiskStyle.thickness``), not
    a geometric field.

    Parameters
    ----------
    center:
        Center of the disk (default ``(0, 0, 0)``).
    radius:
        Radius of the disk (default ``1.0``).
    normal:
        Normal direction of the disk plane (default ``+z``).
    """

    center: Point
    radius: float
    normal: Direction | None = None

    def __init__(self, center=None, radius=None, normal=None):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        radius = 1.0 if radius is None else to_float(radius)
        normal = (
            Direction(0.0, 0.0, 1.0) if normal is None else to_direction(normal)
        )

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "normal", normal)

    def __repr__(self) -> str:
        return f"Disk(c={self.center}, r={self.radius:.2f}, n={self.normal})"


@dataclass(frozen=True)
class PartialDisk:
    """A filled circular sector (a flat, pie-shaped slab), purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`PartialDisk` has
    **no** multivector representation — it exists only as a rendering hint.

    The sector lies in the plane perpendicular to ``normal``, centered on
    ``center``.  Its swept angular extent is ``angle`` (in **radians**, default
    ``2π`` = a full disk), starting at ``start_direction``.  The slab thickness
    is a style knob (``PartialDiskStyle.thickness``).

    Parameters
    ----------
    center:
        Center of the sector (default ``(0, 0, 0)``).
    radius:
        Radius of the sector (default ``1.0``).
    angle:
        Swept angular extent in radians (default ``2π`` — a full disk).
    start_direction:
        Optional unit direction from ``center`` to the sector's start edge.
        Computed automatically (perpendicular to ``normal``) when ``None``.
    normal:
        Normal direction of the sector plane (default ``+z``).
    """

    center: Point
    radius: float
    angle: float = _FULL_TURN
    start_direction: Direction | None = None
    normal: Direction | None = None

    def __init__(
        self,
        center=None,
        radius=None,
        angle=None,
        start_direction=None,
        normal=None,
    ):
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        radius = 1.0 if radius is None else to_float(radius)
        angle = _FULL_TURN if angle is None else to_float(angle)
        normal = (
            Direction(0.0, 0.0, 1.0) if normal is None else to_direction(normal)
        )

        if start_direction is None:
            start_direction = _compute_start_direction(normal)
        else:
            start_direction = to_direction(start_direction).normalized()

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "angle", angle)
        object.__setattr__(self, "start_direction", start_direction)
        object.__setattr__(self, "normal", normal)

    def __repr__(self) -> str:
        return (
            f"PartialDisk(c={self.center}, r={self.radius:.2f}, "
            f"angle={self.angle:.3f}, n={self.normal})"
        )
