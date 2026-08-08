# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Conformal Space".

"""N2-specific entity and operator analysis (full conformal 2D model).

Uses algebraic extraction via ``e∞·e₀ = −1``:
    - e∞ coefficient of *mv*: ``−mv·e₀``
    - e₀ coefficient of *mv*: ``−mv·e∞``

Mirrors ``analysis_n3.py`` with 2D blade IDs and entities.
No raw EP/EM blade IDs are used.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._ana_versor_generic import ana_versor_generic
from ._n2_helpers import (
    E1,
    E2,
    E12,
    E_coefficient,
    bivec_has_null,
    einf_coeff,
    eo_coeff,
    eucl_part,
    get_einf,
    get_eo,
    has_E_component,
    has_translator_components,
    translator_coeffs,
)
from .entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Point,
    PointPair,
    Space,
    Sphere,
)
from .operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionOrigin,
    Rotor,
    Translator,
    VersorFactors,
)

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


# ═══════════════════════════════════════════════════════════════
# Entity detection
# ═══════════════════════════════════════════════════════════════


def analyze_entity(
    mv: MV,
    *,
    opns: bool = True,
) -> Point | Direction | PointPair | HPoint | Line | Circle | Sphere | Space | None:
    """Analyze an MV in N2 as a geometric entity.

    Returns ``None`` if the null-space of the MV (in the requested OPNS/IPNS
    interpretation) is empty.

    In 2D conformal geometry, a "sphere" is a circle and a "plane" is a
    line.  Entity naming follows what the entity looks like in 2D.
    """
    if not opns:
        dual = mv.dual()
        return _analyze_entity_opns(dual)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(
    mv: MV,
) -> Point | Direction | PointPair | HPoint | Line | Circle | Sphere | Space | None:
    if mv.is_zero:
        raise ValueError("Zero MV is not a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV is not a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in N2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_n2(mv)
    elif max_grade == 2:
        return _decompose_grade2(mv)
    elif max_grade == 3:
        return _line_or_circle_n2(mv)
    elif max_grade == 4:
        return _sphere_or_line_n2(mv)
    else:
        raise ValueError(f"Unexpected grade {max_grade} in N2")


# ── Grade 1: Point / Direction ────────────────────────────────


def _point_or_direction_n2(mv: MV) -> Point | Direction | None:
    """Analyze a grade-1 OPNS blade as a conformal point or direction.

    An OPNS point blade has the form ``Cop(p) = p + ½‖p‖²·e∞ + e₀``.
    After normalizing by the e₀ coefficient, the e∞ coefficient must
    equal ``½‖p‖²``.  If this constraint is violated, the blade does
    not represent a valid OPNS point (null-space is empty) and
    ``None`` is returned.
    """
    einf = get_einf(mv.algebra)
    eo = get_eo(mv.algebra)
    f_eo = eo_coeff(mv, einf)
    if abs(f_eo) < 1e-10:
        return Direction(x=float(mv[E1]), y=float(mv[E2]), z=0.0)

    px = float(mv[E1]) / f_eo
    py = float(mv[E2]) / f_eo

    # Validate: normalized blade must have einf coeff = ½‖p‖²
    einf_c = einf_coeff(mv, eo) / f_eo
    expected_einf = 0.5 * (px * px + py * py)
    if abs(einf_c - expected_einf) > 1e-10:
        return None

    return Point(x=px, y=py, z=0.0)


# ── Grade 2: PointPair / HPoint ────────────────────


def _decompose_grade2(mv: MV) -> PointPair | HPoint:
    """Analyze a grade‑2 OPNS blade (mirrors N3 _decompose_grade2).

    Perwass, GAConfSpc_Ana.tex §PointPair (adapted for 2D):
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)

    # ── HPoint check: Q = P∧e∞ → Q∧e∞ = 0 ──
    if mv.op(einf).is_zero:
        weight = float(mv.sp(einf.op(eo)))
        return HPoint(point=_factor_to_point(mv, alg), weight=weight)

    # ── 1. Line through the point pair ──
    L = mv.op(einf)  # grade 3 OPNS
    if L.is_zero:
        raise ValueError("Degenerate point pair line")

    # ── 2. Perpendicular bisector: P* = Q·e∞ ──
    P_star = mv.ip(einf)  # grade 1 IPNS (line through origin)
    if P_star.is_zero:
        raise ValueError("Degenerate point pair bisector")

    # ── 3. Midpoint: X = P*·L ──
    X = P_star.ip(L)
    center = _factor_to_point(X, alg)

    # ── 4. Direction from line ──
    E = einf.op(eo)  # e∞∧e₀ (grade 2)
    d = L.ip(E)  # grade 1 direction
    if d.is_zero:
        raise ValueError("Point pair direction is zero")
    direction = Direction(float(d[E1]), float(d[E2]), 0.0)

    # ── 5. Point separation: S* = Q·L⁻¹ ──
    L_inv = L.inv()
    S_star = mv.ip(L_inv)
    r_sq = float(S_star.sp(S_star))  # (d/2)², may be negative
    separation = 2.0 * math.sqrt(abs(r_sq))
    is_imaginary = r_sq < 0

    half_dist = separation * 0.5
    return PointPair(
        point_a=Point(
            center.x - direction.x * half_dist,
            center.y - direction.y * half_dist,
            0.0,
        ),
        point_b=Point(
            center.x + direction.x * half_dist,
            center.y + direction.y * half_dist,
            0.0,
        ),
        is_imaginary=is_imaginary,
        _center=center if is_imaginary else None,
        _direction=direction if is_imaginary else None,
        _separation=separation if is_imaginary else None,
    )


