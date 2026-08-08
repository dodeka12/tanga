# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Conformal Space".

"""N3-specific entity and operator analysis (full conformal model).

Uses algebraic extraction via ``e∞·e₀ = −1``:
    - e∞ coefficient of *mv*: ``−mv·e₀``
    - e₀ coefficient of *mv*: ``−mv·e∞``

No raw EP/EM blade IDs are used.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._ana_versor_generic import ana_versor_generic
from ._n3_helpers import (
    E1,
    E2,
    E3,
    E12,
    E13,
    E23,
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
    Plane,
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
    ReflectionPlane,
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
) -> (
    Point
    | Direction
    | PointPair
    | HPoint
    | Line
    | Circle
    | Plane
    | Sphere
    | Space
    | None
):
    """Analyze an MV in N3 as a geometric entity.

    Returns ``None`` if the null-space of the MV (in the requested OPNS/IPNS
    interpretation) is empty — i.e., no real Euclidean points satisfy
    the entity equation.
    """
    if not opns:
        dual = mv.dual()
        return _analyze_entity_opns(dual)
    return _analyze_entity_opns(mv)


def _analyze_entity_opns(
    mv: MV,
) -> (
    Point
    | Direction
    | PointPair
    | HPoint
    | Line
    | Circle
    | Plane
    | Sphere
    | Space
    | None
):
    if mv.is_zero:
        raise ValueError("Zero MV is not a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV is not a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in N3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_n3(mv)
    elif max_grade == 2:
        return _decompose_grade2(mv)
    elif max_grade == 3:
        return _line_or_circle_n3(mv)
    elif max_grade == 4:
        return _sphere_or_plane_n3(mv)
    elif max_grade == 5:
        scale, _ = mv.blade_factorize_versor()
        return Space(scale=abs(float(scale[0])))
    else:
        raise ValueError(f"Unexpected grade {max_grade} in N3")


# ── Grade 1: Point / Direction ────────────────────────────────


def _point_or_direction_n3(mv: MV) -> Point | Direction | None:
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
        return Direction(x=float(mv[E1]), y=float(mv[E2]), z=float(mv[E3]))

    px = float(mv[E1]) / f_eo
    py = float(mv[E2]) / f_eo
    pz = float(mv[E3]) / f_eo

    # Validate: normalized blade must have einf coeff = ½‖p‖²
    einf_c = einf_coeff(mv, eo) / f_eo
    expected_einf = 0.5 * (px * px + py * py + pz * pz)
    if abs(einf_c - expected_einf) > 1e-10:
        return None

    return Point(x=px, y=py, z=pz)


# ── Grade 2: PointPair / HPoint ────────────────────


def _decompose_grade2(mv: MV) -> PointPair | HPoint | None:
    """Analyze a grade‑2 OPNS blade.

    Perwass, GAConfSpc_Ana.tex §PointPair:
      - Check whether Q·e∞ = 0 (has pure-e∞ factor) → HPoint.
      - Otherwise:
          L = Q ∧ e∞                         → line through the points (grade 3)
          P* = Q · e∞                         → IPNS of the perpendicular bisector plane
          X = P* · L                          → midpoint (homogeneous point)
          S* = Q · L⁻¹                        → sphere at midpoint with d/2 radius
          d = 2·√|S*·S*|                      → point separation
          direction from L via L·(e∞∧e₀)
          is_imaginary ↔ S*·S* < 0  (negative squared radius)
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)

    # ── HPoint check: Q = P∧e∞ → Q∧e∞ = 0 ──
    if mv.op(einf).is_zero:
        # H = w·a∧e∞ + w·e₀∧e∞, E = e∞∧e₀, E² = -1
        # w = -H·E  (since H·E = -w)
        weight = -float(mv.sp(einf.op(eo)))
        return HPoint(point=_factor_to_point(mv, alg), weight=weight)

    # ── 1. Line through the point pair ──
    L = mv.op(einf)  # grade 3 OPNS
    if L.is_zero:
        return None

    # ── 2. Perpendicular bisector plane: P* = Q·e∞ ──
    P_star = mv.ip(einf)  # grade 1 IPNS plane
    if P_star.is_zero:
        return None

    # ── 3. Midpoint: X = P*·L ──
    X = P_star.ip(L)
    center = _factor_to_point(X, alg)

    # ── 4. Direction from line ──
    E = einf.op(eo)  # e∞∧e₀ (grade 2)
    d = L.ip(E)  # grade 1 direction
    if d.is_zero:
        return None
    dx, dy, dz = float(d[E1]), float(d[E2]), float(d[E3])
    d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d_norm < 1e-15:
        return None
    direction = Direction(dx / d_norm, dy / d_norm, dz / d_norm)

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
            center.z - direction.z * half_dist,
        ),
        point_b=Point(
            center.x + direction.x * half_dist,
            center.y + direction.y * half_dist,
            center.z + direction.z * half_dist,
        ),
        is_imaginary=is_imaginary,
        _center=center if is_imaginary else None,
        _direction=direction if is_imaginary else None,
        _separation=separation if is_imaginary else None,
    )


