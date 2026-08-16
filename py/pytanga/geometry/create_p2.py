# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Projective Space".

"""P2 entity/operator creation — converts dataclasses to MVs.

P2 (Cl(3)) uses homogeneous coordinates: Hop(a) = a + e₃.
Points, lines at any position are represented.
Spheres, circles, translations, dilations require N2.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pytanga.basis.p2 import BasisP2

from .entities import Direction, Point

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs — sourced from BasisP2 as single source of truth.
E1 = BasisP2.E1
E2 = BasisP2.E2
E3 = BasisP2.E3
E12 = BasisP2.E12
E13 = BasisP2.E13
E23 = BasisP2.E23
E123 = BasisP2.E123


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def _point_opns(basis: Algebra, x: float, y: float) -> MV:
    """Raw OPNS homogeneous point ``x·e₁ + y·e₂ + e₃`` (grade-1)."""
    return basis.multivector({E1: x, E2: y, E3: 1})


def create_point(basis: Algebra, x: float, y: float, z: float) -> MV:
    """Homogeneous point ``Hop(a) = x·e₁ + y·e₂ + e₃``.

    Parameters
    ----------
    basis.opns
        *True* (default) → OPNS: grade‑1 vector ``Hop(a)``.
        *False* → IPNS: grade‑2 bivector (dual of Hop(a)).
    """
    opns_mv = _point_opns(basis, x, y)
    if basis.opns:
        return opns_mv
    return opns_mv.dual()


def create_direction(basis: Algebra, x: float, y: float, z: float) -> MV:
    """Ideal point ``x·e₁ + y·e₂`` (e₃ = 0).

    Parameters
    ----------
    basis.opns
        *True* (default) → OPNS: grade‑1 direction vector (no e₃).
        *False* → IPNS: grade‑2 bivector (dual of the direction vector).
    """
    if abs(x) < 1e-15 and abs(y) < 1e-15:
        raise ValueError("Zero‑norm direction is not a valid geometric direction")

    opns_mv = basis.multivector({E1: x, E2: y})

    if basis.opns:
        return opns_mv
    return opns_mv.dual()


def create_line(basis: Algebra, origin: Point, direction: Direction) -> MV:
    """Line through *origin* with direction *d*.

    Constructed as ``Hop(origin) ∧ Hop(origin + direction)`` (two
    homogeneous points on the line).  Both factors have e₃ = 1.

    Parameters
    ----------
    basis.opns
        *True* (default) → OPNS: ``Hop(origin) ∧ Hop(origin + d)``
        (grade‑2 bivector).
        *False* → IPNS: grade‑1 vector (dual of the OPNS bivector),
        representing a line in IPNS form ``â − α·e₃``.
    """
    a = _point_opns(basis, origin.x, origin.y)
    b = _point_opns(basis, origin.x + direction.x, origin.y + direction.y)
    opns_mv = a.op(b)

    if basis.opns:
        return opns_mv
    return opns_mv.dual()


def create_space(basis: Algebra, *, scale: float = 1.0) -> MV:
    """Pseudoscalar ``scale * e₁₂₃``."""
    opns_mv = basis.multivector({E123: scale})
    if basis.opns:
        return opns_mv
    return opns_mv.dual()


# ═══════════════════════════════════════════════════════════════
# N2-only entity stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_sphere(basis: Algebra, center: Point, radius: float) -> MV:
    raise ValueError("Spheres require conformal embedding (N2); not available in P2.")


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
) -> MV:
    raise ValueError("Circles require conformal embedding (N2); not available in P2.")


def create_point_pair(basis: Algebra, a: Point, b: Point) -> MV:
    raise ValueError(
        "Point pairs require conformal embedding (N2); not available in P2."
    )


def create_homogeneous_point(
    basis: Algebra, pt: Point, weight: float = 1.0
) -> MV:
    raise ValueError(
        "Homogeneous points require conformal embedding (N2); not available in P2."
    )


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) − sin(θ/2)·e₁₂``.

    Uses the standard exponential convention R = exp(−θ·B/2), matching
    the C++ ``CBasisP3::CreateRotor`` implementation.  In 2D the plane
    is always e₁₂.
    """
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E12: -math.sin(half),
        }
    )


def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection across a *line* through the origin with direction *d*.

    Returns the bivector ``d∧e₃`` = d.x·e₁₃ + d.y·e₂₃.
    """
    return basis.multivector({E13: direction.x, E23: direction.y})


def create_reflection_point(basis: Algebra, point: Point) -> MV:
    """Reflection in a point."""
    return _point_opns(basis, point.x, point.y)

def create_translator(basis: Algebra, x: float, y: float, z: float) -> MV:
    raise ValueError(
        "Translators require conformal embedding (N2); not available in P2."
    )


def create_dilator(basis: Algebra, factor: float) -> MV:
    raise ValueError("Dilators require conformal embedding (N2); not available in P2.")


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    raise ValueError(
        "Inversions require conformal embedding (N2); not available in P2."
    )


def create_motor(basis: Algebra, rotor, translator) -> MV:
    raise ValueError("Motors require conformal embedding (N2); not available in P2.")


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    raise ValueError(
        "General rotors require conformal embedding (N2); not available in P2."
    )