# ── Grade 3: Line / Circle ────────────────────────────────────


def _line_or_circle_n2(mv: MV) -> Line | Circle:
    """Distinguish Line vs Circle via C∧e∞.

    For a grade‑3 OPNS blade *C*:
      - *C*∧*e∞* = 0  → **line** (contains *e∞*).
      - *C*∧*e∞* ≠ 0  → **circle** (no *e∞* factor).
    """
    einf = get_einf(mv.algebra)
    if mv.op(einf).is_zero:
        return _decompose_line(mv)
    return _decompose_circle(mv)


def _decompose_line(mv: MV) -> Line:
    """Line parameter extraction (Perwass, adapted for 2D).

    Given an OPNS line L (grade 3):
       d = L · (e∞∧e₀)  → direction vector (grade 1)
       X = d · L         → point on line closest to origin
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)

    # Direction: d = L·(e∞∧e₀) = L·E  (grade 1)
    E = einf.op(eo)  # grade 2   (e∞∧e₀)
    d = mv.ip(E)  # grade 1   direction
    if d.is_zero:
        raise ValueError("Line direction is zero")

    # Normalize direction
    dx, dy = float(d[E1]), float(d[E2])
    d_norm = math.sqrt(dx * dx + dy * dy)
    if d_norm < 1e-15:
        raise ValueError("Line direction is zero")

    # Closest point to origin: X = d·L  (grade 1 homogeneous point)
    X = d.ip(mv)
    pt = _factor_to_point(X, alg)
    return Line(
        origin=pt,
        direction=Direction(dx / d_norm, dy / d_norm, 0.0),
    )


def _decompose_circle(mv: MV) -> Circle:
    """Circle parameter extraction (Perwass, adapted for 2D).

    In 2D, a "circle" has no plane normal — the circle lies in the
    XY plane by definition.  The axis is Dir(0,0,1).
    """
    alg = mv.algebra
    einf = get_einf(alg)

    # ── 1. "Plane" of circle (line through centre in 2D) ──
    P = mv.op(einf)  # grade 4 (in 2D this is a line IPNS)
    if P.is_zero:
        raise ValueError("Degenerate circle: no line factor")

    # ── 2. IPNS circle ──
    C_star = mv.dual()  # grade 1

    # ── 3. Centre: extract from IPNS circle ──
    # C* = Cop(c) − ½r²·e∞.  e₀ component gives homogeneous weight.
    f_eo = eo_coeff(C_star, einf)
    if abs(f_eo) < 1e-15:
        raise ValueError("Degenerate circle: no e₀ component in IPNS")
    pt = Point(float(C_star[E1]) / f_eo, float(C_star[E2]) / f_eo, 0.0)

    # ── 4. Radius: from C*·C* ──
    r_sq = float(C_star.sp(C_star))
    is_imaginary = r_sq < 0
    radius = math.sqrt(abs(r_sq))

    # ── 5. Normal: always Dir(0,0,1) in 2D (perpendicular to XY plane) ──
    normal = Direction(0.0, 0.0, 1.0)

    return Circle(center=pt, normal=normal, radius=radius, is_imaginary=is_imaginary)


# ── Grade 4: Sphere (circle) / Line (IPNS dual) ────────────────


def _sphere_or_line_n2(mv: MV) -> Sphere | Line:
    """Distinguish Circle (Sphere) vs Line via dual IPNS analysis.

    In the IPNS (dual):
    - Line (IPNS): L = â + α·e∞  (no e₀ component) → re-dualize to OPNS line
    - Sphere (circle): S = Cop(c) − ½r²·e∞  (has e₀ component)
    """
    ipns = mv.dual()
    if ipns.is_zero:
        raise ValueError("Zero dual – not a valid entity")

    einf = get_einf(mv.algebra)
    eo = get_eo(mv.algebra)

    eo_c = eo_coeff(ipns, einf)
    if abs(eo_c) > 1e-10:
        return _sphere_from_ipns(ipns, einf, eo)
    else:
        return _line_from_ipns_opns(mv, ipns, einf, eo)


def _line_from_ipns_opns(mv: MV, ipns: MV, einf: MV, eo: MV) -> Line:
    """Extract a Line from a grade-4 OPNS blade whose dual is an IPNS line.

    In 2D, a grade-4 blade is the OPNS line (contains e∞ factor).
    We use the same extraction as grade-3 OPNS line, or extract from
    IPNS via dual re‑interpretation.
    """
    # Dual is IPNS: L = â + α·e∞ (no e₀)
    # Recover OPNS by wedging two points on the line
    # Extract normal and offset from IPNS
    ex, ey = float(ipns[E1]), float(ipns[E2])
    n_norm = math.sqrt(ex * ex + ey * ey)
    if n_norm < 1e-15:
        raise ValueError("Zero normal in IPNS line")
    ux, uy = ex / n_norm, ey / n_norm

    # e∞ coefficient = sp(ipns, eo) (via reciprocal)
    einf_c = -float(ipns.sp(eo))
    d = einf_c / n_norm  # signed distance from origin

    # Point on line = −d·â (closest point to origin)
    origin = Point(ux * d, uy * d, 0.0)

    # Direction is perpendicular to normal
    direction = Direction(-uy, ux, 0.0)

    return Line(origin=origin, direction=direction)


def _sphere_from_ipns(ipns: MV, einf: MV, eo: MV) -> Sphere:
    """Perwass: S̃ = α(A − ½r²·e∞) → extract center and radius.

    In 2D, a "sphere" entity represents a circle.
    """
    einf_sp = float(ipns.sp(einf))
    if abs(einf_sp) < 1e-10:
        raise ValueError("Circle IPNS has zero einf component – not a circle")
    norm = -einf_sp
    ex, ey = float(ipns[E1]) / norm, float(ipns[E2]) / norm

    s_normalized = ipns * (1.0 / norm)
    r_sq = float(s_normalized.sp(s_normalized))
    if r_sq < 0:
        return Sphere(
            center=Point(ex, ey, 0.0), radius=math.sqrt(-r_sq), is_imaginary=True
        )
    return Sphere(center=Point(ex, ey, 0.0), radius=math.sqrt(r_sq))


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> (
    ReflectionLine
    | ReflectionOrigin
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
):
    """Analyze an MV in N2 as a versor.

    Classification follows Perwass table (adapted for 2D):
    - Reflection: grade-1, only Euclidean
    - ReflectionOrigin: grade-1, only e₀
    - Inversion: grade-1, Euclidean + e₀ + e∞ (circle IPNS)
    - Rotor: grades {0,2}, only e₁₂ bivector
    - Translator: grades {0,2}, eᵢ∧e∞ bivectors
    - Dilator: grades {0,2}, only e∞∧e₀
    - GeneralDilator: grades {0,2}, eᵢ∧e∞ AND e∞∧e₀
    - Motor: grades {0,2,3}
    - GeneralRotor: grades {0,2} with eᵢ∧e∞
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    einf = get_einf(mv.algebra)
    eo = get_eo(mv.algebra)
    grades = _get_grades(mv)

    # Pure-grade single blade → Reflection family
    if len(grades) == 1:
        return _classify_single_grade_versor(mv, einf, eo)

    # Multivector versor
    scale, factors = mv.blade_factorize_versor()
    _ = scale
    n = len(factors)

    if n == 1:
        return _classify_single_reflector(factors[0], einf, eo)
    elif n == 2:
        return _classify_double_reflector(mv, einf, eo, factors)
    elif n == 4:
        return _classify_quad_reflector(mv, einf, eo, factors)
    else:
        return VersorFactors(factors=tuple(factors))


