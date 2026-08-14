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

from ._ana_versor_generic import ana_versor_generic
from ._pga2_utils import (
    E1,
    E2,
    E12,
    EM,
    EP,
    _get_e0_coeff,
)
from .entities import Direction, Line, Point, Space
from .operators import (
    GeneralRotor,
    Motor,
    ReflectionLine,
    ReflectionPoint,
    Rotor,
    Translator,
    TripleReflection,
)

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(mv: MV) -> Point | Direction | Line | Space | None:
    """Analyze an MV in PGA2 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    OPNS entities (Gunn/Dorst grades, 2D):

    - Grade 1 → :class:`Line`
    - Grade 2 → :class:`Point`
    - Grade 3 → :class:`Space` (pseudoscalar) or :class:`Direction`
    """
    if not mv.algebra.opns:
        return _analyze_entity_ipns(mv)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv: MV) -> Point | Direction | Line | Space | None:
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


def _analyze_entity_ipns(mv: MV) -> Point | Direction | Line | Space | None:
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
        opns = mv.dual()
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


def _point_from_bivector(mv: MV) -> Point | Direction:
    """Decompose a grade‑2 bivector → Point or Direction via PGA2 dual.

    In 2D PGA a grade‑2 OPNS blade represents a point or ideal point.
    The PGA2 dual gives a grade‑1 IPNS vector ``p₁e₁ + p₂e₂ + αe₀``.
    If α ≠ 0 → finite ``Point(p₁/α, p₂/α)``.
    If α = 0 → ideal ``Direction(p₁, p₂)``.
    """
    ipns = mv.dual()
    return _point_or_direction_from_ipns(ipns)


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
    dual = mv.dual()  # global sign divides out

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
    return alg.multivector({E1: x, E2: y, EP: 1.0, EM: 1.0})


def make_direction(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create a PGA2 direction (ideal point, grade‑1 IPNS):
    ``x·e₁ + y·e₂``.
    """
    return alg.multivector({E1: x, E2: y})


def make_line(alg: Algebra, nx: float, ny: float, d: float = 0.0) -> MV:
    """Create a PGA2 line (grade‑1): ``nx·e₁ + ny·e₂ + d·e₀``."""
    return alg.multivector({E1: nx, E2: ny, EP: d, EM: d})


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> (
    ReflectionLine
    | ReflectionPoint
    | Rotor
    | Translator
    | Motor
    | GeneralRotor
    | TripleReflection
):
    """Analyze an MV in PGA2 as a versor.

    Single-grade pure blades are the entity OPNS blades themselves:
    - Grade 1 -> Line  -> ReflectionLine
    - Grade 2 -> Point -> ReflectionPoint

    Multi-grade versors are classified by factorization.
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    grades = _get_grades(mv)

    # Single-grade pure blade -> entity -> operator wrapper
    if len(grades) == 1:
        entity = _analyze_entity_opns(mv)
        return _entity_to_operator(entity)

    # Multi-grade versor -> factorization
    try:
        scale, factors = mv.blade_factorize_versor()
    except Exception:
        raise ValueError("MV is not a valid versor")

    n = len(factors)
    if n == 3:
        return _triple_reflection_from_factors(factors)
    else:
        return _ana_versor(mv)


def _entity_to_operator(entity):
    """Wrap an entity as its corresponding reflection operator."""
    if isinstance(entity, Line):
        return ReflectionLine(line=entity)
    elif isinstance(entity, Point):
        return ReflectionPoint(point=entity)
    raise ValueError(
        f"Entity type {type(entity).__name__} has no reflection operator"
    )


def _triple_reflection_from_factors(factors):
    """Three line reflections -> TripleReflection."""
    lines = tuple(_line_from_vector(f) for f in factors)
    return TripleReflection(planes=lines)

def _ana_versor(
    mv: MV,
) -> Rotor | Translator | GeneralRotor:
    """Analyze a PGA2 versor by grade content.

    Delegates to the generic :func:`ana_versor_generic` with PGA2 parameters:
    ``einf_like = e0``, ``e0_inv_like = e0_inv``, ``is_2d = True``.
    """
    alg = mv._alg
    e0 = alg.e0 if hasattr(alg, "e0") else alg.multivector({EP: 1.0, EM: 1.0})
    e0_inv = (
        alg.e0_inv if hasattr(alg, "e0_inv") else alg.multivector({EP: 0.5, EM: -0.5})
    )
    return ana_versor_generic(
        mv,
        einf_like=e0,
        e0_inv_like=e0_inv,
        is_2d=True,
    )


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _get_grades(mv: MV) -> set[int]:
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
