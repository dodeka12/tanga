# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Euclidean Space".

"""E2 entity/operator creation — converts dataclasses to MVs.

In E2 (Cl(2)), only entities and operators passing through the origin
are representable.  Points require projective (P2) or conformal (N2)
embedding.  Lines not through the origin raise ``ValueError``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import Direction, Point

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs — sourced from BasisE2 as single source of truth.
from pytanga.basis.e2 import BasisE2

E1 = BasisE2.E1
E2 = BasisE2.E2
E12 = BasisE2.E12


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Euclidean point components — ``x·e₁ + y·e₂`` (OPNS/IPNS independent).

    A point cannot be represented as a null space in E2 (that requires
    P2 or N2), but its Euclidean coordinates map to the e₁/e₂ components
    independent of the OPNS/IPNS flag.
    """
    return basis.multivector({E1: x, E2: y})


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Grade-1 vector ``x·e₁ + y·e₂``.

    In E2 a grade-1 blade represents a line through the origin (OPNS)
    or the normal to a line (IPNS).  OPNS returns the vector directly;
    IPNS returns its dual.
    """
    opns_mv = basis.multivector({E1: x, E2: y})
    if opns:
        return opns_mv
    return opns_mv.dual()


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Line through the origin in direction *d* (grade-1 vector).

    In E2 only lines through the origin can be represented.  If *origin*
    is not (0, 0, 0), a ``ValueError`` is raised.
    """
    tol = 1e-12
    if abs(origin.x) > tol or abs(origin.y) > tol or abs(origin.z) > tol:
        raise ValueError(
            "In E2 only lines through the origin can be represented; "
            "use P2 or N2 for general lines."
        )
    return create_direction(basis, direction.x, direction.y, 0.0, opns=opns)


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """OPNS pseudoscalar ``scale * e₁₂``; IPNS is the scalar ``scale``."""
    opns_mv = basis.multivector({E12: scale})
    if opns:
        return opns_mv
    return opns_mv.dual()


# ═══════════════════════════════════════════════════════════════
# N2-only entity stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_sphere(
    basis: Algebra, center: Point, radius: float, *, opns: bool = True
) -> MV:
    raise ValueError("Spheres require conformal embedding (N2); not available in E2.")


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    raise ValueError("Circles require conformal embedding (N2); not available in E2.")


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    raise ValueError(
        "Point pairs require conformal embedding (N2); not available in E2."
    )


def create_homogeneous_point(
    basis: Algebra, pt: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    raise ValueError(
        "Homogeneous points require conformal embedding (N2); not available in E2."
    )


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) + sin(θ/2)·e₁₂``.

    In 2D the rotation axis is always the pseudoscalar e₁₂ (the plane).
    The rotor has only scalar + e₁₂ bivector components.
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

    Returns a grade-1 **vector** ``d.x·e₁ + d.y·e₂``.
    Applying ``d a d⁻¹`` to a vector *a* keeps the component parallel
    to *d* unchanged and flips the perpendicular component.
    """
    return basis.multivector({E1: direction.x, E2: direction.y})


# ═══════════════════════════════════════════════════════════════
# N2-only operator stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_translator(basis: Algebra, x: float, y: float, z: float) -> MV:
    raise ValueError(
        "Translators require conformal embedding (N2); not available in E2."
    )


def create_dilator(basis: Algebra, factor: float) -> MV:
    raise ValueError("Dilators require conformal embedding (N2); not available in E2.")


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    raise ValueError(
        "Inversions require conformal embedding (N2); not available in E2."
    )


def create_motor(basis: Algebra, rotor, translator) -> MV:
    raise ValueError("Motors require conformal embedding (N2); not available in E2.")


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    raise ValueError(
        "General rotors require conformal embedding (N2); not available in E2."
    )


def create_reflection_origin(basis: Algebra) -> MV:
    raise ValueError(
        "Reflection about the origin requires projective (P2) embedding; "
        "not available in E2 (no e₃ dimension)."
    )
