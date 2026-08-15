# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Euclidean Space".

"""E2-specific entity and operator analysis.

Uses :meth:`~pytanga.MV.blade_factorize` and
:meth:`~pytanga.MV.blade_factorize_versor` for decomposition.
Mirrors ``analysis_e3.py`` with 2D blade IDs and entities.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import Direction, Line, Point, Space
from .operators import ReflectionLine, Rotor

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs — sourced from BasisE2 as single source of truth.
from pytanga.basis.e2 import BasisE2

E1 = BasisE2.E1
E2 = BasisE2.E2
E12 = BasisE2.E12


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(mv: MV) -> Direction | Space | Line | None:
    """Analyze an MV in E2 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    OPNS entities (pure-grade blades):

    - Grade 1 → :class:`Direction` (line through origin in OPNS)
    - Grade 2 → :class:`Space` (pseudoscalar e₁₂)

    IPNS entities (via ``dual()``):

    - Grade 1 → :class:`Direction` (line normal, same as OPNS direction)
    - Grade 2 → raises ``ValueError`` (only trivial origin)
    """
    if not mv.algebra.opns:
        return _analyze_entity_ipns(mv)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv: MV) -> Direction | Space | None:
    """OPNS entity analysis.

    In E2, grade-1 blades are lines through the origin (Direction),
    not points.  Grade-2 blades are the pseudoscalar (Space).
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in E2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _direction_from_factor(mv)
    elif max_grade == 2:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in E2")


def _analyze_entity_ipns(mv: MV) -> Direction:
    """IPNS analysis via blade grades of the original MV.

    In E2 IPNS:
    - IPNS grade 1 (vector *n*) → Direction (line normal) through origin.
    - IPNS grade 2 (bivector) → raises ValueError (only trivial origin).
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade IPNS MV in E2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        # IPNS vector = line normal → Direction
        return _direction_from_ipns_vector(mv)
    elif max_grade == 2:
        raise ValueError(
            "IPNS grade 2 in E2 corresponds to the origin (trivial solution); "
            "points cannot be represented in E2."
        )
    else:
        raise ValueError(f"Unexpected IPNS grade {max_grade} in E2")


def _direction_from_ipns_vector(mv: MV) -> Direction:
    """Extract a Direction from an IPNS grade-1 vector.

    The vector *n* is the line normal.  In 2D, the OPNS direction is
    perpendicular: direction = (-ny, nx).
    """
    grade1 = mv.grade(1)
    nx = float(grade1[E1])
    ny = float(grade1[E2])
    length = math.sqrt(nx * nx + ny * ny)
    if length == 0:
        raise ValueError("Zero vector – not a valid IPNS line")
    return Direction(nx / length, ny / length, 0.0)


def _direction_from_factor(mv: MV) -> Direction:
    """Extract a Direction from a grade-1 vector.

    In E2 OPNS, a grade-1 blade represents a line through the origin.
    """
    grade1 = mv.grade(1)
    return Direction(
        x=float(grade1[E1]),
        y=float(grade1[E2]),
        z=0.0,
    )


# ═══════════════════════════════════════════════════════════════
# Entity construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_point(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create an E2 vector (grade-1): ``x·e1 + y·e2``.

    Note: In E2 this is a direction / line through origin, not a point.
    """
    return alg.multivector({E1: x, E2: y})


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(mv: MV) -> ReflectionLine | Rotor:
    """Analyze an MV in E2 as a versor / operator.

    Strategy: first check if *mv* is a pure-grade blade (single reflection).
    If so, grade 1 → ReflectionLine.
    Otherwise, use :meth:`~pytanga.MV.blade_factorize_versor`:

    - 1 factor (grade 1) → :class:`ReflectionLine`
    - 2 factors → :class:`Rotor`
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    grades = _get_grades(mv)

    # Pure-grade check: single blade → ReflectionLine
    if len(grades) == 1:
        max_grade = max(grades)
        if max_grade == 1:
            return _reflection_from_grade1(mv)

    # Factorization-based analysis for mixed-grade versors
    scale, factors = mv.blade_factorize_versor()
    _ = scale

    if len(factors) == 1:
        return _reflection_from_factor(factors[0])
    elif len(factors) == 2:
        return _rotor_from_factors(factors[0], factors[1])
    else:
        raise ValueError(f"Versor has {len(factors)} factors – unexpected for E2")


def _reflection_from_grade1(mv: MV) -> ReflectionLine:
    """Pure grade-1 blade → ReflectionLine."""
    grade1 = mv.grade(1)
    return ReflectionLine(
        direction=Direction(float(grade1[E1]), float(grade1[E2]), 0.0)
    )


def _reflection_from_factor(f: MV) -> ReflectionLine:
    """Single grade-1 factor vector → ReflectionLine."""
    return ReflectionLine(direction=Direction(float(f[E1]), float(f[E2]), 0.0))


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two reflection lines → rotation.

    ``R = n2·n1`` (the product of the two reflectors).  The rotation
    angle is *2·acos(n1·n2)* and the axis is e₁₂ (only bivector in 2D).
    """
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))

    bivector = n1.op(n2)
    bz = float(bivector[E12])

    # In 2D, axis is always the pseudoscalar direction (z-axis)
    if abs(bz) < 1e-15:
        axis = Direction(0, 0, 1)
    else:
        # Sign of bz determines rotation direction
        axis = Direction(0, 0, 1)

    return Rotor(angle=angle, axis=axis)


# ═══════════════════════════════════════════════════════════════
# Operator construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_rotor(alg: Algebra, angle: float, axis: Direction) -> MV:
    """Create an E2 rotor from angle (radians).  Axis is ignored (always e₁₂)."""
    half = angle / 2.0
    return alg.multivector(
        {
            0: math.cos(half),
            E12: math.sin(half),
        }
    )


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _get_grades(mv: MV) -> set[int]:
    """Return the set of grades present in *mv*."""
    return set(mv.grades)


# ═══════════════════════════════════════════════════════════════
# Typed analyzers
# ═══════════════════════════════════════════════════════════════


def _expect(result, cls):
    """Return *result* if it is an instance of *cls*; else raise."""
    if result is None:
        raise ValueError(f"MV does not represent a {cls.__name__}")
    if not isinstance(result, cls):
        raise TypeError(f"Expected a {cls.__name__}, got {type(result).__name__}")
    return result


def analyze_point(mv: MV) -> Point:
    """Interpret *mv* as a :class:`Point` in its algebra's OPNS/IPNS mode.

    In E2, a finite point cannot be represented (the origin is fixed at
    ``(0, 0)``).  This convenience reads a plain Euclidean grade-1 vector
    ``x·e1 + y·e2`` directly into a :class:`Point` (z = 0).
    """
    d = mv._impl.to_dict()
    for bid in d:
        if bid not in (E1, E2):
            raise ValueError("An E2 point requires a plain e1/e2 vector")
    return Point(
        x=float(d.get(E1, 0.0)),
        y=float(d.get(E2, 0.0)),
        z=0.0,
    )


def analyze_direction(mv: MV) -> Direction:
    """Interpret *mv* as a :class:`Direction` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Direction)


def analyze_line(mv: MV) -> Line:
    """Interpret *mv* as a :class:`Line` through the origin.

    In E2 a grade-1 vector is a line through the origin, analyzed as a
    :class:`Direction`; this wraps it into a ``Line(origin=(0,0,0), …)``.
    """
    d = analyze_direction(mv)
    return Line(origin=Point(0.0, 0.0, 0.0), direction=d)


def analyze_space(mv: MV) -> Space:
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Space)