# ── Grade 3: Line / Circle ────────────────────────────────────


def _line_or_circle_n3(mv: MV) -> Line | Circle | None:
    """Distinguish Line vs Circle via C∧e∞.

    For a grade‑3 OPNS blade *C*:
      - *C*∧*e∞* = 0  → the entity is a **line** (contains *e∞*).
      - *C*∧*e∞* ≠ 0  → the entity is a **circle*.

    Returns ``None`` if the blade is degenerate (null-space is empty).
    """
    einf = get_einf(mv.algebra)
    if mv.op(einf).is_zero:
        return _decompose_line(mv)
    return _decompose_circle(mv)


def _decompose_line(mv: MV) -> Line | None:
    """Line parameter extraction (Perwass, GAConfSpc_Ana.tex §Line).

    Given an OPNS line L (grade 3):
       d = L · (e∞∧e₀)                       → direction vector (grade 1)
       X = d · L                              → point on line closest to origin

    Returns ``None`` if the direction is zero (null-space is empty).
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)

    # Direction: d = L·(e∞∧e₀) = L·E  (grade 1)
    E = einf.op(eo)  # grade 2   (e∞∧e₀)
    d = mv.ip(E)  # grade 1   direction
    if d.is_zero:
        return None

    # Normalize direction
    dx, dy, dz = float(d[E1]), float(d[E2]), float(d[E3])
    d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d_norm < 1e-15:
        return None

    # Closest point to origin: X = d·L  (grade 1 homogeneous point)
    X = d.ip(mv)
    pt = _factor_to_point(X, alg)
    return Line(
        origin=pt,
        direction=Direction(dx / d_norm, dy / d_norm, dz / d_norm),
    )


def _decompose_circle(mv: MV) -> Circle | None:
    """Circle parameter extraction (Perwass, GAConfSpc_Ana.tex §Circle).

    Given an OPNS circle C (grade 3):
       P  = C ∧ e∞                             → plane of the circle (grade 4)
       C* = dual(C)                             → IPNS circle (grade 2)
       L  = C* ∧ e∞                             → line through sphere centres (grade 3)
       U  = P* ·  L                             → homogeneous centre point (grade 1)
       S* = C  ·  P⁻¹                           → IPNS sphere at the centre (grade 1)
       r² = S* · S*                             → squared radius (may be negative)
       normal = Euclidean part of P* / |normal|

    Returns ``None`` if the blade is degenerate (null-space is empty).
    """
    alg = mv.algebra
    einf = get_einf(alg)

    # ── 1. Plane of circle ──
    P = mv.op(einf)  # grade 4
    if P.is_zero:
        return None

    # ── 2. IPNS circle ──
    C_star = mv.dual()  # grade 2

    # ── 3. Line through sphere centres ──
    L = C_star.op(einf)  # grade 3
    if L.is_zero:
        return None

    # ── 4. Centre point: U = P*·L ──
    P_star = P.dual()  # grade 1  IPNS plane
    U = P_star.ip(L)  # grade 1  homogeneous point
    pt = _factor_to_point(U, alg)

    # ── 5. Radius: S* = C·P⁻¹ ──
    S_star = mv.ip(P.inv())  # grade 1  IPNS sphere
    r_sq = float(S_star.sp(S_star))
    is_imaginary = r_sq < 0
    radius = math.sqrt(abs(r_sq))

    # ── 6. Normal (Euclidean part of P*) ──
    nx, ny, nz = -float(P_star[E1]), -float(P_star[E2]), -float(P_star[E3])
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        return None
    normal = Direction(nx / n_norm, ny / n_norm, nz / n_norm)

    return Circle(center=pt, normal=normal, radius=radius, is_imaginary=is_imaginary)


# ── Grade 4: Plane / Sphere ───────────────────────────────────


def _sphere_or_plane_n3(mv: MV) -> Plane | Sphere:
    """Distinguish Plane vs Sphere via dual IPNS analysis.

    In the IPNS (dual):
    - Plane: P = â + α·e∞  (no e₀ component)
    - Sphere: S = Cop(c) − ½r²·e∞  (has e₀ component)
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
        return _plane_from_ipns(ipns, einf, eo)


