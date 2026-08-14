# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Projective Space".

"""P3 entity/operator creation — converts dataclasses to MVs.

P3 (Cl(4)) uses homogeneous coordinates: Hop(a) = a + e₄.
Points, lines, and planes at any position are represented.
Spheres, circles, translations, dilations require N3.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from pytanga.basis.p3 import BasisP3

from .entities import Direction, Plane, Point

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
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
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Homogeneous point ``Hop(a) = x·e₁ + y·e₂ + z·e₃ + e₄``.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: grade‑1 vector ``Hop(a)``.
        *False* → IPNS: grade‑3 trivector (dual of Hop(a)), representing
        the intersection of three orthogonal planes through the point.
    """
    opns_mv = basis.multivector({E1: x, E2: y, E3: z, E4: 1})

    if opns:
        return opns_mv
    return opns_mv.dual()


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Ideal point ``x·e₁ + y·e₂ + z·e₃`` (e₄ = 0).

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: grade‑1 direction vector (no e₄).
        *False* → IPNS: grade‑3 trivector (dual of the direction vector).
    """
    if abs(x) < 1e-15 and abs(y) < 1e-15 and abs(z) < 1e-15:
        raise ValueError("Zero‑norm direction is not a valid geometric direction")

    opns_mv = basis.multivector({E1: x, E2: y, E3: z})

    if opns:
        return opns_mv
    return opns_mv.dual()


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Line through *origin* with direction *d*.

    Constructed as ``Hop(origin) ∧ Hop(origin + direction)`` (Perwass:
    two homogeneous points on the line).  Both factors have e₄ = 1.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: ``Hop(origin) ∧ Hop(origin + d)``
        (grade‑2 bivector, two homogeneous points on the line).
        *False* → IPNS: grade‑2 bivector (dual of the OPNS bivector),
        representing the intersection of two IPNS planes containing the line.

    Notes
    -----
    In G(4,0), grade 2 is the self‑dual grade, so OPNS and IPNS lines
    are both bivectors (but with different blade coefficients).
    """
    a = create_point(basis, origin.x, origin.y, origin.z, opns=True)
    b = create_point(
        basis,
        origin.x + direction.x,
        origin.y + direction.y,
        origin.z + direction.z,
        opns=True,
    )
    opns_mv = a.op(b)

    if opns:
        return opns_mv
    return opns_mv.dual()


def create_plane(basis: Algebra, plane: Plane, *, opns: bool = True) -> MV:
    """Plane through *point* with normal *n*.

    OPNS (default): three homogeneous points → grade-3 trivector.
    IPNS (``opns=False``): direct formula ``P = â − α·e₄`` where â is
    the unit normal and α is the signed distance from the origin
    (Perwass GIPNS).  When ``opns=True``, constructs via IPNS then
    dualizes.
    """
    nx, ny, nz = plane.normal.x, plane.normal.y, plane.normal.z
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm < 1e-15:
        raise ValueError("Zero normal – not a valid plane")

    ux, uy, uz = nx / n_norm, ny / n_norm, nz / n_norm
    # Signed distance from origin: point·â
    alpha = plane.point.x * ux + plane.point.y * uy + plane.point.z * uz

    # IPNS: P = â − α·e₄ (grade-1 vector)
    ipns = basis.multivector({E1: ux, E2: uy, E3: uz, E4: -alpha})

    if opns:
        return ipns.dual()
    return ipns


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """Pseudoscalar.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: ``scale * e₁₂₃₄`` (grade‑4 pseudoscalar).
        *False* → IPNS: ``scale * 1`` (grade‑0 scalar).
    """
    opns_mv = basis.multivector({basis.pseudoscalar_id: scale})

    if opns:
        return opns_mv
    return opns_mv.dual()


# ═══════════════════════════════════════════════════════════════
# N3-only entity stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_sphere(
    basis: Algebra, center: Point, radius: float, *, opns: bool = True
) -> MV:
    raise ValueError("Spheres require conformal embedding (N3); not available in P3.")


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    raise ValueError("Circles require conformal embedding (N3); not available in P3.")


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    raise ValueError(
        "Point pairs require conformal embedding (N3); not available in P3."
    )


def create_homogeneous_point(
    basis: Algebra, pt: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    raise ValueError(
        "Homogeneous points require conformal embedding (N3); not available in P3."
    )


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) − sin(θ/2)·(ax·e₂₃ + ay·e₃₁ + az·e₁₂)``.

    Uses the standard exponential convention R = exp(−θ·B/2), matching
    the C++ ``CBasisP3::CreateRotor`` implementation.

    Same rotor as E3 — an overall scalar factor is irrelevant in
    projective space (Perwass §"Rotation in Projective Space").
    """
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E23: -math.sin(half) * axis.x,
            E13: math.sin(half) * axis.y,
            E12: -math.sin(half) * axis.z,
        }
    )


def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection on a *line* through the origin with direction *d*.

    Returns the bivector ``d∧e₄`` = d.x·e₁₄ + d.y·e₂₄ + d.z·e₃₄
    (Perwass: (N·e₄) A (e₄·N) = N(−a + e₄)N = −N a N − e₄,
    which projects to N a N + e₄ → correct line reflection).
    """
    return basis.multivector({E14: direction.x, E24: direction.y, E34: direction.z})


def create_reflection_plane(basis: Algebra, normal: Direction) -> MV:
    """Reflection in a *plane* through the origin with normal *n*.

    Returns a grade-1 **vector** n.x·e₁ + n.y·e₂ + n.z·e₃ (e₄ = 0).
    This is the IPNS of the plane.  Applied as versor N A N, it flips
    the normal component and keeps the in-plane component (Perwass).
    """
    return basis.multivector({E1: normal.x, E2: normal.y, E3: normal.z})


def create_reflection_point(basis: Algebra, point: Point) -> MV:
    """Reflection in a point."""
    return create_point(basis, point.x, point.y, point.z, opns=True)

def create_translator(basis: Algebra, x: float, y: float, z: float) -> MV:
    raise ValueError(
        "Translators require conformal embedding (N3); not available in P3."
    )


def create_dilator(basis: Algebra, factor: float) -> MV:
    raise ValueError("Dilators require conformal embedding (N3); not available in P3.")


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    raise ValueError(
        "Inversions require conformal embedding (N3); not available in P3."
    )


def create_motor(basis: Algebra, rotor, translator) -> MV:
    raise ValueError("Motors require conformal embedding (N3); not available in P3.")


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    raise ValueError(
        "General rotors require conformal embedding (N3); not available in P3."
    )
