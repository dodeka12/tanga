# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Euclidean Space".

"""E3-specific entity and operator analysis.

Uses :meth:`~pytanga.MV.blade_factorize` and
:meth:`~pytanga.MV.blade_factorize_versor` for decomposition.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import Direction, Line, Plane, Point, Space
from .operators import ReflectionLine, ReflectionPlane, Rotor

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs are sourced from BasisE3 as the single source of truth.
# The module-level aliases exist for backward compatibility with code
# that imports them directly (e.g. ``from .analysis_e3 import E12``).
# New code should prefer ``basis.E12`` or ``mv.algebra.E12``.
from pytanga.basis.e3 import BasisE3

E1 = BasisE3.E1
E2 = BasisE3.E2
E3 = BasisE3.E3
E12 = BasisE3.E12
E13 = BasisE3.E13
E23 = BasisE3.E23
E123 = BasisE3.E123


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(mv: MV) -> Direction | Plane | Space | Line | None:
    """Analyze an MV in E3 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    OPNS entities (pure-grade blades):

    - Grade 1 → :class:`Direction` (line through origin in OPNS)

      .. note::

         A grade-1 vector created from a :class:`Line` through the
         origin via :func:`~pytanga.geometry.create_e3.create_line`
         will be analyzed as a :class:`Direction`, not a
         :class:`Line`.  This is an inherent limitation of E3 — the
         origin is always (0, 0, 0) and cannot be recovered from the
         MV alone.  Use P3 or N3 for round-trips that preserve the
         ``Line`` entity type.

    - Grade 2 → :class:`Plane` through origin (dualised to obtain normal)
    - Grade 3 → :class:`Space` (pseudoscalar)

    IPNS entities (via ``sdual()``):

    - Grade 1 → :class:`Plane` through origin (normal = vector)
    - Grade 2 → :class:`Line` through origin (intersection of two planes)
    - Grade 3 → raises ``ValueError`` (only the trivial origin solution)
    """
    if not mv.algebra.opns:
        return _analyze_entity_ipns(mv)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv: MV) -> Direction | Plane | Space | None:
    """OPNS entity analysis.

    In E3, grade-1 blades are lines through the origin (Direction),
    not points.  Grade-2 blades are planes through the origin.
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in E3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _direction_from_factor(mv)
    elif max_grade == 2:
        return _plane_from_bivector(mv)
    elif max_grade == 3:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in E3")


def _analyze_entity_ipns(mv: MV) -> Plane | Line | None:
    """IPNS analysis via blade grades of the original MV.

    Classifies directly based on the grade of the IPNS blade
    (without dualizing), using the Perwass E3 definitions:

    - IPNS grade 1 (vector *n*) → Plane through origin with normal n.
    - IPNS grade 2 (bivector *n∧m*) → Line through origin
      (intersection of two planes).
    - IPNS grade 3 (trivector) → raises ValueError (only trivial origin).
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade IPNS MV in E3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        # IPNS vector = plane normal → Plane through origin
        return _plane_from_ipns_vector(mv)
    elif max_grade == 2:
        # IPNS bivector = intersection of two planes → Line through origin
        return _line_from_ipns_bivector(mv)
    elif max_grade == 3:
        raise ValueError(
            "IPNS grade 3 in E3 corresponds to the origin (trivial solution); "
            "points cannot be represented in E3."
        )
    else:
        raise ValueError(f"Unexpected IPNS grade {max_grade} in E3")


def _plane_from_ipns_vector(mv: MV) -> Plane:
    """Extract a Plane through origin from an IPNS grade-1 vector.

    The vector *n* is the plane normal.  (Perwass: NI_G(n) is plane.)
    """
    grade1 = mv.grade(1)
    nx = float(grade1[E1])
    ny = float(grade1[E2])
    nz = float(grade1[E3])
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        raise ValueError("Zero vector – not a valid IPNS plane")
    return Plane(
        point=Point(0, 0, 0),
        normal=Direction(nx / length, ny / length, nz / length),
    )


def _line_from_ipns_bivector(mv: MV) -> Line:
    """Extract a Line through origin from an IPNS grade-2 bivector.

    IPNS bivector = n∧m (outer product of two plane normals).
    Its sdual gives a grade-1 vector = line direction.
    """
    dual = mv.dual()
    if dual.is_zero:
        raise ValueError("Zero dual – not a valid IPNS bivector")
    grade1 = dual.grade(1)
    dx = float(grade1[E1])
    dy = float(grade1[E2])
    dz = float(grade1[E3])
    return Line(origin=Point(0.0, 0.0, 0.0), direction=Direction(dx, dy, dz))


def _direction_from_factor(mv: MV) -> Direction:
    """Extract a Direction from a grade-1 vector.

    In E3 OPNS, a grade-1 blade represents a line through the origin.
    """
    grade1 = mv.grade(1)
    return Direction(
        x=float(grade1[E1]),
        y=float(grade1[E2]),
        z=float(grade1[E3]),
    )


def _plane_from_bivector(mv: MV) -> Plane:
    """Dualise a grade-2 blade → normal → Plane (through origin)."""
    grade2 = mv.grade(2)
    # In E3, the normal to a bivector is obtained via inner product with I⁻¹
    # bivector = nx·e₂₃ + ny·e₃₁ + nz·e₁₂ → normal = (nx, ny, nz)
    bx = float(grade2[E23])
    by = float(grade2[E13])
    bz = float(grade2[E12])
    length = math.sqrt(bx * bx + by * by + bz * bz)
    if length == 0:
        raise ValueError("Zero bivector – not a valid plane")

    return Plane(
        point=Point(0, 0, 0),
        normal=Direction(bx / length, by / length, bz / length),
    )


# ═══════════════════════════════════════════════════════════════
# Entity construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_point(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create an E3 vector (grade-1): ``x·e1 + y·e2 + z·e3``.

    Note: In E3 this is a direction / line through origin, not a point.
    """
    return alg.multivector({E1: x, E2: y, E3: z})


