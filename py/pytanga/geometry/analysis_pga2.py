# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA2-specific entity and operator analysis.

Implements the Gunn/Dorst plane‑based PGA model (G(2, 0, 1)) within the
4D algebra via the null‑vector embedding e₀ = ep + em.

In 2D PGA, grades map to:
  - Grade 1 → Line (codimension‑1 hyperplane)
  - Grade 2 → Point (intersection of two lines)
  - Grade 3 → Space / Direction (IPNS OPNS dual)

Mirrors ``analysis_pga3.py`` with 2D blade IDs and entities.

References:
  Gunn, *Geometric algebras for Euclidean geometry* (arXiv:1411.6502, 2016)
  Dorst, *A Guided Tour to the Plane‑Based Geometric Algebra PGA* (2020)
  ``docs/py/basis/pga_null_embedding.md``
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._pga2_utils import (
    E1,
    E2,
    E12,
    EM,
    EP,
    _get_e0_coeff,
    _pga2_dual,
)
from .entities import Direction, Line, Point, Space
from .operators import GeneralRotor, Motor, ReflectionLine, Rotor, Translator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(mv: MV, *, opns: bool = True) -> Point | Direction | Line | Space:
    """Analyze an MV in PGA2 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.
    opns : bool, optional
        *True* (default) → OPNS interpretation.
        *False* → IPNS interpretation (dualizes to OPNS first).

    OPNS entities (Gunn/Dorst grades, 2D):

    - Grade 1 → :class:`Line`
    - Grade 2 → :class:`Point`
    - Grade 3 → :class:`Space` (pseudoscalar) or :class:`Direction`
    """
    if not opns:
        return _analyze_entity_ipns(mv)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv: MV) -> Point | Direction | Line | Space:
    """OPNS entity analysis (Gunn/Dorst grades, 2D)."""
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed‑grade MV in PGA2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _line_from_vector(mv)
    elif max_grade == 2:
        return _point_from_bivector(mv)
    elif max_grade == 3:
        return _point_or_space_from_trivector(mv)
    else:
        raise ValueError(f"Unexpected grade {max_grade} in PGA2 OPNS")


