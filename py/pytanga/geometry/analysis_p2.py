# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Projective Space".

"""P2-specific entity and operator analysis.

Uses :meth:`~pytanga.MV.blade_factorize` and
:meth:`~pytanga.MV.blade_factorize_versor` for decomposition.
Mirrors ``analysis_p3.py`` with 2D blade IDs and entities.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pytanga.basis.p2 import BasisP2

from .entities import Direction, Line, Point, Space
from .operators import ReflectionLine, ReflectionPoint, Rotor

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV

# Blade IDs — sourced from BasisP2 as single source of truth.
E1 = BasisP2.E1
E2 = BasisP2.E2
E3 = BasisP2.E3  # homogeneous dimension
E12 = BasisP2.E12
E13 = BasisP2.E13
E23 = BasisP2.E23
E123 = BasisP2.E123


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(mv: MV) -> Point | Direction | Line | Space | None:
    """Analyze an MV in P2 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    P2 OPNS entities (pure-grade blades):

    - Grade 1 → :class:`Point` (e₃ ≠ 0) or :class:`Direction` (e₃ = 0)
    - Grade 2 → :class:`Line` (2 homogeneous point factors)
    - Grade 3 → :class:`Space` (pseudoscalar e₁₂₃)
    """
    if not mv.algebra.opns:
        dual = mv.dual()
        return _analyze_entity_opns(dual)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(
    mv: MV,
) -> Point | Direction | Line | Space | None:
    """OPNS entity analysis."""
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in P2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_from_coeffs(mv)
    elif max_grade == 2:
        return _line_from_factors(mv)
    elif max_grade == 3:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in P2")


def _point_or_direction_from_coeffs(mv: MV) -> Point | Direction:
    """Read a grade-1 blade directly from coefficients."""
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    w = float(g1[E3])  # homogeneous weight (E3 in P2)

    if abs(x) < 1e-15 and abs(y) < 1e-15:
        if abs(w) < 1e-15:
            raise ValueError("Zero MV — not a point or direction")
        # All Euclidean components zero but e₃ ≠ 0 → only e₃ vector
        raise ValueError("MV has only e₃ component — not a point or direction in P2")

    if abs(w) < 1e-15:
        return Direction(x=x, y=y, z=0.0)
    return Point(x=x / w, y=y / w, z=0.0)


def _line_from_factors(mv: MV) -> Line:
    """Factorise a grade-2 blade → direction + point on line.

    With the ``Hop(a)∧Hop(b)`` construction, both factors have
    e₃ ≈ 1.  The difference gives the direction; either factor
    (after dehomogenization) gives a point on the line.
    """
    grade2 = mv.grade(2)

    # Blade‑ness check: a grade-2 blade must satisfy B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a line blade. "
            "(Bivector has non‑zero grade‑4 part: B∧B ≠ 0. "
            "Only simple (factorisable) bivectors represent lines in P2.)"
        )

    factors = grade2.blade_factorize()

    f0 = factors[0]
    f1 = factors[1]

    # Dehomogenize both factors
    w0 = float(f0[E3])
    w1 = float(f1[E3])

    if abs(w0) < 1e-15 or abs(w1) < 1e-15:
        # Fallback: one factor is a direction vector
        if abs(w0) < abs(w1):
            d_factor, p_factor = f0, f1
        else:
            d_factor, p_factor = f1, f0

        dx = float(d_factor[E1])
        dy = float(d_factor[E2])

        pw = float(p_factor[E3])
        if abs(pw) < 1e-15:
            origin = Point(0, 0, 0)
        else:
            origin = Point(
                x=float(p_factor[E1]) / pw,
                y=float(p_factor[E2]) / pw,
                z=0.0,
            )
        return Line(origin=origin, direction=Direction(x=dx, y=dy, z=0.0))

    # Both factors have e₃ ≠ 0: dehomogenize to get two points
    p0 = Point(x=float(f0[E1]) / w0, y=float(f0[E2]) / w0, z=0.0)
    p1 = Point(x=float(f1[E1]) / w1, y=float(f1[E2]) / w1, z=0.0)

    # Direction = difference
    dx = p1.x - p0.x
    dy = p1.y - p0.y
    d_norm = math.sqrt(dx * dx + dy * dy)
    if d_norm < 1e-15:
        raise ValueError("Degenerate line – points are identical")

    return Line(
        origin=p0,
        direction=Direction(dx / d_norm, dy / d_norm, 0.0),
    )


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> ReflectionLine | ReflectionPoint | Rotor:
    """Analyze an MV in P2 as a versor / operator.

    Reflection detection (by blade grade and e₃ component):

    - Grade 1, only e₃ → :class:`ReflectionPoint`
    - Grade 1, e₃ = 0 → :class:`ReflectionLine` (line through origin)
    - Grade 2, e₃ terms present → :class:`ReflectionLine` (line reflection)
    - 2 factors → :class:`Rotor`
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    grades = _get_grades(mv)

    # Pure-grade detection for reflections
    if len(grades) == 1:
        max_grade = max(grades)
        if max_grade == 1:
            return _classify_grade1_versor(mv)
        elif max_grade == 2:
            return _classify_grade2_versor(mv)

    # Factorization-based for mixed-grade versors
    scale, factors = mv.blade_factorize_versor()
    _ = scale

    if len(factors) == 1:
        return _classify_grade1_versor(factors[0])
    elif len(factors) == 2:
        return _rotor_from_factors(factors[0], factors[1])
    else:
        raise ValueError(f"Versor has {len(factors)} factors – unexpected for P2")


