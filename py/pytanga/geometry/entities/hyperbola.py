# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Hyperbola entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._coerce import to_direction, to_float, to_point
from .direction import Direction
from .point import Point


@dataclass(frozen=True)
class Hyperbola:
    """A 2D hyperbola.

    ``dir1``/``dir2`` are the (orthogonal) transverse and conjugate axis
    directions; ``a``/``b`` are the corresponding semi-axis lengths.  ``center``
    is the conic center.  The hyperbola is the image of
    ``(a·cosh t, b·sinh t)`` along ``dir1``/``dir2``.
    """

    center: Point
    dir1: Direction
    dir2: Direction
    a: float
    b: float

    def __init__(self, center, dir1, dir2, a, b):
        object.__setattr__(self, "center", to_point(center))
        object.__setattr__(self, "dir1", to_direction(dir1))
        object.__setattr__(self, "dir2", to_direction(dir2))
        object.__setattr__(self, "a", to_float(a))
        object.__setattr__(self, "b", to_float(b))

    def __repr__(self) -> str:
        return (
            f"Hyperbola(c={self.center}, d1={self.dir1}, d2={self.dir2}, "
            f"a={self.a:.2f}, b={self.b:.2f})"
        )
