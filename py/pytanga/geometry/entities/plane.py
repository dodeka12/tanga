# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Plane entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from ._util import _convert_mv
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Plane:
    """An infinite plane in 3D space.

    The optional *span_u* and *span_v* fields define a parallelogram
    shape for rendering.  When both are provided, the visualizer draws
    a quad with those exact edge vectors instead of a square of size
    ``extent``.  When ``None``, *extent* controls the half-side of a
    square (default 10.0).

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_plane`).
    """

    point: Point
    normal: Direction
    span_u: Direction | None = None
    span_v: Direction | None = None
    extent: float | None = None

    def __init__(self, point=None, normal=None, span_u=None, span_v=None, extent=None):
        try:
            point = to_point(point)
        except TypeError:
            plane = _convert_mv("plane", point)
            object.__setattr__(self, "point", plane.point)
            object.__setattr__(self, "normal", plane.normal)
            object.__setattr__(self, "span_u", plane.span_u)
            object.__setattr__(self, "span_v", plane.span_v)
            object.__setattr__(self, "extent", plane.extent)
            return

        object.__setattr__(self, "point", point)
        object.__setattr__(self, "normal", to_direction(normal))
        object.__setattr__(
            self, "span_u", None if span_u is None else to_direction(span_u)
        )
        object.__setattr__(
            self, "span_v", None if span_v is None else to_direction(span_v)
        )
        object.__setattr__(
            self, "extent", None if extent is None else to_float(extent)
        )

    def __repr__(self) -> str:
        return f"Plane(pt={self.point}, n={self.normal})"

    @classmethod
    def from_corner_and_span(cls, corner: Point, u: Direction, v: Direction) -> "Plane":
        """Construct a plane from a corner point and two full edge vectors.

        The center is ``corner + u/2 + v/2``.  Normal is ``u × v``
        (normalized).  Does **not** set *extent* (the spans define
        the shape).
        """
        center = corner + u / 2.0 + v / 2.0
        normal = u.cross(v).normalized()
        return cls(point=center, normal=normal, span_u=u, span_v=v)

    @classmethod
    def from_center_and_half_span(
        cls, center: Point, u: Direction, v: Direction
    ) -> "Plane":
        """Construct a plane from a center and two half-span vectors.

        The edge vectors are ``2·u`` and ``2·v``.  Normal is ``u × v``
        (normalized).
        """
        normal = u.cross(v).normalized()
        return cls(
            point=center,
            normal=normal,
            span_u=2.0 * u,
            span_v=2.0 * v,
        )