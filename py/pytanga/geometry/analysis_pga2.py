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


def analyze_entity(
    mv: MV, *, opns: bool = True
) -> Point | Direction | Line | Space | None:
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
) -> ReflectionLine | Rotor | Translator | Motor | GeneralRotor | TripleReflection:
    """Analyze an MV in PGA2 as a versor.

    Classification by grade content (not blade factorization):

    - 1 factor  → :class:`ReflectionLine`
    - 3 factors → :class:`TripleReflection`
    - All others → delegated to :func:`_ana_versor` which classifies by
      grade content (no Euclidean bivector → Translator, Euclidean only
      → Rotor, both → GeneralRotor).

    Note: in 2D PGA there is no Motor because translations are always
    in the rotation plane.
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    try:
        scale, factors = mv.blade_factorize_versor()
    except Exception as exc:
        raise ValueError(
            "MV is not a versor — cannot be factorized into grade-1 vectors"
        ) from exc

    _ = scale
    n = len(factors)

    if n == 1:
        return _reflection_from_factor(factors[0])
    elif n == 3:
        return _triple_reflection_from_factors(factors)
    else:
        # Pre-filter: pure bivector with no scalar → ReflectionLine (d∧e₀)
        # This has null bivector content but no Euclidean bivector and no scalar
        s_val = float(mv[0]) if not mv.grade(0).is_zero else 0.0
        if abs(s_val) < 1e-15:
            has_null = _versor_has_null_part(mv)
            has_eucl = _versor_has_euclidean_bivector(mv)
            if has_null and not has_eucl:
                return _reflection_line_from_bivector(mv)
            # Pure Euclidean bivector (no scalar, no null) → 180° rotation
            if has_eucl and not has_null:
                return Rotor(angle=math.pi, axis=Direction(0, 0, 1))
            raise ValueError("Unrecognized pure‑bivector versor in PGA2")
        # 2 or 4+ factors with scalar: classify by grade content
        return _ana_versor(mv)


def _triple_reflection_from_factors(factors: list[MV]) -> TripleReflection:
    """Three line reflections → TripleReflection.

    The three factors are grade-1 vectors encoding lines.
    We convert them to Line entities and return the triple reflection.
    """
    lines = tuple(_line_from_vector(f) for f in factors)
    return TripleReflection(planes=lines)  # type: ignore[arg-type]


def _reflection_from_factor(n: MV) -> ReflectionLine:
    return ReflectionLine(direction=Direction(float(n[E1]), float(n[E2]), 0.0))


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


def _versor_has_null_part(mv: MV) -> bool:
    """Return True if V · e0_inv contains Euclidean vector parts (E1/E2)."""
    e0_inv = (
        mv._alg.e0_inv
        if hasattr(mv._alg, "e0_inv")
        else mv._alg.multivector({EP: 0.5, EM: -0.5})
    )
    result = mv.ip(e0_inv)
    return abs(float(result[E1])) > 1e-15 or abs(float(result[E2])) > 1e-15


def _versor_has_euclidean_bivector(mv: MV) -> bool:
    """Return True if V ^ e0 contains grade > 1 content."""
    e0 = (
        mv._alg.e0
        if hasattr(mv._alg, "e0")
        else mv._alg.multivector({EP: 1.0, EM: 1.0})
    )
    wedge = mv.op(e0)
    grades = _get_grades(wedge)
    return any(g > 1 for g in grades)


def _reflection_line_from_bivector(mv: MV) -> ReflectionLine:
    """Extract ReflectionLine from a pure null bivector ``d∧e₀``.

    The bivector has no scalar part; components are e1∧ep (blade 5),
    e1∧em (blade 9), e2∧ep (blade 6), e2∧em (blade 10).
    """
    dx = float(mv[5])  # e1∧ep
    dy = float(mv[6])  # e2∧ep
    return ReflectionLine(direction=Direction(dx, dy, 0.0))


def _get_grades(mv: MV) -> set[int]:
    return set(mv.grades)
