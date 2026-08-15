# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Conformal Space".

"""N3 entity/operator creation — converts dataclasses to MVs.

N3 (Cl(4,1)) is the conformal model: Cop(x) = x + ½x²·e∞ + e₀.
All Euclidean entities and operators are representable.

Only the null basis vectors einf = e∞ and eo = e₀ are used for
construction.  The underlying ep/em blade IDs are never referenced
directly.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._n3_helpers import (
    E1,
    E2,
    E3,
    E12,
    E13,
    E23,
    get_einf,
    get_eo,
)
from .entities import Direction, Line, Plane, Point
from .operators import Rotor, Translator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


def _cop(basis: Algebra, x: float, y: float, z: float) -> MV:
    """Conformal point Cop(x) = x + ½x²·e∞ + e₀."""
    r_sq = x * x + y * y + z * z
    eucl = basis.multivector({E1: x, E2: y, E3: z})
    return eucl + get_einf(basis) * (0.5 * r_sq) + get_eo(basis)


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Conformal point ``Cop(x)`` (grade-1, on the null cone)."""
    mv = _cop(basis, x, y, z)
    if not opns:
        mv = mv.dual()
    return mv


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Euclidean direction vector (e∞ = 0, e₀ = 0)."""
    mv = basis.multivector({E1: x, E2: y, E3: z})
    if not opns:
        mv = mv.dual()
    return mv


def create_homogeneous_point(
    basis: Algebra, point: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    """OPNS: ``A ∧ e∞``."""
    a = _cop(basis, point.x, point.y, point.z)
    einf = get_einf(basis)
    mv = a.op(einf) * weight
    if not opns:
        mv = mv.dual()
    return mv


def create_homogeneous_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """OPNS: ``d∧e∞`` (grade 2) where d is a Euclidean direction.

    IPNS: dual of OPNS.
    """
    d = basis.multivector({E1: x, E2: y, E3: z})
    einf = get_einf(basis)
    mv = d.op(einf)
    if not opns:
        mv = mv.dual()
    return mv


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    """OPNS: ``Cop(a) ∧ Cop(b)`` (grade-2)."""
    cp1 = _cop(basis, a.x, a.y, a.z)
    cp2 = _cop(basis, b.x, b.y, b.z)
    mv = cp1.op(cp2)
    if not opns:
        mv = mv.dual()
    return mv


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """OPNS: ``Cop(a) ∧ Cop(b) ∧ e∞`` (grade-3)."""
    a = _cop(basis, origin.x, origin.y, origin.z)
    b = _cop(
        basis,
        origin.x + direction.x,
        origin.y + direction.y,
        origin.z + direction.z,
    )
    mv = a.op(b).op(get_einf(basis))
    if not opns:
        mv = mv.dual()
    return mv


def create_plane(basis: Algebra, plane: Plane, *, opns: bool = True) -> MV:
    """Plane with normal *n* through *point*.

    Uses direct IPNS formula ``P = â + α·e∞`` (grade-1 vector) where â
    is the unit normal and α is the signed distance from origin
    (Perwass GIPNS).  Dualizes to OPNS (grade-4) when ``opns=True``.
    """
    nx, ny, nz = plane.normal.x, plane.normal.y, plane.normal.z
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero normal – not a valid plane")

    ux, uy, uz = nx / n_norm, ny / n_norm, nz / n_norm
    alpha = plane.point.x * ux + plane.point.y * uy + plane.point.z * uz

    ipns = basis.multivector({E1: ux, E2: uy, E3: uz}) + get_einf(basis) * alpha
    if opns:
        return ipns.dual()
    return ipns


def create_sphere(
    basis: Algebra,
    center: Point,
    radius: float,
    *,
    opns: bool = True,
    is_imaginary: bool = False,
) -> MV:
    """Sphere centered at *center* with radius *r*.

    Uses direct IPNS formula ``S = Cop(c) − ½·r²·e∞`` (grade-1 vector,
    Perwass GIPNS).  Dualizes to OPNS (grade-4) when ``opns=True``.
    """
    if is_imaginary:
        raise NotImplementedError("Imaginary spheres are not supported yet.")

    c = _cop(basis, center.x, center.y, center.z)
    einf = get_einf(basis)
    ipns = c - einf * (0.5 * radius * radius)
    if opns:
        return ipns.dual()
    return ipns


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    """Circle in plane with given normal, centered at *center*.

    Constructed as intersection of sphere (S = Cop(c) − ½r²·e∞) and
    plane (P = â + α·e∞) in IPNS: ``C = S ∧ P`` (grade-2 IPNS).
    Dualized to OPNS (grade-3) when ``opns=True``.
    """
    nx, ny, nz = normal.x, normal.y, normal.z
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero normal – not a valid circle")

    ux, uy, uz = nx / n_norm, ny / n_norm, nz / n_norm
    alpha = center.x * ux + center.y * uy + center.z * uz

    c = _cop(basis, center.x, center.y, center.z)
    einf = get_einf(basis)

    s_ipns = c - einf * (0.5 * radius * radius)
    p_ipns = basis.multivector({E1: ux, E2: uy, E3: uz}) + einf * alpha

    circle_ipns = s_ipns.op(p_ipns)
    if opns:
        return circle_ipns.dual()
    return circle_ipns


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """OPNS pseudoscalar ``scale * I``; IPNS is the scalar ``scale``."""
    opns_mv = basis.multivector({basis.pseudoscalar_id: scale})
    if opns:
        return opns_mv
    return opns_mv.dual()


def create_imag_point_pair(
    basis: Algebra,
    center: Point,
    direction: Direction,
    separation: float,
    *,
    opns: bool = True,
) -> MV:
    """Imaginary point pair: dual of a real circle (not yet supported)."""
    raise NotImplementedError("Imaginary point pairs are not supported yet.")


def create_imag_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    """Imaginary circle: dual of a real point pair (not yet supported)."""
    raise NotImplementedError("Imaginary circles are not supported yet.")


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) - sin(θ/2)·(ax·e₂₃ + ay·e₃₁ + az·e₁₂)``."""
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E23: -math.sin(half) * axis.x,
            E13: math.sin(half) * axis.y,
            E12: -math.sin(half) * axis.z,
        }
    )


