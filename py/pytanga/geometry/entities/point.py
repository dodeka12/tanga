# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Point entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._util import _convert_mv, _fmt_v, _is_mv


@dataclass(frozen=True)
class Point:
    """A finite point in Euclidean 3D space.

    Attributes:
        x: The x-coordinate.
        y: The y-coordinate.
        z: The z-coordinate.

    Supported algebras: E3, P3, N3/PGA3

    Can be initialised from a multivector via
    :func:`~pytanga.geometry.analysis.analyze_point`, which dispatches to
    the algebra-specific analyzer.  In E3/E2 a plain Euclidean grade-1
    vector (blades e1/e2/e3 only) is read directly as a coordinate
    convenience.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if _is_mv(x):
            p = _convert_mv("point", x)
            object.__setattr__(self, "x", p.x)
            object.__setattr__(self, "y", p.y)
            object.__setattr__(self, "z", p.z)
        else:
            object.__setattr__(self, "x", float(x))
            object.__setattr__(self, "y", float(y))
            object.__setattr__(self, "z", float(z))

    def __repr__(self) -> str:
        return f"Point{_fmt_v(self.x, self.y, self.z)}"

    def __eq__(self, other) -> bool:
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y and self.z == other.z
        if isinstance(other, (tuple, list)) and len(other) == 3:
            return self.x == other[0] and self.y == other[1] and self.z == other[2]
        return NotImplemented

    def __neg__(self) -> "Point":
        return Point(-self.x, -self.y, -self.z)

    def __add__(self, other) -> "Point":
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        from .direction import Direction

        if isinstance(other, Direction):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __radd__(self, other) -> "Point":
        from .direction import Direction

        if isinstance(other, Direction):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __sub__(self, other):
        from .direction import Direction

        if isinstance(other, Point):
            return Direction(self.x - other.x, self.y - other.y, self.z - other.z)
        if isinstance(other, Direction):
            return Point(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Point(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented

    def __rmul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Point(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented

    def __truediv__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Point(self.x / scalar, self.y / scalar, self.z / scalar)
        return NotImplemented

    def dot(self, other: "Point | Direction") -> float:
        """Euclidean dot product with another Point or Direction."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Point | Direction") -> "Direction":
        """Vector cross product.  Always returns a Direction."""
        from .direction import Direction

        return Direction(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def mag(self) -> float:
        """Euclidean magnitude sqrt(x² + y² + z²)."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalized(self) -> "Point":
        """Return a normalised copy (same direction, magnitude 1)."""
        m = self.mag()
        if m == 0:
            raise ValueError("Cannot normalise zero-length Point")
        return Point(self.x / m, self.y / m, self.z / m)