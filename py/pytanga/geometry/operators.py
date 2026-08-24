# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra-independent operator (versor) data classes.

These data classes represent geometric operators (versors/transformations)
in Euclidean 3D space. They are pure data containers with no dependency
on pytanga.algebra, pytanga.MV, or pytanga.basis. Algebra-specific
conversion between MVs and these operator classes is handled by the
analysis and create modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from .entities import (
    Direction,
    HDirection,
    Line,
    Plane,
    Point,
    to_direction,
    to_float,
    to_point,
)


@dataclass(frozen=True)
class ReflectionLine:
    """Reflection across a line (not necessarily through origin).

    The versor is ``Cop(a)∧Cop(b)∧e∞`` for two points a, b on the line.
    Equivalent to the OPNS line entity blade.

    Can be constructed with either a :class:`Line` (new, full line) or a
    :class:`Direction` (backward-compat, origin-only line).

    Supported algebras: E3, P3, N3/PGA3 (origin-only via Direction),
                       N3/N2 (full entity blade)
    """

    line: Line

    def __init__(self, line_or_direction: Line | Direction):
        if isinstance(line_or_direction, Direction):
            line_or_direction = Line(Point(0, 0, 0), line_or_direction)
        elif not isinstance(line_or_direction, Line):
            raise TypeError(
                "ReflectionLine requires a Line or Direction, got "
                f"{type(line_or_direction).__name__}"
            )

        object.__setattr__(self, "line", line_or_direction)

    def __repr__(self) -> str:
        return f"ReflLine(line={self.line})"


@dataclass(frozen=True)
class ReflectionPlane:
    """Reflection across a plane (not necessarily through origin).

    The versor is ``Cop(a)∧Cop(b)∧Cop(c)∧e∞`` for three non-collinear
    points a, b, c on the plane.  Equivalent to the OPNS plane entity blade.

    Can be constructed with either a :class:`Plane` (new, full plane) or a
    :class:`Direction` (backward-compat, origin-only plane).

    Supported algebras: E3, P3, N3/PGA3 (origin-only via Direction),
                       N3/N2 (full entity blade)
    """

    plane: Plane

    def __init__(self, plane_or_normal: Plane | Direction):
        if isinstance(plane_or_normal, Direction):
            plane_or_normal = Plane(Point(0, 0, 0), plane_or_normal)
        elif not isinstance(plane_or_normal, Plane):
            raise TypeError(
                "ReflectionPlane requires a Plane or Direction, got "
                f"{type(plane_or_normal).__name__}"
            )
        object.__setattr__(self, "plane", plane_or_normal)

    def __repr__(self) -> str:
        return f"ReflPlane(plane={self.plane})"


@dataclass(frozen=True)
class ReflectionPoint:
    """Reflection in a point.

    The versor is ``Cop(p)∧e∞`` — the HPoint blade used as a versor.
    Applying the sandwich reflects points across *p*: ``q → 2p − q``.

    Reflection in the origin is ``ReflectionPoint(Point(0,0,0))``.

    Supported algebras: N3/N2 (needs e∞)
    """

    point: Point

    def __init__(self, point: Point):
        point = to_point(point)
        object.__setattr__(self, "point", point)

    def __repr__(self) -> str:
        return f"ReflPoint(pt={self.point})"


@dataclass(frozen=True)
class Inversion:
    """Inversion in a sphere.

    Perwass: ``S = Cop(center) − ½·radius²·e∞`` is the sphere IPNS
    that acts as the inversion operator via ``S X S``.

    Supported algebras: N3 only (needs eo)
    """

    center: Point
    radius: float = 1.0

    def __init__(self, center: Point, radius: float = 1.0):
        center = to_point(center)
        radius = to_float(radius)
        object.__setattr__(self, "center", center)
        object.__setattr__(self, "radius", radius)

    def __repr__(self) -> str:
        return f"Inv(c={self.center}, r={self.radius:.2f})"


@dataclass(frozen=True)
class Rotor:
    """A 3D rotation (even-grade versor: scalar + bivector).

    Supported algebras: E3, P3, N3/PGA3
    """

    angle: float
    axis: Direction

    def __init__(self, angle: float, axis: Direction):
        angle = to_float(angle)
        axis = to_direction(axis)
        object.__setattr__(self, "angle", angle)
        object.__setattr__(self, "axis", axis)

    def __repr__(self) -> str:
        deg = math.degrees(self.angle)
        return f"Rotor({deg:.1f}° about {self.axis})"


@dataclass(frozen=True)
class Translator:
    """A translation in 3D space.

    Supported algebras: N3/PGA3
    """

    vector: Direction

    def __init__(self, vector: Direction):
        vector = to_direction(vector)
        object.__setattr__(self, "vector", vector)

    def __repr__(self) -> str:
        return f"Transl({self.vector})"