def _plane_from_ipns(ipns: MV, einf: MV, eo: MV) -> Plane:
    """Perwass: P̃ = α(â + d·e∞) → extract â and d.

    Uses Euclidean coefficients directly (einf/eo have zero E1/E2/E3).
    The sdual may introduce a global sign flip, so we use ratios.
    """
    ex, ey, ez = -float(ipns[E1]), -float(ipns[E2]), -float(ipns[E3])
    n_norm = math.sqrt(ex * ex + ey * ey + ez * ez)
    if n_norm < 1e-15:
        raise ValueError("Zero normal in dual plane")
    ux, uy, uz = ex / n_norm, ey / n_norm, ez / n_norm
    # e∞ coefficient = sp(ipns, eo) — sign adjusted for dual negated normal
    einf_c = float(ipns.sp(eo))
    d = einf_c / n_norm
    # Point on plane: −d·â (signed distance from origin along normal)
    point = Point(ux * d, uy * d, uz * d)
    return Plane(point=point, normal=Direction(ux, uy, uz))


def _sphere_from_ipns(ipns: MV, einf: MV, eo: MV) -> Sphere:
    """Perwass: S̃ = α(A − ½r²·e∞) → extract center and radius.

    Uses scale-invariant formulas:
      r² = (S̃)² / (S̃·e∞)²
      a  = proj_{e123}(S̃) / (−S̃·e∞)

    If r² < 0, returns a Sphere with ``is_imaginary=True``.
    """
    einf_sp = float(ipns.sp(einf))
    if abs(einf_sp) < 1e-10:
        raise ValueError("Sphere IPNS has zero einf component – not a sphere")
    norm = -einf_sp
    ex, ey, ez = float(ipns[E1]) / norm, float(ipns[E2]) / norm, float(ipns[E3]) / norm

    s_normalized = ipns * (1.0 / norm)
    r_sq = float(s_normalized.sp(s_normalized))
    if r_sq < 0:
        return Sphere(
            center=Point(ex, ey, ez), radius=math.sqrt(-r_sq), is_imaginary=True
        )
    return Sphere(center=Point(ex, ey, ez), radius=math.sqrt(r_sq))


# ═══════════════════════════════════════════════════════════════
# Operator detection
# ═══════════════════════════════════════════════════════════════


