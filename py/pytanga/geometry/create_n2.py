# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Conformal Space".

"""N2 entity/operator creation — converts dataclasses to MVs.

N2 (Cl(3,1)) is the conformal model for 2D: Cop(x) = x + ½x²·e∞ + e₀.
All 2D Euclidean entities and operators are representable.

Only the null basis vectors einf = e∞ and eo = e₀ are used for
construction.  The underlying ep/em blade IDs are never referenced
directly.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._n2_helpers import (
    E1,
    E2,
    E12,
    get_einf,
    get_eo,
)
from .entities import Direction, Point
from .operators import Rotor, Translator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


def _cop(basis: Algebra, x: float, y: float) -> MV:
    """Conformal point Cop(x) = x + ½x²·e∞ + e₀."""
    r_sq = x * x + y * y
    eucl = basis.multivector({E1: x, E2: y})
    return eucl + get_einf(basis) * (0.5 * r_sq) + get_eo(basis)


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Conformal point ``Cop(x, y)`` (grade-1, on the null cone)."""
    mv = _cop(basis, x, y)
    if not opns:
        mv = mv.dual()
    return mv


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Euclidean direction vector (e∞ = 0, e₀ = 0)."""
    mv = basis.multivector({E1: x, E2: y})
    if not opns:
        mv = mv.dual()
    return mv


def create_homogeneous_point(
    basis: Algebra, point: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    """OPNS: ``A ∧ e∞``."""
    a = _cop(basis, point.x, point.y)
    einf = get_einf(basis)
    mv = a.op(einf) * weight
    if not opns:
        mv = mv.dual()
    return mv


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    """OPNS: ``Cop(a) ∧ Cop(b)`` (grade-2)."""
    cp1 = _cop(basis, a.x, a.y)
    cp2 = _cop(basis, b.x, b.y)
    mv = cp1.op(cp2)
    if not opns:
        mv = mv.dual()
    return mv


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """OPNS: ``Cop(a) ∧ Cop(b) ∧ e∞`` (grade-3)."""
    a = _cop(basis, origin.x, origin.y)
    b = _cop(
        basis,
        origin.x + direction.x,
        origin.y + direction.y,
    )
    mv = a.op(b).op(get_einf(basis))
    if not opns:
        mv = mv.dual()
    return mv


def create_sphere(
    basis: Algebra,
    center: Point,
    radius: float,
    *,
    opns: bool = True,
    is_imaginary: bool = False,
) -> MV:
    """Circle centered at *center* with radius *r*.

    In 2D conformal geometry, a "sphere" (codimension-0 entity) is a
    circle.  Uses direct IPNS formula ``S = Cop(c) − ½·r²·e∞`` (grade-1
    vector, Perwass GIPNS).  Dualizes to OPNS (grade-3) when ``opns=True``.

    For imaginary circles (no real points), use ``is_imaginary=True``
    (plus sign: ``S = Cop(c) + ½·r²·e∞``, has ``S² = −r²``).
    """
    c = _cop(basis, center.x, center.y)
    einf = get_einf(basis)
    sign = 1.0 if is_imaginary else -1.0
    ipns = c + einf * (0.5 * radius * radius * sign)
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
    """In 2D, a "circle" is equivalent to a sphere (both are circles).

    This is provided for API consistency with 3D.  Delegates to
    ``create_sphere``, ignoring the normal parameter.
    """
    return create_sphere(basis, center, radius, opns=opns)


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """Pseudoscalar ``scale * I``."""
    return basis.multivector({basis.pseudoscalar_id: scale})


def create_imag_point_pair(
    basis: Algebra,
    center: Point,
    direction: Direction,
    separation: float,
    *,
    opns: bool = True,
) -> MV:
    """Imaginary point pair: dual of a real circle."""
    nx, ny = direction.x, direction.y
    n_norm = math.sqrt(nx * nx + ny * ny)
    if n_norm < 1e-15:
        raise ValueError("Zero direction – not a valid imaginary point pair")
    ux, uy = nx / n_norm, ny / n_norm
    r = separation / 2.0
    circle_opns = create_sphere(basis, center, r, opns=True)
    mv = circle_opns.dual()
    if not opns:
        mv = mv.dual()
    return mv


def create_imag_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    """Imaginary circle: dual of a real point pair."""
    nx, ny = normal.x, normal.y
    n_norm = math.sqrt(nx * nx + ny * ny)
    if n_norm < 1e-15:
        raise ValueError("Zero normal – not a valid imaginary circle")
    ux, uy = nx / n_norm, ny / n_norm
    half_sep = radius
    a = Point(
        center.x - ux * half_sep,
        center.y - uy * half_sep,
        0.0,
    )
    b = Point(
        center.x + ux * half_sep,
        center.y + uy * half_sep,
        0.0,
    )
    pp_opns = create_point_pair(basis, a, b, opns=True)
    mv = pp_opns.dual()
    if not opns:
        mv = mv.dual()
    return mv


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) + sin(θ/2)·e₁₂``."""
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E12: math.sin(half),
        }
    )


def create_translator(basis: Algebra, dx: float, dy: float, dz: float) -> MV:
    """``T = 1 − ½·t·e∞`` (Perwass)."""
    t = basis.multivector({E1: dx, E2: dy})
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

    t = create_translator(basis, origin.x, origin.y, 0.0)
    return t.gp(d).gp(t.rev())


def create_motor(basis: Algebra, rotor: Rotor, translator: Translator) -> MV:
    """``M = T·R`` — translation followed by rotation."""
    t = create_translator(basis, translator.vector.x, translator.vector.y, 0.0)
    r = create_rotor(basis, rotor.angle, rotor.axis)
    return t.gp(r)


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    """Inversion in a circle of given *radius* centered at *center*.

    Returns grade-1 circle IPNS ``S = Cop(center) − ½·radius²·e∞``.
    This is NOT a null vector — it's an IPNS circle with S² = radius².
    """
    return create_sphere(basis, center, radius, opns=False)


def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection across a *line* through the origin with direction *d*.

    Returns the bivector ``d∧e∞`` = d.x·e₁∧e∞ + d.y·e₂∧e∞ (grade-2).
    """
    d = basis.multivector({E1: direction.x, E2: direction.y})
    return d.op(get_einf(basis))


def create_reflection_origin(basis: Algebra) -> MV:
    """Reflection about the origin (versor = e₀)."""
    return get_eo(basis)


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    """General rotor: ``G = T·R·T̃`` (Perwass).

    Represents a rotation about *axis* through *origin* (a point in 2D).
    The result has 5 components (scalar + 4 bivectors),
    with no 3-vector term (distinguishes it from Motor).
    """
    t = create_translator(basis, origin.x, origin.y, 0.0)
    r = create_rotor(basis, angle, axis)
    return t.gp(r).gp(t.rev())