def create_translator(basis: Algebra, dx: float, dy: float, dz: float) -> MV:
    """``T = 1 − ½·t·e∞`` (Perwass)."""
    t = basis.multivector({E1: dx, E2: dy, E3: dz})
    return basis.multivector({0: 1.0}) - basis.multivector({0: 0.5}) * t.op(
        get_einf(basis)
    )


def create_dilator(
    basis: Algebra,
    factor: float,
    *,
    origin: Point | None = None,
) -> MV:
    """Dilator about an origin point.

    ``D = 1 + (1−d)/(1+d)·E`` where E = e∞∧e₀ (Perwass).

    If *origin* is given, returns ``D_t = T·D·T̃`` where T translates
    from the global origin to the dilation center (general dilator).
    """
    if factor <= 0:
        raise ValueError(f"Dilator factor must be positive, got {factor}")
    coeff = (1.0 - factor) / (1.0 + factor)
    E = get_einf(basis).op(get_eo(basis))
    d = basis.multivector({0: 1.0}) + E * coeff

    if origin is None:
        return d

    t = create_translator(basis, origin.x, origin.y, origin.z)
    return t.gp(d).gp(t.rev())


def create_motor(basis: Algebra, rotor: Rotor, translator: Translator) -> MV:
    """``M = T·R`` — translation followed by rotation."""
    t = create_translator(
        basis, translator.vector.x, translator.vector.y, translator.vector.z
    )
    r = create_rotor(basis, rotor.angle, rotor.axis)
    return t.gp(r)


def create_reflection_plane(basis: Algebra, plane: Plane) -> MV:
    """Reflection in a plane (not necessarily through the origin).

    OPNS: ``Cop(a)∧Cop(b)∧Cop(c)∧e∞`` where a, b, c are three
    non-collinear points on the plane.  Equivalent to creating the
    plane entity OPNS.
    """
    return create_plane(basis, plane, opns=True)


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    """Inversion in a sphere of given *radius* centered at *center*.

    Returns grade-1 sphere IPNS ``S = Cop(center) − ½·radius²·e∞``.
    This is NOT a null vector — it's an IPNS sphere with S² = radius².
    For center at (0,0,0) and radius=1: S = e₀ − ½e∞ = −e₊.
    """
    return create_sphere(basis, center, radius, opns=False)


def create_reflection_line(basis: Algebra, line: Line) -> MV:
    """Reflection across a line (not necessarily through the origin).

    OPNS: ``Cop(a)∧Cop(b)∧e∞`` where a, b are two points on the line.
    This is the same MV as the line entity itself.
    """
    a = _cop(basis, line.origin.x, line.origin.y, line.origin.z)
    b = _cop(
        basis,
        line.origin.x + line.direction.x,
        line.origin.y + line.direction.y,
        line.origin.z + line.direction.z,
    )
    return a.op(b).op(get_einf(basis))


def create_reflection_point(basis: Algebra, point: Point) -> MV:
    """Reflection in a point.

    OPNS: ``Cop(p)∧e∞`` — the HPoint blade used as a versor.
    This is identical to the OPNS HPoint entity with weight=1.
    """
    return create_homogeneous_point(basis, point, weight=1.0, opns=True)


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    """General rotor: ``G = T·R·T̃`` (Perwass).

    Represents a rotation about *axis* through *origin*.
    The result has 7 components (scalar + 6 bivectors),
    with no 4-vector term (distinguishes it from Motor).
    """
    t = create_translator(basis, origin.x, origin.y, origin.z)
    r = create_rotor(basis, angle, axis)
    return t.gp(r).gp(t.rev())