def analyze_operator(
    mv: MV,
) -> (
    ReflectionLine
    | ReflectionPlane
    | ReflectionOrigin
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | VersorFactors
):
    """Analyze an MV in N3 as a versor.

    Classification:
    - Single-grade → Reflection/ReflectionOrigin/Inversion
    - Grades {0,2}, E-only → Dilator
    - Grades {0,2}, t-only → Translator
    - Grades {0,2}, E+t → GeneralDilator
    - Grades {0,2} or {0,2,4} → delegated to :func:`ana_versor_generic`
    - Fallback → :class:`VersorFactors`
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
        # Unhandled factor count → fallback
        return VersorFactors(factors=tuple(factors))


def _classify_single_grade_versor(mv: MV, einf: MV, eo: MV):
    """Pure-grade blade: distinguish by algebraic components.

    Perwass (table in GAConfSpc_Op.tex):
    - Reflection: basis e₁, e₂, e₃, e∞ (plane IPNS, NO e₀)
    - Inversion:  basis e₁, e₂, e₃, e∞, e₀ (sphere IPNS, HAS e₀)

    So the e₀ component discriminates:
      - eo_c ≈ 0  → plane  → ReflectionPlane (any distance from origin)
      - eo_c ≠ 0  → sphere → Inversion or ReflectionOrigin

    ReflectionOrigin is the special case: e₀ only, no Euclidean, no e∞.
    """
    grades = _get_grades(mv)
    max_grade = max(grades)

    if max_grade == 1:
        ex, ey, ez = eucl_part(mv, einf, eo)
        eucl_norm = math.sqrt(ex * ex + ey * ey + ez * ez)
        einf_c = einf_coeff(mv, eo)
        eo_c = eo_coeff(mv, einf)

        if eucl_norm < 1e-10 and abs(eo_c) < 1e-10 and abs(einf_c) < 1e-10:
            raise ValueError("Zero versor")

        # Has e₀ component → sphere IPNS → Inversion or ReflectionOrigin
        if abs(eo_c) > 1e-10:
            # ReflectionOrigin: only e₀, no Euclidean, no e∞
            if eucl_norm < 1e-10 and abs(einf_c) < 1e-10:
                return ReflectionOrigin()
            # Inversion: sphere IPNS S = Cop(c) − ½r²·e∞
            f_eo = eo_c
            px = ex / f_eo if abs(f_eo) > 1e-10 else 0.0
            py = ey / f_eo if abs(f_eo) > 1e-10 else 0.0
            pz = ez / f_eo if abs(f_eo) > 1e-10 else 0.0
            r_sq = float(mv.sp(mv))
            radius = math.sqrt(abs(r_sq)) if abs(r_sq) > 1e-10 else 1.0
            return Inversion(center=Point(px, py, pz), radius=radius)

        # No e₀ → plane IPNS → ReflectionPlane (any distance)
        if eucl_norm < 1e-10:
            raise ValueError("Zero normal in reflection versor")
        return ReflectionPlane(
            normal=Direction(ex / eucl_norm, ey / eucl_norm, ez / eucl_norm)
        )
    elif max_grade == 2:
        # ReflectionLine: mv = d∧e∞ where d is a Euclidean direction.
        # d = -mv·e₀  (algebraic identity: (eᵢ∧e∞)·e₀ = -eᵢ)
        inner = mv.ip(eo)  # grade-1, purely Euclidean
        dx, dy, dz = -float(inner[E1]), -float(inner[E2]), -float(inner[E3])
        d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d_norm < 1e-15:
            raise ValueError("Zero direction in ReflectionLine versor")
        return ReflectionLine(
            direction=Direction(dx / d_norm, dy / d_norm, dz / d_norm)
        )
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
            is_2d=False,
        )


def _classify_quad_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    """Classify a 4-factor versor: Motor or GeneralRotor.

    Delegates to :func:`ana_versor_generic` which classifies by grade
    content (grade-4 → Motor, no grade-4 → GeneralRotor).
    """
    return ana_versor_generic(
        mv,
        einf_like=einf,
        e0_inv_like=-eo,
        blade_order_sign=-1,
        is_2d=False,
    )


# ── Operator helpers ──────────────────────────────────────────


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))
    bivector = n1.op(n2)
    bx, by, bz = float(bivector[E23]), float(bivector[E13]), float(bivector[E12])
    bv_norm = math.sqrt(bx * bx + by * by + bz * bz)
    axis = (
        Direction(1, 0, 0)
        if bv_norm < 1e-15
        else Direction(bx / bv_norm, by / bv_norm, bz / bv_norm)
    )
    return Rotor(angle=angle, axis=axis)


def _translator_from_versor(mv: MV) -> Translator:
    """Extract translation vector using algebraic eᵢ∧e₀ inner product.

    Uses the algebraic identity (eᵢ∧e∞)·(eᵢ∧e₀) = 1 to extract
    the eᵢ∧e∞ coefficient without relying on raw ep/em blade IDs.
    For T = 1 − ½·t·e∞:  tᵢ = +2 · mv·(eᵢ∧e₀) / mv[0].
    """
    dx, dy, dz = translator_coeffs(mv, mv.algebra)
    return Translator(vector=Direction(dx, dy, dz))


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
    tz = float(t_euc[E3])
    t_norm = math.sqrt(tx * tx + ty * ty + tz * tz)

    if t_norm < 1e-10:
        return Dilator(factor=factor)
    else:
        return Dilator(factor=factor, origin=Point(tx, ty, tz))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _get_grades(mv: MV) -> set[int]:
    return set(mv.grades)


def _factor_to_point(factor: MV, alg: Algebra) -> Point:
    """Extract a Euclidean point from a homogeneous point blade.

    Supports two forms:
      - Grade 1  (standard form):  X = x + s·e∞ + e₀
        handled by dividing Euclidean coefficients by e₀ coefficient.
      - Grade 2  (from P*·L):     X = x^i e_i e∞ + s e∞ e₀
        handled via  p = X·e₀, s = −p·e∞, then p/s.
    """
    einf = get_einf(alg)
    eo = get_eo(alg)

    grades = _get_grades(factor)
    if 1 in grades:
        # Grade-1 homogeneous point
        f_eo = eo_coeff(factor, einf)
        if abs(f_eo) < 1e-15:
            return Point(float(factor[E1]), float(factor[E2]), float(factor[E3]))
        return Point(
            x=float(factor[E1]) / f_eo,
            y=float(factor[E2]) / f_eo,
            z=float(factor[E3]) / f_eo,
        )

    # Grade-2 homogeneous point (from circle centre U = P*·L)
    p = factor.ip(eo)  # grade 1: Euclidean point up to scale
    s = -float(p.sp(einf))  # scale factor
    if abs(s) < 1e-15:
        return Point(float(p[E1]), float(p[E2]), float(p[E3]))
    return Point(
        x=float(p[E1]) / s,
        y=float(p[E2]) / s,
        z=float(p[E3]) / s,
    )


def _circumcenter(p1: Point, p2: Point, p3: Point) -> Point:
    a = (p2.x - p1.x, p2.y - p1.y, p2.z - p1.z)
    b = (p3.x - p1.x, p3.y - p1.y, p3.z - p1.z)
    n = (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )
    a_len2 = a[0] ** 2 + a[1] ** 2 + a[2] ** 2
    b_len2 = b[0] ** 2 + b[1] ** 2 + b[2] ** 2
    n_len2 = n[0] ** 2 + n[1] ** 2 + n[2] ** 2
    if n_len2 < 1e-15:
        return p1
    nxa = (
        n[1] * a[2] - n[2] * a[1],
        n[2] * a[0] - n[0] * a[2],
        n[0] * a[1] - n[1] * a[0],
    )
    bxn = (
        b[1] * n[2] - b[2] * n[1],
        b[2] * n[0] - b[0] * n[2],
        b[0] * n[1] - b[1] * n[0],
    )
    cx = p1.x + (b_len2 * nxa[0] + a_len2 * bxn[0]) / (2 * n_len2)
    cy = p1.y + (b_len2 * nxa[1] + a_len2 * bxn[1]) / (2 * n_len2)
    cz = p1.z + (b_len2 * nxa[2] + a_len2 * bxn[2]) / (2 * n_len2)
    return Point(cx, cy, cz)
