# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Projective Space".

"""P3-specific entity and operator analysis.

Uses :meth:`~pytanga.MV.blade_factorize` and
:meth:`~pytanga.MV.blade_factorize_versor` for decomposition.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pytanga.basis.p3 import BasisP3

from .entities import Direction, Line, Plane, Point, Space
from .operators import ReflectionLine, ReflectionPlane, ReflectionPoint, Rotor

if TYPE_CHECKING:
    from pytanga.algebra._mv import MV

# Blade IDs — sourced from BasisP3 as single source of truth.
# Module-level aliases exist for backward compatibility with
# code that imports them directly.  Prefer basis.E12 for new code.
E1 = BasisP3.E1
E2 = BasisP3.E2
E3 = BasisP3.E3
E4 = BasisP3.E4
E12 = BasisP3.E12
E13 = BasisP3.E13
E23 = BasisP3.E23
E14 = BasisP3.E14
E24 = BasisP3.E24
E34 = BasisP3.E34


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(
    mv: MV, *, opns: bool = True
) -> Point | Direction | Line | Plane | Space | None:
    """Analyze an MV in P3 as a geometric entity.

    Parameters
    ----------
    mv : MV
        A multivector to analyze.
    opns : bool, optional
        *True* (default) → OPNS interpretation.
        *False* → IPNS interpretation (dualizes to OPNS first).

    P3 OPNS entities (pure-grade blades):

    - Grade 1 → :class:`Point` (e4 ≠ 0) or :class:`Direction` (e4 = 0)
    - Grade 2 → :class:`Line` (2 homogeneous point factors)
    - Grade 3 → :class:`Plane` (dual gives normal + offset)
    - Grade 4 → :class:`Space` (pseudoscalar)
    """
    if not opns:
        dual = mv.dual()
        return _analyze_entity_opns(dual)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(
    mv: MV,
) -> Point | Direction | Line | Plane | Space | None:
    """OPNS entity analysis."""
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in P3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_from_coeffs(mv)
    elif max_grade == 2:
        return _line_from_factors(mv)
    elif max_grade == 3:
        return _plane_from_trivector(mv)
    elif max_grade == 4:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=float(scale[0]))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in P3")


def _point_or_direction_from_coeffs(mv: MV) -> Point | Direction:
    """Read a grade-1 blade directly from coefficients."""
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    z = float(g1[E3])
    w = float(g1[E4])

    if abs(x) < 1e-15 and abs(y) < 1e-15 and abs(z) < 1e-15:
        if abs(w) < 1e-15:
            raise ValueError("Zero MV — not a point or direction")
        # All Euclidean components zero but e₄ ≠ 0 → only e₄ vector
        raise ValueError("MV has only e₄ component — not a point or direction in P3")

    if abs(w) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / w, y=y / w, z=z / w)


def _line_from_factors(mv: MV) -> Line:
    """Factorise a grade-2 blade → direction + point on line.

    With the new ``Hop(a)∧Hop(b)`` construction, both factors have
    e₄ ≈ 1.  The difference gives the direction; either factor
    (after dehomogenization) gives a point on the line.
    """
    grade2 = mv.grade(2)

    # Blade‑ness check: a grade-2 blade must satisfy B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a line blade. "
            "(Bivector has non‑zero grade‑4 part: B∧B ≠ 0. "
            "Only simple (factorisable) bivectors represent lines in P3.)"
        )

    factors = grade2.blade_factorize()

    f0 = factors[0]
    f1 = factors[1]

    # Dehomogenize both factors
    w0 = float(f0[E4])
    w1 = float(f1[E4])

    if abs(w0) < 1e-15 or abs(w1) < 1e-15:
        # Fallback: one factor is a direction vector
        if abs(w0) < abs(w1):
            d_factor, p_factor = f0, f1
        else:
            d_factor, p_factor = f1, f0

        dx = float(d_factor[E1])
        dy = float(d_factor[E2])
        dz = float(d_factor[E3])

        pw = float(p_factor[E4])
        if abs(pw) < 1e-15:
            origin = Point(0, 0, 0)
        else:
            origin = Point(
                x=float(p_factor[E1]) / pw,
                y=float(p_factor[E2]) / pw,
                z=float(p_factor[E3]) / pw,
            )
        return Line(origin=origin, direction=Direction(x=dx, y=dy, z=dz))

    # Both factors have e₄ ≠ 0: dehomogenize to get two points
    p0 = Point(x=float(f0[E1]) / w0, y=float(f0[E2]) / w0, z=float(f0[E3]) / w0)
    p1 = Point(x=float(f1[E1]) / w1, y=float(f1[E2]) / w1, z=float(f1[E3]) / w1)

    # Direction = difference
    dx = p1.x - p0.x
    dy = p1.y - p0.y
    dz = p1.z - p0.z
    d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d_norm < 1e-15:
        raise ValueError("Degenerate line – points are identical")

    return Line(
        origin=p0,
        direction=Direction(dx / d_norm, dy / d_norm, dz / d_norm),
    )


def _plane_from_trivector(mv: MV) -> Plane:
    """Extract a Plane from a grade-3 trivector via dualisation.

    The dual of the trivector n∧e₄ gives P = â − α·e₄ (IPNS),
    where â is the unit normal and α the signed distance.
    """
    grade3 = mv.grade(3)
    # IPNS: dual gives P = â − α·e₄  (since trivector = IPNS plane ∧ e₄)
    ip_dual = grade3.dual()

    nx = float(ip_dual[E1])
    ny = float(ip_dual[E2])
    nz = float(ip_dual[E3])
    d = float(ip_dual[E4])

    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero normal – not a valid plane")

    ux = nx / n_norm
    uy = ny / n_norm
    uz = nz / n_norm
    # P = â − α·e₄ → IPNS has d = −α, so α = −d
    alpha = -d / n_norm

    # Point on plane: closest point to origin = α·â
    return Plane(
        point=Point(x=ux * alpha, y=uy * alpha, z=uz * alpha),
        normal=Direction(x=ux, y=uy, z=uz),
    )


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> ReflectionLine | ReflectionPlane | ReflectionPoint | Rotor:
    """Analyze an MV in P3 as a versor / operator.

    Reflection detection (by blade grade and e₄ component):

    - Grade 1, only e₄ → :class:`ReflectionPoint`
    - Grade 1, e₄ = 0 → :class:`ReflectionPlane`
    - Grade 2, e₄ terms present → :class:`ReflectionLine`
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
        raise ValueError(f"Versor has {len(factors)} factors – unexpected for P3")