def _classify_grade1_versor(mv: MV) -> ReflectionLine | ReflectionPoint:
    """Grade-1 versor: determines ReflectionLine vs ReflectionPoint.

    - Only e₃ component → ReflectionPoint.
    - Euclidean components present, e₃ = 0 → ReflectionLine (line direction).
    """
    grade1 = mv.grade(1)
    e3_val = float(grade1[E3])
    ex = float(grade1[E1])
    ey = float(grade1[E2])
    eucl_norm = math.sqrt(ex * ex + ey * ey)

    if eucl_norm < 1e-15:
        if abs(e3_val) < 1e-15:
            raise ValueError("Zero vector – not a valid versor")
        return ReflectionPoint(Point(0.0, 0.0, 0.0))
    else:
        if abs(e3_val) > 1e-15:
            raise ValueError("Mixed e₃ and Euclidean components – ambiguous P2 versor")
        return ReflectionLine(direction=Direction(ex / eucl_norm, ey / eucl_norm, 0.0))


def _classify_grade2_versor(mv: MV) -> ReflectionLine:
    """Grade-2 bivector with e₃ terms → ReflectionLine.

    The bivector has form N∧e₃ with N = (nx, ny).
    """
    grade2 = mv.grade(2)
    nx = float(grade2[E13])
    ny = float(grade2[E23])
    n_norm = math.sqrt(nx * nx + ny * ny)
    if n_norm < 1e-15:
        raise ValueError("Zero direction in e₃ bivector – not a valid reflection")
    return ReflectionLine(direction=Direction(nx / n_norm, ny / n_norm, 0.0))


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two reflection lines → rotation.

    In 2D, the bivector is always e₁₂ (single component).
    """
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))

    bivector = n1.op(n2)
    bz = float(bivector[E12])

    axis = Direction(0, 0, 1)

    return Rotor(angle=angle, axis=axis)


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

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Point)


def analyze_direction(mv: MV) -> Direction:
    """Interpret *mv* as a :class:`Direction` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Direction)


def analyze_line(mv: MV) -> Line:
    """Interpret *mv* as a :class:`Line` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Line)


def analyze_space(mv: MV) -> Space:
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Space)
