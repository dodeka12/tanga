# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA2 entity/operator creation — converts dataclasses to MVs.

Implements the Gunn/Dorst plane‑based PGA model (G(2, 0, 1)) within the
4D algebra via the null‑vector embedding e₀ = ep + em.  This embedding is
necessary because TANGA does not support zero‑squaring basis vectors
natively; see ``docs/py/basis/pga_null_embedding.md``.

In 2D PGA, a "plane" is a line (codimension-1 hyperplane) and a "line"
(through two points) is a point.  The naming follows the 3D PGA convention
but with reduced spatial dimension.

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
    _get_e0,
)
from .entities import Direction, Point
from .operators import GeneralRotor, ReflectionLine, Rotor, Translator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


# ── Entities ──────────────────────────────────────────────────


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Create a PGA2 point.

    *opns=True* (default):  grade‑2 bivector (intersection of two lines
      ``(e₁ − x·e₀) ∧ (e₂ − y·e₀)``).

    *opns=False* (IPNS):  grade‑1 vector ``x·e₁ + y·e₂ + e₀``.
    """
    p_ipns = basis.multivector({E1: -x, E2: -y, EP: -1.0, EM: -1.0})
    if not opns:
        return p_ipns

    return p_ipns.dual()


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Create a PGA2 direction (ideal point).

    *opns=True*:  grade‑2 bivector (dual of the IPNS direction vector).

    *opns=False* (IPNS):  grade‑1 vector ``x·e₁ + y·e₂``.
    """
    if not opns:
        return basis.multivector({E1: x, E2: y})

    # OPNS: dualize the IPNS direction vector using the 3D PGA dual.
    # A direction's IPNS form is v₁e₁ + v₂e₂ (no e₀ component).
    # Its OPNS form is the PGA dual of this, producing a grade‑2 bivector
    # whose dual has zero e₀ coefficient (ideal point at infinity).
    ipns = basis.multivector({E1: x, E2: y})
    return basis.dual(ipns)


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Create a PGA2 line (codimension-1 hyperplane in 2D).

    In 2D PGA, a line is a grade‑1 vector ``nx·e₁ + ny·e₂ + d·e₀``
    where *d* is the signed distance from origin (the IPNS/OPNS form
    of a hyperplane).  The line's normal is perpendicular to *direction*.

    *opns=True* (default):  grade‑1 vector.
    *opns=False* (IPNS):  4D ``dual()`` of the OPNS blade.
    """
    # Line direction (dx, dy), normal = (-dy, dx)
    dx, dy = direction.x, direction.y
    n_norm = math.sqrt(dx * dx + dy * dy)
    if n_norm < 1e-15:
        raise ValueError("Zero direction – not a valid line")
    nx, ny = -dy / n_norm, dx / n_norm

    # Signed distance: n·origin
    d = -(nx * origin.x + ny * origin.y)

    mv = basis.multivector({E1: nx, E2: ny, EP: d, EM: d})
    if not opns:
        mv = mv.dual()
    return mv


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """PGA2 Space: ``scale · e₁ ∧ e₂ ∧ e₀``."""
    if hasattr(basis, "e1"):
        mv = basis.e1.op(basis.e2).op(_get_e0(basis)) * scale
    else:
        mv = basis.multivector(
            {
                E12: scale,
                EP: scale,
                EM: scale,
            }
        ).grade(3)
    if not opns:
        mv = mv.dual()  # IPNS is a scalar
    return mv


# ── Operators (no opns flag) ──────────────────────────────────


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) + sin(θ/2)·e₁₂``.

    In 2D the rotation bivector is always e₁₂.
    """
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E12: -math.sin(half),
        }
    )


def create_translator(basis: Algebra, dx: float, dy: float, dz: float) -> MV:
    """``1 − 0.5·(dx·e₁∧e₀ + dy·e₂∧e₀)``."""
    return basis.multivector(
        {
            0: 1.0,
            5: 0.5 * dx,  # e1∧ep
            9: 0.5 * dx,  # e1∧em
            6: 0.5 * dy,  # e2∧ep
            10: 0.5 * dy,  # e2∧em
        }
    )


def create_motor(basis: Algebra, rotor: Rotor, translator: Translator) -> MV:
    """``T · R`` = translation followed by rotation."""
    t_mv = create_translator(basis, translator.vector.x, translator.vector.y, 0.0)
    r_mv = create_rotor(basis, rotor.angle, rotor.axis)
    return t_mv.gp(r_mv)


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    """General rotor: rotation about an arbitrary origin point.

    ``G = T · R · T̃`` — the conjugation cancels the translator's effect on
    position, leaving a pure rotation about the origin point.

    The result has grades {0, 2} (scalar + bivector), distinguishing it from
    a Motor which also has a grade‑3 term.
    """
    t_mv = create_translator(basis, origin.x, origin.y, 0.0)
    r_mv = create_rotor(basis, angle, axis)
    return t_mv.gp(r_mv).gp(t_mv.rev())


def create_reflection_line(basis: Algebra, line: Line) -> MV:
    """Reflection across a line — same blade as the line entity OPNS.

    In PGA2, a line is a grade-1 vector.
    """
    return create_line(basis, line.origin, line.direction, opns=True)


def create_reflection_point(basis: Algebra, point: Point) -> MV:
    """Reflection in a point — same blade as the point entity OPNS.

    In PGA2, a point is a grade-2 bivector.
    Reflection in the origin is ``ReflectionPoint(Point(0,0,0))``.
    """
    return create_point(basis, point.x, point.y, 0.0, opns=True)


# ═══════════════════════════════════════════════════════════════
# N2-only stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_sphere(
    basis: Algebra, center: Point, radius: float, *, opns: bool = True
) -> MV:
    raise ValueError("Spheres require conformal embedding (N2); not available in PGA2.")


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    raise ValueError("Circles require conformal embedding (N2); not available in PGA2.")


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    raise ValueError(
        "Point pairs require conformal embedding (N2); not available in PGA2."
    )


def create_homogeneous_point(
    basis: Algebra, pt: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    raise ValueError(
        "Homogeneous points require conformal embedding (N2); not available in PGA2."
    )


def create_dilator(basis: Algebra, factor: float) -> MV:
    raise ValueError(
        "Dilators require conformal embedding (N2); not available in PGA2."
    )


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    raise ValueError(
        "Inversions require conformal embedding (N2); not available in PGA2."
    )