@dataclass(frozen=True)
class Dilator:
    """A uniform dilation (scaling) about an origin point.

    Form: ``D_t = T · D · T̃`` where T translates from the global origin
    to the dilation center and ``D = 1 + (1−d)/(1+d)·E`` is the
    origin‑centered dilator (E = e∞∧e₀, Perwass).

    When ``origin=(0,0,0)``, this is a pure dilator about the origin:
    ``D = 1 + (1−d)/(1+d)·E``, sandwich ``D·p·D̃`` scales p by factor d.

    Supported algebras: N3/N2 only (needs E = e∞∧e₀)
    """

    factor: float
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))

    def __init__(self, factor: float, origin: Optional[Point] = None):
        factor = to_float(factor)
        origin = to_point(origin) if origin is not None else Point(0, 0, 0)

        object.__setattr__(self, "factor", factor)
        object.__setattr__(self, "origin", origin)

    def __repr__(self) -> str:
        if self.origin.x == 0 and self.origin.y == 0 and self.origin.z == 0:
            return f"Dilator(×{self.factor:.2f})"
        return f"Dilator(×{self.factor:.2f} at {self.origin})"


def _motor_screw(
    angle: float,
    axis: Direction,
    t: Direction,
) -> tuple[GeneralRotor, Translator]:
    """Decompose a motor (rotation + translation) into its screw form.

    ``T(t)·R(angle, axis) = T(u)·(T(v)·R(angle, axis)·T̃(v))`` where ``u`` is
    along the rotation axis and ``v`` is perpendicular to it.  Returns
    ``(GeneralRotor, Translator)``.
    """
    a = axis.normalized() if axis.mag() > 1e-15 else Direction(0.0, 0.0, 1.0)

    if t.mag() < 1e-15:
        # Pure rotation: no translation and no axis displacement.
        return GeneralRotor(angle, a, Point(0.0, 0.0, 0.0)), Translator(
            Direction(0.0, 0.0, 0.0)
        )

    if abs(angle) < 1e-15:
        # Pure translation: infinite-pitch screw (no rotation).
        return GeneralRotor(0.0, a, Point(0.0, 0.0, 0.0)), Translator(t)

    t_par = a * t.dot(a)
    t_perp = t - t_par

    if t_perp.mag() < 1e-15:
        v = Direction(0.0, 0.0, 0.0)
    else:
        cot = 1.0 / math.tan(angle / 2.0)
        v = 0.5 * (t_perp + cot * a.cross(t_perp))

    return GeneralRotor(angle, a, Point(v.x, v.y, v.z)), Translator(t_par)


@dataclass(frozen=True)
class Motor:
    """A rigid body motion (screw): rotation about a displaced axis plus a
    translation along that axis.

    Stored as a :class:`GeneralRotor` and a :class:`Translator`; a ``Rotor`` +
    ``Translator`` input is normalized to this screw form on construction.

    Supported algebras: N3/PGA3
    """

    rotor: GeneralRotor
    translator: Translator

    def __init__(self, rotor: Rotor | GeneralRotor, translator: Translator):
        if not isinstance(translator, Translator):
            raise TypeError(f"Expected Translator, got {type(translator).__name__}")
        if isinstance(rotor, GeneralRotor):
            gen, trans = rotor, translator
        elif isinstance(rotor, Rotor):
            gen, trans = _motor_screw(rotor.angle, rotor.axis, translator.vector)
        else:
            raise TypeError(
                f"Expected Rotor or GeneralRotor, got {type(rotor).__name__}"
            )
        object.__setattr__(self, "rotor", gen)
        object.__setattr__(self, "translator", trans)

    def __repr__(self) -> str:
        return f"Motor({self.rotor}, {self.translator})"


@dataclass(frozen=True)
class GeneralRotor:
    """A rotation about an arbitrary origin point.

    The underlying MV is ``G = T · R · T̃`` where *T* translates from
    the global origin to the rotation center and *R* is the rotor.

    In 2D the axis is always ``Dir(0, 0, 1)`` and origin z=0.
    """

    angle: float
    axis: Direction
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))

    def __init__(self, angle: float, axis: Direction, origin: Optional[Point] = None):
        angle = to_float(angle)
        axis = to_direction(axis)
        origin = to_point(origin) if origin is not None else Point(0, 0, 0)

        object.__setattr__(self, "angle", angle)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "origin", origin)

    def __repr__(self) -> str:
        deg = math.degrees(self.angle)
        return f"GenRotor({deg:.1f}° about {self.axis} at {self.origin})"


@dataclass(frozen=True)
class TripleReflection:
    """Three successive plane reflections — reflection × rotor/translator.

    Because three reflections can be grouped as (rotor + reflection)
    or (translator + reflection) or (general rotor + reflection) in
    multiple ways, the decomposition into rotor+translator is not unique.
    This class preserves the raw plane information for downstream use.
    """

    planes: tuple[Plane, Plane, Plane]

    def __repr__(self) -> str:
        return f"TripleRefl({self.planes[0]}, {self.planes[1]}, {self.planes[2]})"


@dataclass(frozen=True)
class VersorFactors:
    """Unclassified versor — raw grade-1 factors from blade factorization.

    Used as a fallback when a versor cannot be classified as a specific
    operator (e.g. mixed dilator+rotor combinations in N3/N2).
    """

    factors: tuple = ()  # tuple of MV (grade-1 vectors)

    def __repr__(self) -> str:
        return f"VersorFactors({len(self.factors)} factors)"


# Backward-compatibility alias: Reflection → ReflectionPlane
Reflection = ReflectionPlane  # deprecated; use ReflectionLine/ReflectionPlane

# Union type for all operators
Operator = (
    ReflectionLine
    | ReflectionPlane
    | ReflectionPoint
    | HDirection
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | TripleReflection
    | VersorFactors
)
