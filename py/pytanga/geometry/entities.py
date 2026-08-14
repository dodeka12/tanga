# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra-independent geometric entity data classes.

These data classes represent geometric entities in Euclidean 3D space.
They are pure data containers with no dependency on pytanga.algebra,
pytanga.MV, or pytanga.basis. Algebra-specific conversion between MVs
and these entity classes is handled by the analysis and create modules.

Entity constructors accept a single multivector argument and convert it
via the matching typed analyzer, raising if the MV has the wrong
structure.  ``Point``/``Direction`` keep the E3 plain-vector convenience.
"""

from __future__ import annotations

from dataclasses import dataclass


def _fmt_v(x: float, y: float, z: float) -> str:
    """Format a 3D vector with 2 decimal places."""
    return f"({x:.2f}, {y:.2f}, {z:.2f})"


def _is_mv(x) -> bool:
    """True if *x* is a multivector (has the ``_alg`` slot)."""
    return hasattr(x, "_alg")


def _plain_vector_coords(mv):
    """Return ``(x, y, z)`` if *mv* is a plain Euclidean grade-1 vector.

    A "plain" vector is one whose non-zero blades are all grade-1 basis
    vectors e1/e2/e3 (blade ids 1, 2, 4).  Returns ``None`` otherwise.
    """
    d = mv._impl.to_dict()
    if not d:
        return None
    for bid in d:
        if bid not in (1, 2, 4):
            return None
    return (float(d.get(1, 0.0)), float(d.get(2, 0.0)), float(d.get(4, 0.0)))


def _import_analyzer(name):
    from . import analysis

    return getattr(analysis, f"analyze_{name}")


def _point_from_mv(mv) -> "Point":
    coords = _plain_vector_coords(mv)
    if coords is not None:
        return Point(coords[0], coords[1], coords[2])
    return _import_analyzer("point")(mv)


def _direction_from_mv(mv) -> "Direction":
    coords = _plain_vector_coords(mv)
    if coords is not None:
        return Direction(coords[0], coords[1], coords[2])
    return _import_analyzer("direction")(mv)


def _scalar(value):
    """Return the python scalar for a scalar MV, or *value* unchanged."""
    if _is_mv(value):
        if not value.is_scalar:
            raise ValueError("Expected a scalar multivector")
        return value.scalar
    return value


def _coerce(value, target):
    """Auto-convert an MV to the target python type.

    - ``target is Point``      → ``Point(value)`` (typed + E3 shortcut)
    - ``target is Direction``  → ``Direction(value)``
    - ``target is float``      → ``float(value.scalar)`` for scalar MVs
    """
    if _is_mv(value):
        if target is Point:
            return _point_from_mv(value)
        if target is Direction:
            return _direction_from_mv(value)
        if target is float:
            return float(_scalar(value))
    return value


@dataclass(frozen=True)
class Point:
    """A finite point in Euclidean 3D space.

    Attributes:
        x: The x-coordinate.
        y: The y-coordinate.
        z: The z-coordinate.

    Supported algebras: E3, P3, N3/PGA3

    Can be initialised from a multivector:

    - A plain Euclidean grade-1 vector (blades e1/e2/e3 only) in E3 is
      read directly (the E3 convenience).
    - Any other MV is converted via :func:`~pytanga.geometry.analysis.analyze_point`.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if _is_mv(x):
            p = _point_from_mv(x)
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

    Can be initialised from a multivector:

    - A plain Euclidean grade-1 vector (blades e1/e2/e3 only) in E3 is
      read directly (the E3 convenience).
    - Any other MV is converted via :func:`~pytanga.geometry.analysis.analyze_direction`.
    """

    x: float
    y: float
    z: float

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if _is_mv(x):
            d = _direction_from_mv(x)
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

    def __init__(self, point, weight=1.0):
        if _is_mv(point) and weight == 1.0:
            h = _import_analyzer("hpoint")(point)
            object.__setattr__(self, "point", h.point)
            object.__setattr__(self, "weight", h.weight)
        else:
            object.__setattr__(self, "point", _coerce(point, Point))
            object.__setattr__(self, "weight", float(_coerce(weight, float)))

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

    def __init__(
        self,
        point_a,
        point_b=None,
        is_imaginary=False,
        _center=None,
        _direction=None,
        _separation=None,
    ):
        if _is_mv(point_a) and point_b is None:
            pp = _import_analyzer("point_pair")(point_a)
            object.__setattr__(self, "point_a", pp.point_a)
            object.__setattr__(self, "point_b", pp.point_b)
            object.__setattr__(self, "is_imaginary", pp.is_imaginary)
            object.__setattr__(self, "_center", pp._center)
            object.__setattr__(self, "_direction", pp._direction)
            object.__setattr__(self, "_separation", pp._separation)
        else:
            object.__setattr__(self, "point_a", _coerce(point_a, Point))
            object.__setattr__(self, "point_b", _coerce(point_b, Point))
            object.__setattr__(self, "is_imaginary", is_imaginary)
            object.__setattr__(
                self, "_center", None if _center is None else _coerce(_center, Point)
            )
            object.__setattr__(
                self,
                "_direction",
                None if _direction is None else _coerce(_direction, Direction),
            )
            object.__setattr__(
                self,
                "_separation",
                None if _separation is None else _coerce(_separation, float),
            )

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
        if _is_mv(origin):
            line = _import_analyzer("line")(origin)
            object.__setattr__(self, "origin", line.origin)
            object.__setattr__(self, "direction", line.direction)
            object.__setattr__(self, "length", line.length)
        else:
            object.__setattr__(self, "origin", _coerce(origin, Point))
            object.__setattr__(self, "direction", _coerce(direction, Direction))
            object.__setattr__(
                self, "length", None if length is None else _coerce(length, float)
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
        if _is_mv(start):
            start = Point(start)
        if _is_mv(end):
            end = Point(end)
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

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_plane`).
    """

    point: Point
    normal: Direction
    span_u: Direction | None = None
    span_v: Direction | None = None
    extent: float | None = None

    def __init__(self, point=None, normal=None, span_u=None, span_v=None, extent=None):
        if _is_mv(point):
            plane = _import_analyzer("plane")(point)
            object.__setattr__(self, "point", plane.point)
            object.__setattr__(self, "normal", plane.normal)
            object.__setattr__(self, "span_u", plane.span_u)
            object.__setattr__(self, "span_v", plane.span_v)
            object.__setattr__(self, "extent", plane.extent)
        else:
            object.__setattr__(self, "point", _coerce(point, Point))
            object.__setattr__(self, "normal", _coerce(normal, Direction))
            object.__setattr__(
                self, "span_u", None if span_u is None else _coerce(span_u, Direction)
            )
            object.__setattr__(
                self, "span_v", None if span_v is None else _coerce(span_v, Direction)
            )
            object.__setattr__(
                self, "extent", None if extent is None else _coerce(extent, float)
            )

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
        if _is_mv(center) and radius is None:
            circle = _import_analyzer("circle")(center)
            object.__setattr__(self, "center", circle.center)
            object.__setattr__(self, "radius", circle.radius)
            object.__setattr__(self, "normal", circle.normal)
            object.__setattr__(self, "is_imaginary", circle.is_imaginary)
        else:
            if normal is None:
                normal = Direction(0.0, 0.0, 1.0)
            object.__setattr__(self, "center", _coerce(center, Point))
            object.__setattr__(self, "radius", float(_coerce(radius, float)))
            object.__setattr__(self, "normal", _coerce(normal, Direction))
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