def _classify_single_grade_versor(mv: MV, einf: MV, eo: MV):
    """Pure-grade blade: distinguish by algebraic components."""
    grades = _get_grades(mv)
    max_grade = max(grades)

    if max_grade == 1:
        ex, ey = eucl_part(mv, einf, eo)
        eucl_norm = math.sqrt(ex * ex + ey * ey)
        einf_c = einf_coeff(mv, eo)
        eo_c = eo_coeff(mv, einf)

        if eucl_norm < 1e-10 and abs(eo_c) < 1e-10 and abs(einf_c) < 1e-10:
            raise ValueError("Zero versor")

        # Has e₀ component → circle IPNS → Inversion or ReflectionOrigin
        if abs(eo_c) > 1e-10:
            # ReflectionOrigin: only e₀, no Euclidean, no e∞
            if eucl_norm < 1e-10 and abs(einf_c) < 1e-10:
                return ReflectionOrigin()
            # Inversion: circle IPNS S = Cop(c) − ½r²·e∞
            f_eo = eo_c
            px = ex / f_eo if abs(f_eo) > 1e-10 else 0.0
            py = ey / f_eo if abs(f_eo) > 1e-10 else 0.0
            r_sq = float(mv.sp(mv))
            radius = math.sqrt(abs(r_sq)) if abs(r_sq) > 1e-10 else 1.0
            return Inversion(center=Point(px, py, 0.0), radius=radius)

        # No e₀ → line IPNS → ReflectionLine (line through origin)
        if eucl_norm < 1e-10:
            raise ValueError("Zero normal in reflection versor")
        return ReflectionLine(direction=Direction(ex / eucl_norm, ey / eucl_norm, 0.0))
    elif max_grade == 2:
        # ReflectionLine (bivector): mv = d∧e∞ where d is Euclidean.
        inner = mv.ip(eo)
        dx, dy = -float(inner[E1]), -float(inner[E2])
        d_norm = math.sqrt(dx * dx + dy * dy)
        if d_norm < 1e-15:
            raise ValueError("Zero direction in ReflectionLine versor")
        return ReflectionLine(direction=Direction(dx / d_norm, dy / d_norm, 0.0))
    raise ValueError(f"Unexpected single-grade versor grade {max_grade}")


