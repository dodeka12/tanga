# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""The fundamental 3D vector type :class:`Vec3`.

``Vec3`` carries the shared Euclidean math (add, subtract, scalar and
element-wise multiply, dot, cross, magnitude, normalize) used by the semantic
entity types :class:`~pytanga.entity.point.Point` and
:class:`~pytanga.entity.direction.Direction`, which subclass it and override
the typed operations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga.entity.direction import Direction
    from pytanga.entity.point import Point


@dataclass(frozen=True)
class Vec3:
    """A 3D vector with Euclidean vector arithmetic."""

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"Vec3({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Vec3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return NotImplemented

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def __add__(self, other: "Vec3") -> "Vec3":
        if isinstance(other, Vec3):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __sub__(self, other: "Vec3") -> "Vec3":
        if isinstance(other, Vec3):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented

    def __mul__(self, other: "Vec3" | int | float) -> "Vec3":
        if isinstance(other, (int, float)):
            return Vec3(self.x * other, self.y * other, self.z * other)
        if isinstance(other, Vec3):
            return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)
        return NotImplemented

    def __rmul__(self, scalar: int | float) -> "Vec3":
        if isinstance(scalar, (int, float)):
            return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented

    def __truediv__(self, scalar: int | float) -> "Vec3":
        if isinstance(scalar, (int, float)):
            return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)
        return NotImplemented

    def elem_mul(self, other: "Vec3") -> "Vec3":
        """Element-wise (Hadamard) product."""
        return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)

    def dot(self, other: "Vec3") -> float:
        """Euclidean dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: "Vec3") -> "Vec3":
        """Vector cross product."""
        return Vec3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x,
        )

    def mag(self) -> float:
        """Euclidean magnitude sqrt(x² + y² + z²)."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self) -> "Vec3":
        """Return a normalised copy (magnitude 1)."""
        m = self.mag()
        if m == 0:
            raise ValueError("Cannot normalise zero-length Vec3")
        return Vec3(self.x / m, self.y / m, self.z / m)

    def to_point(self) -> "Point":
        """Convert to a :class:`~pytanga.entity.point.Point`."""
        from pytanga.entity.point import Point

        return Point(self.x, self.y, self.z)

    def to_direction(self) -> "Direction":
        """Convert to a :class:`~pytanga.entity.direction.Direction`."""
        from pytanga.entity.direction import Direction

        return Direction(self.x, self.y, self.z)

    @classmethod
    def from_point(cls, p: "Point") -> "Vec3":
        """Convert from a :class:`~pytanga.entity.point.Point`."""
        return cls(p.x, p.y, p.z)

    @classmethod
    def from_direction(cls, d: "Direction") -> "Vec3":
        """Convert from a :class:`~pytanga.entity.direction.Direction`."""
        return cls(d.x, d.y, d.z)