def _analyze_entity_ipns(mv: MV) -> Point | Direction | Line | Space:
    """IPNS entity analysis.

    IPNS grades in 2D Gunn/Dorst:
    - Grade 1 with e₀ → Point
    - Grade 1 without e₀ → Direction
    - Grade 2 → Line (dual = Line OPNS)
    - Grade 3 → Space (dual gives scalar)
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed‑grade MV in PGA2 IPNS: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_from_ipns(mv)
    elif max_grade == 2:
        # IPNS bivector → dual → OPNS grade‑1 line → Line
        opns = _pga2_dual(mv)
        return _line_from_vector(opns)
    elif max_grade == 3:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in PGA2 IPNS")


def _point_or_direction_from_ipns(mv: MV) -> Point | Direction:
    """Extract Point/Direction from a grade‑1 IPNS vector.

    Finite point: ``x·e₁ + y·e₂ + α·e₀`` → Point(x/α, y/α, 0).
    Direction:    ``x·e₁ + y·e₂`` (α = 0).
    """
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])

    alpha = _get_e0_coeff(mv)

    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=0.0)
    return Point(x=x / alpha, y=y / alpha, z=0.0)


# ── Grade 1: Line (OPNS) ────────────────────────────────────


def _line_from_vector(mv: MV) -> Line:
    """Extract a Line from a grade‑1 vector ``n + d·e₀``.

    In 2D PGA, a line is a codimension‑1 hyperplane.  The vector
    has the form: ``nx·e₁ + ny·e₂ + d·e₀`` where *d* is the signed
    distance from the origin.
    """
    g1 = mv.grade(1)
    nx = float(g1[E1])
    ny = float(g1[E2])
    d = float(g1[EP])  # e₀ component (same as EM)

    n_norm = math.sqrt(nx * nx + ny * ny)
    if n_norm < 1e-15:
        raise ValueError("Zero normal — not a valid line")

    ux, uy = nx / n_norm, ny / n_norm
    offset = d / n_norm  # signed distance along normal

    # Line through point: closest to origin is −d·â
    origin = Point(x=-ux * offset, y=-uy * offset, z=0.0)
    # Direction is perpendicular to normal
    direction = Direction(-uy, ux, 0.0)

    return Line(origin=origin, direction=direction)


# ── Grade 2: Point (OPNS) ───────────────────────────────────


def _point_from_bivector(mv: MV) -> Point:
    """Decompose a grade‑2 bivector → Point (intersection of 2 lines).

    In 2D PGA, a point is the intersection of two lines.  The bivector
    is factored into two grade‑1 lines, and their intersection is computed.
    """
    grade2 = mv.grade(2)

    # Blade‑ness check: a simple bivector satisfies B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a point. "
            "Only simple (factorisable) bivectors represent points in PGA2."
        )

    factors = grade2.blade_factorize()

    if len(factors) < 2:
        raise ValueError(f"Expected 2 line factors for point, got {len(factors)}")

    # Interpret each factor as a line vector
    l1 = _line_from_vector(factors[0])
    l2 = _line_from_vector(factors[1])

    # Point = intersection of two lines
    origin = _point_from_line_intersection(l1, l2)
    return origin


def _point_from_line_intersection(l1: Line, l2: Line) -> Point:
    """Compute intersection point of two 2D lines.

    Line 1: n1·p = d1  (where n1 = l1 normal, d1 = signed distance)
    Line 2: n2·p = d2

    Solve the 2×2 system:
      n1x·x + n1y·y = d1
      n2x·x + n2y·y = d2
    """
    n1x, n1y = -l1.direction.y, l1.direction.x  # normal from direction
    n2x, n2y = -l2.direction.y, l2.direction.x

    d1 = -(n1x * l1.origin.x + n1y * l1.origin.y)
    d2 = -(n2x * l2.origin.x + n2y * l2.origin.y)

    det = n1x * n2y - n1y * n2x
    if abs(det) < 1e-15:
        # Parallel lines — point at infinity → Direction
        raise ValueError("Parallel lines — intersection is at infinity (use Direction)")

    x = (d1 * n2y - d2 * n1y) / det
    y = (n1x * d2 - n2x * d1) / det
    return Point(x, y, 0.0)


# ── Grade 3: Point (from IPNS dual) / Space ─────────────────


def _point_or_space_from_trivector(mv: MV) -> Point | Direction | Space:
    """Extract a Point, Direction, or Space from a grade‑3 trivector.

    In 2D PGA (dim=4, pseudoscalar = 15 = e1∧e2∧ep∧em):
    - The dual of a Space trivector (e1∧e2∧e0) is a scalar.
    - The dual of a point (via IPNS) gives a grade‑1 vector.

    We check whether the dual is a scalar (Space) or a vector (Point/Direction).
    """
    dual = -_pga2_dual(mv)  # negate for correct sign

    # Check if dual is a scalar (Space)
    if dual.is_scalar or dual.grade(0).is_zero is False:
        scal = float(dual[0]) if not dual.is_scalar else float(dual.grade(0)[0])
        if abs(scal) < 1e-15:
            raise ValueError("Degenerate trivector")
        return Space(scale=scal)

    # Check if dual has Euclidean components → Point/Direction
    g1 = dual.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    eucl_norm = math.sqrt(x * x + y * y)
    if eucl_norm < 1e-15:
        # Pure e₀ component → Space? Check e₀ coefficient
        alpha = _get_e0_coeff(dual)
        if abs(alpha) < 1e-15:
            # Pure pseudoscalar encoding
            scale, _ = mv.blade_factorize_versor()
            return Space(scale=float(scale[0]))
        raise ValueError("Unrecognized trivector form")

    alpha = _get_e0_coeff(dual)
    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=0.0)
    return Point(x=x / alpha, y=y / alpha, z=0.0)


# ═══════════════════════════════════════════════════════════════
# Entity construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_point(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create a PGA2 point (grade‑1 IPNS form):
    ``x·e₁ + y·e₂ + e₀``.
    """
    if hasattr(alg, "point"):
        return alg.point(x, y)
    return alg.multivector({E1: x, E2: y, EP: 1.0, EM: 1.0})


