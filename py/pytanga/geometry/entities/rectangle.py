# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Rectangle2D visualization-only entity data class."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV


@dataclass(frozen=True)
class Rectangle2D:
    """A flat rectangle, purely for visualization.

    Unlike the MV-backed entities in this package, a :class:`Rectangle2D` has
    **no** multivector representation — it cannot be passed to
    :func:`~pytanga.geometry.create` or produced by
    :func:`~pytanga.geometry.analyze`.  It exists only as a rendering hint for
    the visualizer (e.g. interactive rectangles on an image).

    The rectangle lies in the plane perpendicular to ``normal`` (default ``+z``,
    the natural choice for 2D use cases and the xy-plane in 3D), centered on
    ``center``.  ``size`` is the full width (x) and height (y).  ``angle`` is an
    in-plane rotation in radians (default ``0.0`` = axis-aligned).

    Parameters
    ----------
    center:
        Center of the rectangle (default ``(0, 0, 0)``).
    size:
        Full ``(width, height)`` along the local x/y axes (default ``(1, 1)``).
    normal:
        Normal direction of the rectangle plane (default ``+z``).
    angle:
        In-plane rotation of the rectangle in radians (default ``0.0``).
    """

    center: Point
    size: tuple[float, float]
    normal: Direction = field(default_factory=lambda: Direction(0.0, 0.0, 1.0))
    angle: float = 0.0

    def __init__(
        self,
        center: "Point | MV | None" = None,
        size: "tuple[float, float] | list[float] | None" = None,
        normal: "Direction | MV | None" = None,
        angle: "float | MV | None" = None,
    ) -> None:
        center = Point(0.0, 0.0, 0.0) if center is None else to_point(center)
        if size is None:
            size = (1.0, 1.0)
        elif not isinstance(size, (tuple, list)) or len(size) != 2:
            raise TypeError(
                f"Expected a 2-sequence of floats, got {type(size).__name__}"
            )
        else:
            size = (to_float(size[0]), to_float(size[1]))
        normal = Direction(0.0, 0.0, 1.0) if normal is None else to_direction(normal)
        angle = 0.0 if angle is None else to_float(angle)

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "angle", angle)

    def __repr__(self) -> str:
        return (
            f"Rectangle2D(c={self.center}, size=({self.size[0]:.2f}, "
            f"{self.size[1]:.2f}), n={self.normal}, angle={self.angle:.3f})"
        )

    @classmethod
    def between(cls, a: "Point | MV", b: "Point | MV") -> "Rectangle2D":
        """Construct the axis-aligned rectangle with *a* and *b* as opposite corners.

        ``center`` is the midpoint of the two points and ``size`` is the
        absolute x/y difference, so the corner order does not matter.  The
        rectangle lies in the default ``normal`` plane (+z) with ``angle = 0``.
        """
        a = to_point(a)
        b = to_point(b)
        return cls(
            center=Point(
                (a.x + b.x) / 2.0,
                (a.y + b.y) / 2.0,
                (a.z + b.z) / 2.0,
            ),
            size=(abs(b.x - a.x), abs(b.y - a.y)),
        )
