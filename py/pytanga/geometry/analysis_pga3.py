# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA3-specific entity and operator analysis.

Implements the Gunn/Dorst plane‑based PGA model (G(3, 0, 1)) within the
5D algebra via the null‑vector embedding e₀ = ep + em.  This embedding is
necessary because TANGA does not support zero‑squaring basis vectors
natively; see ``docs/py/basis/pga_null_embedding.md`` for the
mathematical isomorphism.

Entity grades follow the Gunn/Dorst convention:
  - Plane  = grade‑1 vector   (Gunn §4.2, Dorst §3.1)
  - Line   = grade‑2 bivector (intersection of two planes)
  - Point  = grade‑3 trivector (intersection of three planes)
  - Direction = grade‑3 trivector, dual has no e₀ component

References:
  Gunn, *Geometric algebras for Euclidean geometry* (arXiv:1411.6502, 2016)
  Dorst, *A Guided Tour to the Plane‑Based Geometric Algebra PGA* (2020)
  ``docs/py/basis/pga_null_embedding.md``

The 4D dual is computed as ``mv.ip(I_4d_pinv)`` where
``I_4d = e₁∧e₂∧e₃∧e₀`` and ``I_4d_pinv`` is its pseudo‑inverse
(``I_4d.blade_pseudo_inverse()``).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._ana_versor_generic import ana_versor_generic
from ._pga3_utils import (
    E1,
    E2,
    E3,
    E12,
    E13,
    E23,
    # E123,
    EM,
    EP,
    # _get_e0,
    _get_e0_coeff,
)
from .entities import Direction, Line, Plane, Point, Space
from .operators import (
    GeneralRotor,
    Motor,
    ReflectionLine,
    ReflectionPlane,
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


def analyze_entity(mv: MV) -> Point | Direction | Line | Plane | Space | None:
    """Analyze an MV in PGA3 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.

    OPNS entities (Gunn/Dorst grades):

    - Grade 1 → :class:`Plane`
    - Grade 2 → :class:`Line`
    - Grade 3 → :class:`Point` (finite) or :class:`Direction` (ideal)
    - Grade 5 → :class:`Space`
    """
    if not mv.algebra.opns:
        return _analyze_entity_ipns(mv)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(mv: MV) -> Point | Direction | Line | Plane | Space | None:
    """OPNS entity analysis (Gunn/Dorst grades)."""
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed‑grade MV in PGA3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _plane_from_vector(mv)
    elif max_grade == 2:
        return _line_from_bivector(mv)
    elif max_grade == 3:
        return _point_from_trivector(mv)
    elif max_grade == 4:
        # I_4d = e₁∧e₂∧e₃∧e₀ (null blade → versor factorize returns 0)
        # Grade-4 components are e123p (blade 15) and e123m (blade 23)
        g4 = mv.grade(4)
        return Space(scale=float(g4[15]))  # e123∧ep
    else:
        raise ValueError(f"Unexpected grade {max_grade} in PGA3 OPNS")


def _analyze_entity_ipns(mv: MV) -> Point | Direction | Line | Plane | Space | None:
    """IPNS entity analysis.

    IPNS grades in Gunn/Dorst:
    - Grade 1 with e₀ → Point
    - Grade 1 without e₀ → Direction
    - Grade 2 → Line
    - Grade 3 → Plane
    - Grade 5 → Space
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed‑grade MV in PGA3 IPNS: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_from_ipns(mv)
    elif max_grade == 2:
        return _line_from_bivector(mv)  # lines are self‑dual in the 4D sense
    elif max_grade == 3:
        # IPNS trivector → dual → OPNS grade-1 vector → plane
        opns = mv.dual()
        return _plane_from_vector(opns)
    elif max_grade == 5:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in PGA3 IPNS")


def _point_or_direction_from_ipns(mv: MV) -> Point | Direction:
    """Extract Point/Direction from a grade‑1 IPNS vector.

    Finite point: ``x·e₁ + y·e₂ + z·e₃ + α·e₀`` → Point(x/α, y/α, z/α).
    Direction:    ``x·e₁ + y·e₂ + z·e₃`` (α = 0).
    """
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    z = float(g1[E3])

    # Extract homogeneous weight α algebraically
    alpha = _get_e0_coeff(mv)

    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / alpha, y=y / alpha, z=z / alpha)


# ── Grade 1: Plane ──────────────────────────────────────────


def _plane_from_vector(mv: MV) -> Plane:
    """Extract a Plane from a grade‑1 vector ``n + d·e₀``."""
    g1 = mv.grade(1)
    nx = float(g1[E1])
    ny = float(g1[E2])
    nz = float(g1[E3])
    d = float(g1[EP])  # e₀ component (same as EM)

    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero normal — not a valid plane")

    ux, uy, uz = nx / n_norm, ny / n_norm, nz / n_norm
    offset = d / n_norm  # signed distance along normal
    return Plane(
        point=Point(x=-ux * offset, y=-uy * offset, z=-uz * offset),
        normal=Direction(x=ux, y=uy, z=uz),
    )


# ── Grade 2: Line ───────────────────────────────────────────


def _line_from_bivector(mv: MV) -> Line:
    """Decompose a grade‑2 bivector → Line (intersection of 2 planes)."""
    grade2 = mv.grade(2)

    # Blade‑ness check: a simple bivector satisfies B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a line. "
            "Only simple (factorisable) bivectors represent lines in PGA3. "
            "A non‑simple bivector is a screw/motor bivector; use analyze_operator instead."
        )

    factors = grade2.blade_factorize()

    if len(factors) < 2:
        raise ValueError(f"Expected 2 plane factors for line, got {len(factors)}")

    # Interpret each factor as a plane vector
    p1 = _plane_from_vector(factors[0])
    p2 = _plane_from_vector(factors[1])

    # Line direction = cross product of plane normals
    dx = p1.normal.y * p2.normal.z - p1.normal.z * p2.normal.y
    dy = p1.normal.z * p2.normal.x - p1.normal.x * p2.normal.z
    dz = p1.normal.x * p2.normal.y - p1.normal.y * p2.normal.x
    d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d_norm < 1e-15:
        raise ValueError("Parallel planes — degenerate line")

    direction = Direction(dx / d_norm, dy / d_norm, dz / d_norm)

    # Closest point to origin on the intersection
    origin = _line_origin_from_planes(p1, p2)
    return Line(origin=origin, direction=direction)


def _line_origin_from_planes(p1: Plane, p2: Plane) -> Point:
    """Closest point to origin on the intersection of two planes."""
    n1x, n1y, n1z = p1.normal.x, p1.normal.y, p1.normal.z
    n2x, n2y, n2z = p2.normal.x, p2.normal.y, p2.normal.z
    d1 = -(n1x * p1.point.x + n1y * p1.point.y + n1z * p1.point.z)
    d2 = -(n2x * p2.point.x + n2y * p2.point.y + n2z * p2.point.z)

    # Direction = n1 × n2
    dx = n1y * n2z - n1z * n2y
    dy = n1z * n2x - n1x * n2z
    dz = n1x * n2y - n1y * n2x

    # Solve:  n1·p = d1, n2·p = d2,  dir·p = 0  (closest to origin)
    det = dx * dx + dy * dy + dz * dz
    if det < 1e-15:
        return Point(0, 0, 0)

    # Cramer's rule for the 3×3 system
    # | n1x n1y n1z |   |x|   |d1|
    # | n2x n2y n2z | · |y| = |d2|
    # | dx  dy  dz  |   |z|   |0 |
    detx = (
        d1 * (n2y * dz - n2z * dy)
        - n1y * (d2 * dz - n2z * 0)
        + n1z * (d2 * dy - n2y * 0)
    )
    dety = (
        n1x * (d2 * dz - n2z * 0)
        - d1 * (n2x * dz - n2z * dx)
        + n1z * (n2x * 0 - d2 * dx)
    )
    detz = (
        n1x * (n2y * 0 - d2 * dy)
        - n1y * (n2x * 0 - d2 * dx)
        + d1 * (n2x * dy - n2y * dx)
    )

    return Point(detx / det, dety / det, detz / det)


# ── Grade 3: Point / Direction ───────────────────────────────


def _point_from_trivector(mv: MV) -> Point | Direction:
    """Extract a Point or Direction from a grade‑3 trivector.

    The dual of a point trivector is ``x·e₁ + y·e₂ + z·e₃ + α·e₀``
    for a finite point, or ``x·e₁ + y·e₂ + z·e₃`` for a direction.
    """
    dual = mv.dual()  # grade‑1 vector (global sign divides out)

    x = float(dual[E1])
    y = float(dual[E2])
    z = float(dual[E3])

    # Extract homogeneous weight α algebraically
    alpha = _get_e0_coeff(dual)

    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / alpha, y=y / alpha, z=z / alpha)


# ═══════════════════════════════════════════════════════════════
# Entity construction (factory helpers)
# ═══════════════════════════════════════════════════════════════


def make_point(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create a PGA3 point (grade‑1 IPNS form):
    ``x·e₁ + y·e₂ + z·e₃ + e₀``.
    """
    return alg.multivector({E1: x, E2: y, E3: z, EP: 1.0, EM: 1.0})


def make_direction(alg: Algebra, x: float, y: float, z: float) -> MV:
    """Create a PGA3 direction (ideal point, grade‑1 IPNS):
    ``x·e₁ + y·e₂ + z·e₃``.
    """
    return alg.multivector({E1: x, E2: y, E3: z})


def make_plane(alg: Algebra, nx: float, ny: float, nz: float, d: float = 0.0) -> MV:
    """Create a PGA3 plane (grade‑1): ``nx·e₁ + ny·e₂ + nz·e₃ + d·e₀``."""
    return alg.multivector({E1: nx, E2: ny, E3: nz, EP: d, EM: d})


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> (
    ReflectionLine
    | ReflectionPlane
    | ReflectionPoint
    | Rotor
    | Translator
    | Motor
    | GeneralRotor
    | TripleReflection
):
    """Analyze an MV in PGA3 as a versor.

    Single-grade pure blades are the entity OPNS blades themselves:
    - Grade 1 -> Plane  -> ReflectionPlane
    - Grade 2 -> Line   -> ReflectionLine
    - Grade 3 -> Point  -> ReflectionPoint

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
    if isinstance(entity, Plane):
        return ReflectionPlane(entity)
    elif isinstance(entity, Line):
        return ReflectionLine(entity)
    elif isinstance(entity, Point):
        return ReflectionPoint(entity)
    raise ValueError(f"Entity type {type(entity).__name__} has no reflection operator")


def _triple_reflection_from_factors(factors):
    """Three plane reflections -> TripleReflection."""
    planes = tuple(_plane_from_vector(f) for f in factors)
    return TripleReflection(planes=planes)


def _ana_versor(
    mv: MV,
) -> Rotor | Translator | Motor | GeneralRotor:
    """Analyze a PGA3 versor by grade content.

    Delegates to the generic :func:`ana_versor_generic` with PGA3 parameters:
    ``einf_like = e0``, ``e0_inv_like = e0_inv``.
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
        is_2d=False,
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


def analyze_plane(mv: MV) -> Plane:
    """Interpret *mv* as a :class:`Plane` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Plane)


def analyze_space(mv: MV) -> Space:
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode.

    Raises ``TypeError`` if the MV represents a different entity.
    """
    return _expect(analyze_entity(mv), Space)
