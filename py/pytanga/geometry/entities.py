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

    Can be initialised from a BasisE3 multivector (grade-1),
    in which case only the e1, e2 and e3 components are used.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        # When called with a single MV argument, extract vector components
        if hasattr(x, "_alg"):
            mv = x
            object.__setattr__(self, "x", float(mv[1]))
            object.__setattr__(self, "y", float(mv[2]))
            object.__setattr__(self, "z", float(mv[4]))
        else:
            object.__setattr__(self, "x", float(x))
            object.__setattr__(self, "y", float(y))
            object.__setattr__(self, "z", float(z))

    def __repr__(self) -> str:
        return f"Point{_fmt_v(self.x, self.y, self.z)}"

    def __neg__(self) -> "Point":
        return Point(-self.x, -self.y, -self.z)

    def __add__(self, other) -> "Point":
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        if isinstance(other, Direction):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __radd__(self, other) -> "Point":
        if isinstance(other, Direction):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __sub__(self, other):
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

    Can be initialised from a BasisE3 multivector (grade-1),
    in which case only the e1, e2 and e3 components are used.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        # When called with a single MV argument, extract vector components
        if hasattr(x, "_alg"):
            mv = x
            object.__setattr__(self, "x", float(mv[1]))
            object.__setattr__(self, "y", float(mv[2]))
            object.__setattr__(self, "z", float(mv[4]))
        else:
            object.__setattr__(self, "x", float(x))
            object.__setattr__(self, "y", float(y))
            object.__setattr__(self, "z", float(z))

    def __repr__(self) -> str:
        return f"Dir{_fmt_v(self.x, self.y, self.z)}"

    def __neg__(self) -> "Direction":
        return Direction(-self.x, -self.y, -self.z)

    def __add__(self, other) -> "Direction":
        if isinstance(other, Direction):
            return Direction(self.x + other.x, self.y + other.y, self.z + other.z)
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented

    def __radd__(self, other) -> "Point":
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
    """An infinite line in 3D space.

    Can be constructed from origin+direction or directly from two points
    via :meth:`from_points`.

    The optional *length* field provides a rendering hint for the
    visualizer — when set, it overrides the default line length.
    ``None`` (the default) means "use the style default" (typically
    20 units for lines derived from geometric algebra).
    """

    origin: Point
    direction: Direction
    length: float | None = None

    def __repr__(self) -> str:
        return f"Line(org={self.origin}, dir={self.direction})"

    @classmethod
    def from_points(cls, start: Point, end: Point) -> "Line":
        """Construct a line segment from *start* to *end*.

        The direction is ``end - start`` and *length* is set to
        ``|end - start|`` so the visualizer draws exactly the segment.
        """
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


@dataclass(frozen=True)
class Plane:
    """An infinite plane in 3D space.

    The optional *span_u* and *span_v* fields define a parallelogram
    shape for rendering.  When both are provided, the visualizer draws
    a quad with those exact edge vectors instead of a square of size
    ``extent``.  When ``None``, *extent* controls the half-side of a
    square (default 10.0).
    """

    point: Point
    normal: Direction
    span_u: Direction | None = None
    span_v: Direction | None = None
    extent: float | None = None

    def __repr__(self) -> str:
        return f"Plane(pt={self.point}, n={self.normal})"

    @classmethod
    def from_corner_and_span(
        cls, corner: Point, u: Direction, v: Direction
    ) -> "Plane":
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
            point=center, normal=normal,
            span_u=2.0 * u, span_v=2.0 * v,
        )


@dataclass(frozen=True)
class Circle:
    """A circle in 3D space.

    For imaginary circles (N3-only, dual of a real point pair), set
    ``is_imaginary=True``.  They have no real Euclidean points on them.

    The ``normal`` defaults to ``Direction(0, 0, 1)`` (the positive
    z-axis), which is the natural choice for 2D use cases where the
    circle lies in the xy-plane.
    """

    center: Point
    radius: float
    normal: Direction | None = None
    is_imaginary: bool = False

    def __init__(
        self,
        center: Point,
        radius: float,
        normal: Direction | None = None,
        is_imaginary: bool = False,
    ):
        if normal is None:
            normal = Direction(0.0, 0.0, 1.0)
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", float(radius))
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
        center: Point,
        radius: float,
        normal: Direction | None = None,
        is_imaginary: bool = True,
    ):
        super().__init__(center, radius, normal, is_imaginary)


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
class HDirection:
    """A homogeneous direction (point at infinity).

    Represented by ``d∧e∞`` in the conformal model, where *d* is a
    Euclidean direction vector.  Useful as a reflection operator
    (reflect in a point at infinity → maps to e∞).

    Supported algebras: N3/N2 (needs e∞)
    """

    direction: Direction

    def __repr__(self) -> str:
        return f"HDirection(dir={self.direction})"


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
    | HDirection
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