def _classify_grade1_versor(mv: MV) -> ReflectionPlane | ReflectionPoint:
    """Grade-1 versor: determines ReflectionPlane vs ReflectionPoint.

    - Only e₄ component → ReflectionPoint.
    - Euclidean components present, e₄ = 0 → ReflectionPlane (IPNS normal).
    """
    grade1 = mv.grade(1)
    e4_val = float(grade1[E4])
    ex = float(grade1[E1])
    ey = float(grade1[E2])
    ez = float(grade1[E3])
    eucl_norm = math.sqrt(ex * ex + ey * ey + ez * ez)

    if eucl_norm < 1e-15:
        if abs(e4_val) < 1e-15:
            raise ValueError("Zero vector – not a valid versor")
        return ReflectionPoint(Point(0.0, 0.0, 0.0))
    else:
        if abs(e4_val) > 1e-15:
            raise ValueError("Mixed e₄ and Euclidean components – ambiguous P3 versor")
        return ReflectionPlane(
            normal=Direction(ex / eucl_norm, ey / eucl_norm, ez / eucl_norm)
        )


def _classify_grade2_versor(mv: MV) -> ReflectionLine:
    """Grade-2 bivector with e₄ terms → ReflectionLine.

    The bivector has form N∧e₄ with N = (nx, ny, nz).
    """
    grade2 = mv.grade(2)
    nx = float(grade2[E14])
    ny = float(grade2[E24])
    nz = float(grade2[E34])
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero direction in e₄ bivector – not a valid reflection")
    return ReflectionLine(direction=Direction(nx / n_norm, ny / n_norm, nz / n_norm))


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two reflection planes → rotation (identical logic to E3)."""
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
# Helpers
# ═══════════════════════════════════════════════════════════════


def _get_grades(mv: MV) -> set[int]:
    """Return the set of grades present in *mv*."""
    return set(mv.grades)