def _classify_single_reflector(n: MV, einf: MV, eo: MV):
    return _classify_single_grade_versor(n, einf, eo)


def _classify_double_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    """Classify 2-factor versor by blade components.

    - E-only (e∞∧e₀) → Dilator (possibly with origin)
    - Everything else → delegated to :func:`ana_versor_generic`
      (handles Rotor / Translator / GeneralRotor).
    """
    has_E = has_E_component(mv, mv.algebra)

    if has_E:
        return _dilator_from_versor(mv)
    else:
        # Rotor, Translator, or GeneralRotor
        return ana_versor_generic(
            mv,
            einf_like=einf,
            e0_inv_like=-eo,
            blade_order_sign=-1,
            is_2d=True,
        )


def _classify_quad_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    """Classify a 4-factor versor: Motor or GeneralRotor.

    Delegates to :func:`ana_versor_generic` which classifies by grade
    content (grade-3 → Motor in 2D, no grade-3 → GeneralRotor).
    """
    return ana_versor_generic(
        mv,
        einf_like=einf,
        e0_inv_like=-eo,
        blade_order_sign=-1,
        is_2d=True,
    )


# ── Operator helpers ──────────────────────────────────────────


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))
    axis = Direction(0, 0, 1)  # 2D rotation always about z-axis
    return Rotor(angle=angle, axis=axis)