def make_plane(alg: Algebra, normal: Direction | tuple[float, float, float]) -> MV:
    """Create an E3 plane bivector from a normal vector.

    The result is: ``nx·e23 + ny·e31 + nz·e12``.
    """
    if isinstance(normal, Direction):
        nx, ny, nz = normal.x, normal.y, normal.z
    else:
        nx, ny, nz = normal
    return alg.multivector({E23: nx, E13: -ny, E12: nz})


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(mv: MV) -> ReflectionLine | ReflectionPlane | Rotor:
    """Analyze an MV in E3 as a versor / operator.

    Strategy: first check if *mv* is a pure-grade blade (single reflection).
    If so, the grade determines line (grade 1) vs plane (grade 2).
    Otherwise, use :meth:`~pytanga.MV.blade_factorize_versor`:

    - 1 factor (grade 1) → :class:`ReflectionLine`
    - 2 factors → :class:`Rotor`

    Note: a grade-2 bivector (ReflectionPlane) is a single blade, so it's
    detected via the pure-grade check before factorization.
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    grades = _get_grades(mv)

    # Pure-grade check: single blade → Reflection (line or plane)
    if len(grades) == 1:
        max_grade = max(grades)
        if max_grade == 1:
            return _reflection_from_grade1(mv)
        elif max_grade == 2:
            return _reflection_plane_from_bivector(mv)

    # Factorization-based analysis for mixed-grade versors
    scale, factors = mv.blade_factorize_versor()
    _ = scale

    if len(factors) == 1:
        return _reflection_from_factor(factors[0])
    elif len(factors) == 2:
        return _rotor_from_factors(factors[0], factors[1])
    else:
        raise ValueError(f"Versor has {len(factors)} factors – unexpected for E3")


def _reflection_from_grade1(mv: MV) -> ReflectionLine:
    """Pure grade-1 blade → ReflectionLine."""
    grade1 = mv.grade(1)
    return ReflectionLine(
        direction=Direction(float(grade1[E1]), float(grade1[E2]), float(grade1[E3]))
    )


def _reflection_plane_from_bivector(mv: MV) -> ReflectionPlane:
    """Pure grade-2 bivector → ReflectionPlane.

    The bivector ``n·I⁻¹`` has components (nx, ny, nz) in (e₂₃, e₃₁, e₁₂).
    """
    grade2 = mv.grade(2)
    bx = float(grade2[E23])
    by = float(grade2[E13])
    bz = float(grade2[E12])
    n_norm = math.sqrt(bx * bx + by * by + bz * bz)
    if n_norm < 1e-15:
        raise ValueError("Zero bivector – not a valid reflection plane")
    return ReflectionPlane(Direction(bx / n_norm, by / n_norm, bz / n_norm))


def _reflection_from_factor(f: MV) -> ReflectionLine:
    """Single grade-1 factor vector → ReflectionLine."""
    return ReflectionLine(Direction(float(f[E1]), float(f[E2]), float(f[E3])))


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two reflection planes → rotation.

    ``R = n2·n1`` (the product of the two reflectors).  The rotation
    angle is *2·acos(n1·n2)* and the axis is the bivector *n1 ∧ n2*.
    """
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))

    bivector = n1.op(n2)
    bx = float(bivector[E23])
    by = float(bivector[E13])
    bz = float(bivector[E12])

    bv_norm = math.sqrt(bx * bx + by * by + bz * bz)
    if bv_norm < 1e-15:
        axis = Direction(1, 0, 0)
    else:
        axis = Direction(bx / bv_norm, by / bv_norm, bz / bv_norm)

    return Rotor(angle=angle, axis=axis)


# ═══════════════════════════════════════════════════════════════
# Operator construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_rotor(alg: Algebra, angle: float, axis: Direction) -> MV:
    """Create an E3 rotor from angle (radians) and unit axis."""
    half = angle / 2.0
    return alg.multivector(
        {
            0: math.cos(half),
            E23: math.sin(half) * axis.x,
            E13: -math.sin(half) * axis.y,
            E12: math.sin(half) * axis.z,
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

    In E3, a finite point cannot be represented (the origin is fixed at
    ``(0, 0, 0)``).  This convenience reads a plain Euclidean grade-1
    vector ``x·e1 + y·e2 + z·e3`` directly into a :class:`Point`.
    """
    d = mv._impl.to_dict()
    for bid in d:
        if bid not in (E1, E2, E3):
            raise ValueError("An E3 point requires a plain e1/e2/e3 vector")
    return Point(
        x=float(d.get(E1, 0.0)),
        y=float(d.get(E2, 0.0)),
        z=float(d.get(E3, 0.0)),
    )


def analyze_direction(mv: MV) -> Direction:
    """Interpret *mv* as a :class:`Direction` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Direction)


def analyze_line(mv: MV) -> Line:
    """Interpret *mv* as an IPNS :class:`Line` (grade-2 bivector).

    In E3 a line is an IPNS entity; the MV only succeeds when the current
    ``mv.algebra.opns`` mode and input combination actually produce a Line.
    """
    return _expect(analyze_entity(mv), Line)


def analyze_plane(mv: MV) -> Plane:
    """Interpret *mv* as a :class:`Plane` through the origin.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Plane)


def analyze_space(mv: MV) -> Space:
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Space)
