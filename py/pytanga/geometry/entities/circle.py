# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Circle entity data classes."""

from __future__ import annotations

from dataclasses import dataclass

from pytanga.geometry.entities._util import _convert_mv

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Circle:
    """A circle in 3D space.

    For imaginary circles (N3-only, dual of a real point pair), set
    ``is_imaginary=True``.  They have no real Euclidean points on them.

    The ``normal`` defaults to ``Direction(0, 0, 1)`` (the positive
    z-axis), which is the natural choice for 2D use cases where the
    circle lies in the xy-plane.

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_circle`).
    """

    center: Point
    radius: float
    normal: Direction | None = None
    is_imaginary: bool = False

    def __init__(
        self,
        center,
        radius=None,
        normal=None,
        is_imaginary=False,
    ):
        try:
            center = to_point(center)
        except TypeError:
            circle = _convert_mv("circle", center)
            object.__setattr__(self, "center", circle.center)
            object.__setattr__(self, "radius", circle.radius)
            object.__setattr__(self, "normal", circle.normal)
            object.__setattr__(self, "is_imaginary", circle.is_imaginary)
            return

        radius = to_float(radius)
        normal = (
            to_direction(normal) if normal is not None else Direction(0.0, 0.0, 1.0)
        )

        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", radius)
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "is_imaginary", is_imaginary)

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}Circle(c={self.center}, r={self.radius:.2f}, n={self.normal})"


@dataclass(frozen=True)
class ImagCircle(Circle):
    """An imaginary circle in 3D space.

    Inherits all fields from :class:`Circle` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.default_styles`
    (e.g. ``viz.default_styles[ImagCircle]``).

    Like :class:`Circle`, the ``normal`` defaults to ``Direction(0, 0, 1)``
    when not provided.
    """

    is_imaginary: bool = True

    def __init__(
        self,
        center,
        radius=None,
        normal=None,
        is_imaginary=True,
    ):
        super().__init__(center, radius, normal, is_imaginary)