@dataclass(frozen=True)
class Sphere:
    """A sphere in 3D space.

    For imaginary spheres (N3-only, ``S = A + ½ρ² e∞``), set
    ``is_imaginary=True``.  Imaginary spheres have ``S² = −ρ²``
    (negative squared norm — no real points).

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_sphere`).
    """

    center: Point
    radius: float
    is_imaginary: bool = False

    def __init__(self, center, radius=None, is_imaginary=False):
        if _is_mv(center) and radius is None:
            sphere = _import_analyzer("sphere")(center)
            object.__setattr__(self, "center", sphere.center)
            object.__setattr__(self, "radius", sphere.radius)
            object.__setattr__(self, "is_imaginary", sphere.is_imaginary)
        else:
            object.__setattr__(self, "center", _coerce(center, Point))
            object.__setattr__(self, "radius", float(_coerce(radius, float)))
            object.__setattr__(self, "is_imaginary", is_imaginary)

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

    def __init__(self, direction):
        if _is_mv(direction):
            hd = _import_analyzer("hdirection")(direction)
            object.__setattr__(self, "direction", hd.direction)
        else:
            object.__setattr__(self, "direction", _coerce(direction, Direction))

    def __repr__(self) -> str:
        return f"HDirection(dir={self.direction})"


@dataclass(frozen=True)
class Space:
    """The entire 3D volume (pseudoscalar).

    Attributes:
        scale: The scalar coefficient of the pseudoscalar blade
            (OPNS), or the grade-0 scalar value (IPNS).

    Can also be constructed from a single multivector (converted via
    :func:`~pytanga.geometry.analysis.analyze_space`).
    """

    scale: float = 1.0

    def __init__(self, scale=1.0):
        if _is_mv(scale):
            if scale.is_scalar:
                object.__setattr__(self, "scale", float(scale.scalar))
            else:
                s = _import_analyzer("space")(scale)
                object.__setattr__(self, "scale", s.scale)
        else:
            object.__setattr__(self, "scale", float(scale))


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