def make_direction(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create a PGA2 direction (ideal point, grade‑1 IPNS):
    ``x·e₁ + y·e₂``.
    """
    if hasattr(alg, "direction"):
        return alg.direction(x, y)
    return alg.multivector({E1: x, E2: y})


def make_line(alg: Algebra, nx: float, ny: float, d: float = 0.0) -> MV:
    """Create a PGA2 line (grade‑1): ``nx·e₁ + ny·e₂ + d·e₀``."""
    if hasattr(alg, "line"):
        return alg.line(nx, ny, d)
    return alg.multivector({E1: nx, E2: ny, EP: d, EM: d})


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> ReflectionLine | Rotor | Translator | Motor | GeneralRotor:
    """Analyze an MV in PGA2 as a versor.

    Classification by factor count and null‑vector content (e₀):

    - 1 factor, no null   → :class:`ReflectionLine`
    - 2 factors, no null  → :class:`Rotor`
    - 2 factors, with null → :class:`Translator`
    - 2 factors, mixed    → :class:`GeneralRotor`
    - 4 factors           → :class:`Motor`
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    scale, factors = mv.blade_factorize_versor()
    _ = scale
    n = len(factors)
    has_null_flags = [_has_null(f) for f in factors]

    if n == 1:
        return _reflection_from_factor(factors[0])
    elif n == 2:
        if any(has_null_flags) and not all(has_null_flags):
            return _general_rotor_from_versor(mv)
        elif any(has_null_flags):
            return _translator_from_versor(mv)
        else:
            return _rotor_from_factors(factors[0], factors[1])
    elif n == 4:
        return _motor_from_factors(mv, factors)
    else:
        raise ValueError(f"Unexpected {n} factors for PGA2 versor")


def _reflection_from_factor(n: MV) -> ReflectionLine:
    return ReflectionLine(direction=Direction(float(n[E1]), float(n[E2]), 0.0))


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two Euclidean reflectors → rotation.

    In 2D, rotation is always about the z‑axis.
    """
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))
    axis = Direction(0, 0, 1)
    return Rotor(angle=angle, axis=axis)


def _translator_from_versor(mv: MV) -> Translator:
    """Extract translator directly from versor coefficients.

    ``T = 1 − 0.5·(dx·e₁∧e₀ + dy·e₂∧e₀)`` where
    ``e₁∧ep`` is blade 5 and ``e₁∧em`` is blade 9.
    """
    dx = -2.0 * float(mv[5])  # e1∧ep
    dy = -2.0 * float(mv[6])  # e2∧ep
    return Translator(vector=Direction(dx, dy, 0.0))


def _motor_from_factors(mv: MV, factors: list[MV]) -> Motor:
    """Four reflectors → Motor (rotation + translation)."""
    eucl = [f for f in factors if not _has_null(f)]
    null = [f for f in factors if _has_null(f)]

    if len(eucl) == 2:
        rotor = _rotor_from_factors(eucl[0], eucl[1])
    else:
        rotor = Rotor(0.0, Direction(0, 0, 1))

    translator = _translator_from_versor(mv)
    return Motor(rotor=rotor, translator=translator)


def _general_rotor_from_versor(mv: MV) -> GeneralRotor:
    """Extract a GeneralRotor from a 2‑factor versor with mixed components.

    G = T·R·T̃ has both Euclidean and null bivector parts but no grade‑3.
    In 2D, the Euclidean bivector is always e₁₂.
    """
    # Extract rotor from e₁₂ bivector component
    bz = float(mv[E12])
    b_norm = abs(bz)

    if b_norm < 1e-15:
        raise ValueError("GeneralRotor has zero Euclidean bivector part")

    scal = float(mv[0])
    if abs(scal) < 1e-15:
        raise ValueError("GeneralRotor has zero scalar component")

    angle = 2.0 * math.atan2(b_norm, scal)
    axis = Direction(0, 0, 1)

    # Extract translator from null bivector components
    dx = -2.0 * float(mv[5]) / scal  # e1∧ep
    dy = -2.0 * float(mv[6]) / scal  # e2∧ep

    return GeneralRotor(
        rotor=Rotor(angle=angle, axis=axis),
        translator=Translator(vector=Direction(dx, dy, 0.0)),
    )


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _has_euclidean(factor: MV) -> bool:
    return abs(float(factor[E1])) > 1e-15 or abs(float(factor[E2])) > 1e-15


def _has_null(factor: MV) -> bool:
    return abs(float(factor[EP])) > 1e-15 or abs(float(factor[EM])) > 1e-15


def _get_grades(mv: MV) -> set[int]:
    return set(mv.grades)
