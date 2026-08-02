# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra-independent geometric entity data classes.

These data classes represent geometric entities in Euclidean 3D space.
They are pure data containers with no dependency on pytanga.algebra,
pytanga.MV, or pytanga.basis. Algebra-specific conversion between MVs
and these entity classes is handled by the analysis and create modules.
"""

from __future__ import annotations

from dataclasses import dataclass


def _fmt_v(x: float, y: float, z: float) -> str:
    """Format a 3D vector with 2 decimal places."""
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


@dataclass(frozen=True)
class Point:
    """A finite point in Euclidean 3D space.

    Attributes:
        x: The x-coordinate.
        y: The y-coordinate.
        z: The z-coordinate.

    Supported algebras: E3, P3, N3/PGA3
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"Point{_fmt_v(self.x, self.y, self.z)}"


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

    Supported algebras: E3, P3, N3/PGA3
    """

    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"Dir{_fmt_v(self.x, self.y, self.z)}"


@dataclass(frozen=True)
class HPoint:
    """A flat point — finite point with homogeneous weight (N3-only)."""

    point: Point
    weight: float = 1.0

    def __repr__(self) -> str:
        return f"HPoint({self.point}, w={self.weight:.2f})"


@dataclass(frozen=True)
class PointPair:
    """A pair of points (CGA grade-2 entity).

    For imaginary point pairs (N3-only, dual of a real circle), set
    ``is_imaginary=True``.  They have no real Euclidean points
    satisfying ``X·PP = 0``.

    The optional reconstruction fields ``_center``, ``_direction``,
    and ``_separation`` store the data needed to reconstruct an
    imaginary point pair via ``create_imag_point_pair`` (needed
    because the dual-of-circle representation is not directly
    expressible from ``point_a``/``point_b`` alone).
    """

    point_a: Point
    point_b: Point
    is_imaginary: bool = False
    _center: Point | None = None
    _direction: Direction | None = None
    _separation: float | None = None

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}PntPair({self.point_a}, {self.point_b})"


@dataclass(frozen=True)
class ImagPointPair(PointPair):
    """An imaginary point pair (N3/PGA3 only).

    Inherits all fields from :class:`PointPair` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.default_styles`
    (e.g. ``viz.default_styles[ImagPointPair]``).
    """

    is_imaginary: bool = True


@dataclass(frozen=True)
class Line:
    """An infinite line in 3D space."""

    origin: Point
    direction: Direction

    def __repr__(self) -> str:
        return f"Line(org={self.origin}, dir={self.direction})"


@dataclass(frozen=True)
class Plane:
    """An infinite plane in 3D space."""

    point: Point
    normal: Direction

    def __repr__(self) -> str:
        return f"Plane(pt={self.point}, n={self.normal})"


@dataclass(frozen=True)
class Circle:
    """A circle in 3D space.

    For imaginary circles (N3-only, dual of a real point pair), set
    ``is_imaginary=True``.  They have no real Euclidean points on them.
    """

    center: Point
    normal: Direction
    radius: float
    is_imaginary: bool = False

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}Circle(c={self.center}, n={self.normal}, r={self.radius:.2f})"


@dataclass(frozen=True)
class ImagCircle(Circle):
    """An imaginary circle in 3D space.

    Inherits all fields from :class:`Circle` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.default_styles`
    (e.g. ``viz.default_styles[ImagCircle]``).
    """

    is_imaginary: bool = True


@dataclass(frozen=True)
class Sphere:
    """A sphere in 3D space.

    For imaginary spheres (N3-only, ``S = A + ½ρ² e∞``), set
    ``is_imaginary=True``.  Imaginary spheres have ``S² = −ρ²``
    (negative squared norm — no real points).
    """

    center: Point
    radius: float
    is_imaginary: bool = False

    def __repr__(self) -> str:
        prefix = "Imag" if self.is_imaginary else ""
        return f"{prefix}Sphere(c={self.center}, r={self.radius:.2f})"


@dataclass(frozen=True)
class ImagSphere(Sphere):
    """An imaginary sphere in 3D space.

    Inherits all fields from :class:`Sphere` with ``is_imaginary=True``.
    Can be used as a class-based key in :attr:`Visualizer.default_styles`
    (e.g. ``viz.default_styles[ImagSphere]``).
    """

    is_imaginary: bool = True


@dataclass(frozen=True)
class Space:
    """The entire 3D volume (pseudoscalar).

    Attributes:
        scale: The scalar coefficient of the pseudoscalar blade
            (OPNS), or the grade-0 scalar value (IPNS).
    """

    scale: float = 1.0


# Union type for all entities
Entity = (
    Point
    | Direction
    | HPoint
    | PointPair
    | ImagPointPair
    | Line
    | Plane
    | Circle
    | ImagCircle
    | Sphere
    | ImagSphere
    | Space
)