def _translator_from_versor(mv: MV) -> Translator:
    """Extract translation vector using algebraic eᵢ∧e₀ inner product."""
    dx, dy = translator_coeffs(mv, mv.algebra)
    return Translator(vector=Direction(dx, dy, 0.0))


def _dilator_from_versor(mv: MV) -> Dilator:
    """Extract factor and origin from a dilator MV via algebraic extraction.

    Uses left-contraction with E = e∞∧e₀ and ip-op-op-ip chain
    (see dev/src/entities_04.py).  No blade factorization needed.

    Pure dilator:   origin defaults to (0,0,0).
    General dilator (T·D·T̃): origin extracted from translator part.
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)
    E = einf.op(eo)  # e∞∧e₀

    # Extract scalar D part: d_part = mv | E
    d_part = mv.ip(E)
    D_val = float(d_part[0])
    if abs(D_val) < 1e-15:
        raise ValueError("Degenerate dilator: D coefficient is zero")

    # Extract translator part: t_part = mv.ip(eo).op(eo).ip(einf)
    t_part = mv.ip(eo).op(eo).ip(einf)
    t_euc = t_part * (-1.0 / D_val)

    factor = (1.0 - D_val) / (1.0 + D_val)
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")

    # Determine if general dilator (has non-zero translator part)
    tx = float(t_euc[E1])
    ty = float(t_euc[E2])
    t_norm = math.sqrt(tx * tx + ty * ty)

    if t_norm < 1e-10:
        return Dilator(factor=factor)
    else:
        return Dilator(factor=factor, origin=Point(tx, ty, 0.0))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _get_grades(mv: MV) -> set[int]:
    return set(mv.grades)


def _factor_to_point(factor: MV, alg: Algebra) -> Point:
    """Extract a Euclidean point from a homogeneous point blade.

    Supports two forms:
      - Grade 1  (standard form):  X = x + s·e∞ + e₀
      - Grade 2  (from P*·L):     X = x^i e_i e∞ + s e∞ e₀
    """
    einf = get_einf(alg)
    eo = get_eo(alg)

    grades = _get_grades(factor)
    if 1 in grades:
        # Grade-1 homogeneous point
        f_eo = eo_coeff(factor, einf)
        if abs(f_eo) < 1e-15:
            return Point(float(factor[E1]), float(factor[E2]), 0.0)
        return Point(
            x=float(factor[E1]) / f_eo,
            y=float(factor[E2]) / f_eo,
            z=0.0,
        )

    # Grade-2 homogeneous point (from circle centre)
    p = factor.ip(eo)  # grade 1: Euclidean point up to scale
    s = -float(p.sp(einf))  # scale factor
    if abs(s) < 1e-15:
        return Point(float(p[E1]), float(p[E2]), 0.0)
    return Point(
        x=float(p[E1]) / s,
        y=float(p[E2]) / s,
        z=0.0,
    )
