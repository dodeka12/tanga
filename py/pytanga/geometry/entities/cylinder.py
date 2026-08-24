# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cylinder visualization-only entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Cylinder:
    """A solid cylinder in 3D space, purely for visualization.

    Unlike the other entities in this package, a :class:`Cylinder` has **no**
    multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer.

    ``origin`` is positioned along the cylinder's main axis according to
    ``align_center``: at ``0`` (the default) the cylinder starts at ``origin``
    and extends ``length`` in the direction of ``axis``; at ``0.5`` the
    cylinder is centered on ``origin``.  Intermediate values interpolate the
    anchor point along the length.

    Parameters
    ----------
    origin:
        Anchor point of the cylinder (see ``align_center``).
    axis:
        Direction of the cylinder's main axis (normalized when rendered).
    length:
        Total length of the cylinder along ``axis``.
    radius:
        Radius of the cylinder cross-section.
    align_center:
        Fraction of ``length`` where ``origin`` sits: ``0`` = start/base point,
        ``0.5`` = center (default ``0.0``).
    """

    origin: Point
    axis: Direction
    length: float
    radius: float
    align_center: float = 0.0

    def __init__(
        self, origin=None, axis=None, length=None, radius=None, align_center=None
    ):
        origin = Point(0.0, 0.0, 0.0) if origin is None else to_point(origin)
        axis = Direction(0.0, 0.0, 1.0) if axis is None else to_direction(axis)
        length = 1.0 if length is None else to_float(length)
        radius = 0.1 if radius is None else to_float(radius)
        align_center = 0.0 if align_center is None else to_float(align_center)

        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "length", length)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "align_center", align_center)

    def __repr__(self) -> str:
        return (
            f"Cylinder(org={self.origin}, axis={self.axis}, "
            f"len={self.length:.2f}, r={self.radius:.2f}, "
            f"align={self.align_center:.2f})"
        )
