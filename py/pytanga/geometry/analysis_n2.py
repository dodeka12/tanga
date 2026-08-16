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
    HDirection,
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
    ReflectionPoint,
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
) -> (
    Point
    | Direction
    | PointPair
    | HPoint
    | HDirection
    | Line
    | Circle
    | Sphere
    | Space
    | None
):
    """Analyze an MV in N2 as a geometric entity.

    Returns ``None`` if the null-space of the MV (in the
    ``mv.algebra.opns`` interpretation) is empty.

    In 2D conformal geometry, a "sphere" is a circle and a "plane" is a
    line.  Entity naming follows what the entity looks like in 2D.
    """
    if not mv.algebra.opns:
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
    | HDirection
    | Line
    | Circle
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
        raise ValueError(f"Mixed-grade MV in N2: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_or_direction_n2_opns(mv)
    elif max_grade == 2:
        return _decompose_grade2_opns(mv)
    elif max_grade == 3:
        return _line_or_circle_n2_opns(mv)
    elif max_grade == 4:
        # Pseudoscalar → Space
        if mv.grade(4).mag > 0 and mv.grade(0).mag < 1e-15 and len(grades) == 1:
            # Pure grade-4 blade could be Space, IPNS line, or OPNS sphere
            # Check if it's the pseudoscalar (all unit components) → Space
            return _sphere_or_line_or_space_n2_opns(mv)
        return _sphere_or_line_n2_opns(mv)
    else:
        raise ValueError(f"Unexpected grade {max_grade} in N2")


# ── Grade 1: Point / Direction ────────────────────────────────


def _point_or_direction_n2_opns(mv: MV) -> Point | Direction | None:
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


def _decompose_grade2_opns(mv: MV) -> PointPair | HPoint | HDirection:
    """Analyze a grade‑2 OPNS blade (mirrors N3 _decompose_grade2).

    Perwass, GAConfSpc_Ana.tex §PointPair (adapted for 2D):
    """
    alg = mv.algebra
    einf = get_einf(alg)
    eo = get_eo(alg)

    # ── HPoint / HDirection check: Q = P∧e∞ → Q∧e∞ = 0 ──
    if mv.op(einf).is_zero:
        # Check for E = e∞∧e₀ component to distinguish HPoint from HDirection
        E = einf.op(eo)
        E_coeff = float(mv.sp(E))
        if abs(E_coeff) > 1e-10:
            # HPoint: has e₀∧e∞ component
            weight = -E_coeff
            return HPoint(point=_factor_to_point(mv, alg), weight=weight)
        else:
            # HDirection: d∧e∞, no e₀∧e∞ component
            inner = mv.ip(eo)  # (d∧e∞)·e₀ = -d
            dx, dy = -float(inner[E1]), -float(inner[E2])
            d_norm = math.sqrt(dx * dx + dy * dy)
            if d_norm < 1e-15:
                raise ValueError("Zero direction in HDirection blade")
            return HDirection(direction=Direction(dx / d_norm, dy / d_norm, 0.0))

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
    direction = Direction(float(d[E1]), float(d[E2]), 0.0).normalized()

    # ── 5. Point separation: S* = Q·L⁻¹ ──
    L_inv = L.inv()
    S_star = mv.ip(L_inv)
    f_eo = eo_coeff(S_star, einf)
    S_star = S_star / f_eo  # normalize to get Cop(c) − ½r²·e∞
    r_sq = float(S_star.sp(S_star))  # separation², may be negative
    half_dist = math.sqrt(abs(r_sq))
    separation = half_dist * 2.0
    is_imaginary = r_sq < 0

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


def _line_or_circle_n2_opns(mv: MV) -> Line | Circle:
    """Distinguish Line vs Circle via C∧e∞.

    For a grade-3 OPNS blade *C*:
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
    P = mv.op(einf)  # grade 3 (in 2D this is a line IPNS)
    if P.is_zero:
        raise ValueError("Degenerate circle: no line factor")

    # ── 2. IPNS circle ──
    C_star = mv.dual()  # grade 1

    # ── 3. Centre: extract from IPNS circle ──
    # C* = Cop(c) − ½r²·e∞.  e₀ component gives homogeneous weight.
    f_eo = eo_coeff(C_star, einf)
    C_star = C_star / f_eo  # normalize to get Cop(c) − ½r²·e∞

    if abs(f_eo) < 1e-15:
        raise ValueError("Degenerate circle: no e₀ component in IPNS")
    pt = Point(float(C_star[E1]), float(C_star[E2]), 0.0)

    # ── 4. Radius: from C*·C* ──
    r_sq = float(C_star.sp(C_star))
    is_imaginary = r_sq < 0
    radius = math.sqrt(abs(r_sq))

    # ── 5. Normal: always Dir(0,0,1) in 2D (perpendicular to XY plane) ──
    normal = Direction(0.0, 0.0, 1.0)

    return Circle(center=pt, normal=normal, radius=radius, is_imaginary=is_imaginary)


# ── Grade 4: Sphere (circle) / Line (IPNS dual) ────────────────


def _sphere_or_line_or_space_n2_opns(mv: MV) -> Space | Sphere | Line:
    """Distinguish Space / Circle (Sphere) / Line from grade-4 OPNS blade."""
    ipns = mv.dual()
    if ipns.is_zero:
        raise ValueError("Zero dual – not a valid entity")

    einf = get_einf(mv.algebra)
    eo = get_eo(mv.algebra)

    # Space detection: pseudoscalar → dual is a scalar
    if ipns.is_scalar:
        return Space(scale=float(ipns[0]))

    eo_c = eo_coeff(ipns, einf)
    if abs(eo_c) > 1e-10:
        return _sphere_from_ipns(ipns, einf, eo)
    else:
        return _line_from_ipns_opns(mv, ipns, einf, eo)


def _sphere_or_line_n2_opns(mv: MV) -> Sphere | Line:
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
    | ReflectionPoint
    | HDirection
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | VersorFactors
):
    """Analyze an MV in N2 as a versor.

    Classification follows Perwass table (adapted for 2D):
    - Pure-grade blade → dualization+grade-1/2 classifiers
    - Rotor: grades {0,2}, only e₁₂ bivector
    - Translator: grades {0,2}, eᵢ∧e∞ bivectors
    - Dilator: grades {0,2}, only e∞∧e₀
    - Dilator: grades {0,2}, eᵢ∧e∞ AND e∞∧e₀
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
    """Pure-grade blade: dualize high grades, then classify at grade 1 or 2.

    Dualization principle: the dual has the same operator effect (up to sign).
    For N2 (dim=4):
      - v_grade 1 or 2 → classify directly
      - v_grade 3      → handle directly if OPNS line, else dualize → grade 1
    """
    v_scale, v_factors = mv.blade_factorize_versor()
    v_grade = len(v_factors)

    if v_grade == 3:
        # Grade-3 blade: if it contains e∞ it's an OPNS line (ReflectionLine)
        if mv.op(einf).is_zero:
            line = _decompose_line(mv)
            if line is None:
                raise ValueError("Degenerate line in ReflectionLine operator")
            return ReflectionLine(line)
        # Otherwise dualize (e.g. imaginary circle → inversion via dual)
        op = mv.dual()
        return _classify_grade1_operator(op, einf, eo)

    if v_grade >= 4:
        op = mv.dual()
        v_grade = 4 - v_grade
    else:
        op = mv

    if v_grade == 1:
        return _classify_grade1_operator(op, einf, eo)
    elif v_grade == 2:
        return _classify_grade2_operator(op, einf, eo)
    raise ValueError(f"Unexpected versor grade {v_grade} after dualization")


# ── Grade-1 operator classification (N2) ─────────────────────────


def _classify_grade1_operator(op, einf, eo):
    """Classify a grade-1 blade after dualization as Inversion or ReflectionLine.

    In 2D, a grade-1 IPNS with no e₀ represents a line (the 2D "plane").
    """
    ex, ey = eucl_part(op, einf, eo)
    eucl_norm = math.sqrt(ex * ex + ey * ey)
    einf_c = einf_coeff(op, eo)
    eo_c = eo_coeff(op, einf)

    if eucl_norm < 1e-10 and abs(eo_c) < 1e-10 and abs(einf_c) < 1e-10:
        raise ValueError("Zero versor")

    # Has e₀ component → circle IPNS → Inversion
    if abs(eo_c) > 1e-10:
        return _inversion_from_ipns(op, einf, eo)

    # No e₀ → line IPNS → ReflectionLine
    if eucl_norm < 1e-10:
        raise ValueError("Zero normal in reflection versor")
    return _reflection_line_from_ipns_grade1(op, einf, eo)


# ── Grade-2 operator classification (N2) ─────────────────────────


def _classify_grade2_operator(op, einf, eo):
    """Classify a grade-2 blade (direct or dualized) as
    ReflectionPoint, ReflectionLine, or HDirection."""
    E = einf.op(eo)

    # Check for E = e∞∧e₀ component → ReflectionPoint
    e_scalar = float(op.ip(E)[0])
    if abs(e_scalar) > 1e-10:
        return _reflection_point_from_hpoint(op, einf, eo)

    # Check for Euclidean bivector → ReflectionLine (IPNS line)
    if _has_euclidean_bivector(op):
        return _reflection_line_from_ipns(op, einf, eo)

    # Pure d∧e∞ → HDirection
    return _hdirection_from_blade(op, einf, eo)


# ── Helper: Inversion from IPNS circle ───────────────────────────


def _inversion_from_ipns(op, einf, eo):
    """Extract Inversion from IPNS circle blade (grade 1)."""
    sphere = _sphere_from_ipns(op, einf, eo)
    return Inversion(center=sphere.center, radius=sphere.radius)


# ── Helper: ReflectionLine from IPNS grade-1 line ────────────────


def _reflection_line_from_ipns_grade1(op, einf, eo):
    """Extract ReflectionLine from an IPNS grade-1 line blade (2D).

    A ReflectionLine IS a Line — re-dualize back to OPNS and use the
    same decomposition as the entity path.
    """
    line_opns = op.dual()  # grade-1 IPNS → grade-3 OPNS
    line = _decompose_line(line_opns)
    if line is None:
        raise ValueError("Degenerate line in ReflectionLine operator")
    return ReflectionLine(line)


# ── Helper: ReflectionPoint from HPoint blade ───────────────────


def _reflection_point_from_hpoint(op, einf, eo):
    """Extract ReflectionPoint from an OPNS HPoint blade (grade 2)."""
    alg = op.algebra
    point = _factor_to_point(op, alg)
    return ReflectionPoint(point)


# ── Helper: ReflectionLine from IPNS bivector ───────────────────


def _reflection_line_from_ipns(op, einf, eo):
    """Extract ReflectionLine from an IPNS line bivector (grade 2).

    Dualizes back to OPNS and uses existing line decomposition.
    """
    line_opns = op.dual()
    line = _decompose_line(line_opns)
    if line is None:
        raise ValueError("Degenerate line in ReflectionLine operator")
    return ReflectionLine(line)


# ── Helper: HDirection from blade ───────────────────────────────


def _hdirection_from_blade(op, einf, eo):
    """Extract HDirection from a pure d∧e∞ blade (grade 2)."""
    inner = op.ip(eo)  # (d∧e∞)·e₀ = -d
    dx, dy = -float(inner[E1]), -float(inner[E2])
    d_norm = math.sqrt(dx * dx + dy * dy)
    if d_norm < 1e-15:
        raise ValueError("Zero direction in HDirection blade")
    return HDirection(direction=Direction(dx / d_norm, dy / d_norm, 0.0))


# ── Helper: Has Euclidean bivector ───────────────────────────────


def _has_euclidean_bivector(op):
    """True if the blade has E12 bivector component (2D)."""
    return abs(float(op[E12])) > 1e-15


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
    """Interpret *mv* as a :class:`Point` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Point)


def analyze_direction(mv: MV) -> Direction:
    """Interpret *mv* as a :class:`Direction` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Direction)


def analyze_line(mv: MV) -> Line:
    """Interpret *mv* as a :class:`Line` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Line)


def analyze_circle(mv: MV) -> Circle:
    """Interpret *mv* as a :class:`Circle` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Circle)


def analyze_sphere(mv: MV) -> Sphere:
    """Interpret *mv* as a :class:`Sphere` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Sphere)


def analyze_point_pair(mv: MV) -> PointPair:
    """Interpret *mv* as a :class:`PointPair` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), PointPair)


def analyze_hpoint(mv: MV) -> HPoint:
    """Interpret *mv* as an :class:`HPoint` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), HPoint)


def analyze_hdirection(mv: MV) -> HDirection:
    """Interpret *mv* as an :class:`HDirection` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), HDirection)


def analyze_space(mv: MV) -> Space:
    """Interpret *mv* as :class:`Space` in its algebra's OPNS/IPNS mode."""
    return _expect(analyze_entity(mv), Space)


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
