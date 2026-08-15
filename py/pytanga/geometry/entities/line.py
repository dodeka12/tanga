# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Line entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from ._util import _convert_mv
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Line:
    """An infinite line in 3D space.

    Can be constructed from origin+direction, from two points via
    :meth:`from_points`, or from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_line`).

    The optional *length* field provides a rendering hint for the
    visualizer — when set, it overrides the default line length.
    ``None`` (the default) means "use the style default" (typically
    20 units for lines derived from geometric algebra).
    """

    origin: Point
    direction: Direction
    length: float | None = None

    def __init__(self, origin=None, direction=None, length=None):
        try:
            origin = to_point(origin)
        except TypeError:
            line = _convert_mv("line", origin)
            object.__setattr__(self, "origin", line.origin)
            object.__setattr__(self, "direction", line.direction)
            object.__setattr__(self, "length", line.length)
            return

        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "direction", to_direction(direction))
        object.__setattr__(
            self, "length", None if length is None else to_float(length)
        )

    def __repr__(self) -> str:
        return f"Line(org={self.origin}, dir={self.direction})"

    @classmethod
    def from_points(cls, start, end) -> "Line":
        """Construct a line segment from *start* to *end*.

        The direction is ``end - start`` and *length* is set to
        ``|end - start|`` so the visualizer draws exactly the segment.
        Multivector arguments are auto-converted via :class:`Point`.
        """
        start = to_point(start)
        end = to_point(end)
        direction = end - start
        return cls(origin=start, direction=direction, length=direction.mag())

    @property
    def start(self) -> Point:
        """The origin point of the line (alias for :attr:`origin`)."""
        return self.origin

    @property
    def end(self) -> Point:
        """A point on the line at distance ``length`` from ``origin``.

        When *length* is set (as with :meth:`from_points`), this is
        exactly the endpoint passed to the factory.
        """
        if self.length is not None:
            return self.origin + self.direction.normalized() * self.length
        return self.origin + self.direction