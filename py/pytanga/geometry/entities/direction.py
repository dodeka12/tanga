# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Direction entity data class."""

from __future__ import annotations

from dataclasses import dataclass

from ._util import _convert_mv, _fmt_v, _is_mv


@dataclass(frozen=True)
class Direction:
    """A direction vector in 3D space.

    In E3, a grade-1 vector represents a line through the origin in OPNS
    (see Perwass §"Outer Product Representations", eqn. GAGeo:E3:OPLine1).
    In P3/N3/PGA3, a direction represents an ideal point at infinity.

    Attributes:
        x: The x-component of the direction vector.
        y: The y-component of the direction vector.
        z: The z-component of the direction vector.

    Can be initialised from a multivector via
    :func:`~pytanga.geometry.analysis.analyze_direction`, which dispatches
    to the algebra-specific analyzer.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if _is_mv(x):
            d = _convert_mv("direction", x)
            object.__setattr__(self, "x", d.x)
            object.__setattr__(self, "y", d.y)
            object.__setattr__(self, "z", d.z)
        else:
            object.__setattr__(self, "x", float(x))
            object.__setattr__(self, "y", float(y))
            object.__setattr__(self, "z", float(z))

    def __repr__(self) -> str:
        return f"Dir{_fmt_v(self.x, self.y, self.z)}"

    def __eq__(self, other) -> bool:
        if isinstance(other, Direction):
            return self.x == other.x and self.y == other.y and self.z == other.z
        if isinstance(other, (tuple, list)) and len(other) == 3:
            return self.x == other[0] and self.y == other[1] and self.z == other[2]
        return NotImplemented

    def __neg__(self) -> "Direction":
        return Direction(-self.x, -self.y, -self.z)

    def __add__(self, other) -> "Direction":
        if isinstance(other, Direction):
            return Direction(self.x + other.x, self.y + other.y, self.z + other.z)
        from .point import Point

        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __radd__(self, other) -> "Point":
        from .point import Point

        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __sub__(self, other) -> "Direction":
        if isinstance(other, Direction):
            return Direction(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented

    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Direction(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented

    def __rmul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Direction(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented

    def __truediv__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Direction(self.x / scalar, self.y / scalar, self.z / scalar)
        return NotImplemented

    def dot(self, other: "Point | Direction") -> float:
        """Euclidean dot product with another Point or Direction."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Point | Direction") -> "Direction":
        """Vector cross product.  Always returns a Direction."""
        return Direction(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def mag(self) -> float:
        """Euclidean magnitude sqrt(x² + y² + z²)."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalized(self) -> "Direction":
        """Return a normalised copy (same direction, magnitude 1)."""
        m = self.mag()
        if m == 0:
            raise ValueError("Cannot normalise zero-length Direction")
        return Direction(self.x / m, self.y / m, self.z / m)