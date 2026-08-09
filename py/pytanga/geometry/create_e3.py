# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

# Reference: Perwass, "Geometric Algebra with Applications in Engineering",
#            Springer 2009, Chapter "Euclidean Space".

"""E3 entity/operator creation — converts dataclasses to MVs.

In E3 (Cl(3)), only entities and operators passing through the origin
are representable.  Points require projective (P3) or conformal (N3)
embedding.  Lines and planes not through the origin raise ``ValueError``.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .entities import Direction, Plane, Point

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs are sourced from BasisE3 as the single source of truth.
# The module-level aliases exist for backward compatibility with code
# that imports them directly (e.g. ``from .create_e3 import E12``).
# New code should prefer ``basis.E12`` or ``mv.algebra.E12``.
from pytanga.basis.e3 import BasisE3

E1 = BasisE3.E1
E2 = BasisE3.E2
E3 = BasisE3.E3
E12 = BasisE3.E12
E13 = BasisE3.E13
E23 = BasisE3.E23
E123 = BasisE3.E123


# ═══════════════════════════════════════════════════════════════
# Entity creation
# ═══════════════════════════════════════════════════════════════


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Points cannot be represented as null spaces in E3 — raise ValueError."""
    raise ValueError(
        "Points cannot be represented as null spaces in E3; "
        "use P3 or N3 for point representation."
    )


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Grade-1 vector ``x·e₁ + y·e₂ + z·e₃``.

    In E3 a grade-1 blade represents a line through the origin (OPNS)
    or a plane normal (IPNS).  This function produces the vector itself;
    the caller uses *opns* to control the dual.
    """
    if hasattr(basis, "vector"):
        return basis.vector(x, y, z)
    return basis.multivector({E1: x, E2: y, E3: z})


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Line through the origin in direction *d* (grade-1 vector).

    In E3 only lines through the origin can be represented.  If *origin*
    is not (0, 0, 0), a ``ValueError`` is raised.

    .. note::

       The returned MV is a grade-1 vector.  When analyzed with
       :func:`~pytanga.geometry.analysis_e3.analyze_entity` with
       ``opns=True``, it is recognized as a :class:`Direction`, not a
       :class:`Line`.  This is because E3 cannot distinguish a
       line-through-origin from a raw direction vector — the origin is
       always implicitly (0, 0, 0).  Use P3 or N3 for round-trips that
       preserve the ``Line`` entity type.
    """
    tol = 1e-12
    if abs(origin.x) > tol or abs(origin.y) > tol or abs(origin.z) > tol:
        raise ValueError(
            "In E3 only lines through the origin can be represented; "
            "use P3 or N3 for general lines."
        )
    return create_direction(basis, direction.x, direction.y, direction.z)


def create_plane(basis: Algebra, plane: Plane, *, opns: bool = True) -> MV:
    """Plane through origin.

    Uses the IPNS formula (grade-1 vector = normal *n*) as the simplest
    construction, then dualizes if *opns* is requested.

    Raises ``ValueError`` if the plane does not pass through the origin.
    """
    tol = 1e-12
    if abs(plane.point.x) > tol or abs(plane.point.y) > tol or abs(plane.point.z) > tol:
        raise ValueError(
            "In E3 only planes through the origin can be represented; "
            "use P3 or N3 for general planes."
        )

    # IPNS: grade-1 vector = plane normal (Perwass: NI_G(n))
    ipns = basis.multivector(
        {E1: plane.normal.x, E2: plane.normal.y, E3: plane.normal.z}
    )
    if opns:
        return ipns.dual()
    return ipns


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """Pseudoscalar ``scale * e₁₂₃``."""
    return basis.multivector({E123: scale})


# ═══════════════════════════════════════════════════════════════
# N3-only entity stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_sphere(
    basis: Algebra, center: Point, radius: float, *, opns: bool = True
) -> MV:
    raise ValueError("Spheres require conformal embedding (N3); not available in E3.")


def create_circle(
    basis: Algebra,
    center: Point,
    normal: Direction,
    radius: float,
    *,
    opns: bool = True,
) -> MV:
    raise ValueError("Circles require conformal embedding (N3); not available in E3.")


def create_point_pair(basis: Algebra, a: Point, b: Point, *, opns: bool = True) -> MV:
    raise ValueError(
        "Point pairs require conformal embedding (N3); not available in E3."
    )


def create_homogeneous_point(
    basis: Algebra, pt: Point, weight: float = 1.0, *, opns: bool = True
) -> MV:
    raise ValueError(
        "Homogeneous points require conformal embedding (N3); not available in E3."
    )


# ═══════════════════════════════════════════════════════════════
# Operator creation
# ═══════════════════════════════════════════════════════════════


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) + sin(θ/2)·(ax·e₂₃ + ay·e₃₁ + az·e₁₂)``.

    Perwass defines the rotor as ``R = cos(θ/2) − sin(θ/2)·N₂`` where
    N₂ is the rotation *plane* bivector.  Our convention uses the axis
    vector *r* (normal to the plane) with N₂ = r·I.  Because I² = −1
    and I = −Ĩ in Cl(3), the sign flips, giving ``+ sin(θ/2)·axis_bivector``.
    The two conventions are equivalent: both rotate by θ about the axis
    in the right-handed sense.
    """
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E23: math.sin(half) * axis.x,
            E13: -math.sin(half) * axis.y,
            E12: math.sin(half) * axis.z,
        }
    )


def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection on a *line* through the origin with direction *d*.

    Returns a grade-1 **vector** ``d.x·e₁ + d.y·e₂ + d.z·e₃``.
    Applying ``d a d⁻¹`` to a vector *a* keeps the component parallel
    to *d* unchanged and flips the perpendicular component.
    """
    return basis.multivector({E1: direction.x, E2: direction.y, E3: direction.z})


def create_reflection_plane(basis: Algebra, normal: Direction) -> MV:
    """Reflection in a *plane* through the origin with normal *n*.

    Returns a grade-2 **bivector** ``n·I⁻¹`` = nx·e₂₃ + ny·e₃₁ + nz·e₁₂.
    Applying ``−B a B̃`` keeps the in-plane component unchanged and
    flips the normal component.  The ``−1`` from ``(−1)^(k+1)`` is
    built into the bivector form via I² = −1 in Cl(3).
    """
    return basis.multivector(
        {
            E23: normal.x,
            E13: -normal.y,
            E12: normal.z,
        }
    )


# ═══════════════════════════════════════════════════════════════
# N3-only operator stubs — raise ValueError
# ═══════════════════════════════════════════════════════════════


def create_translator(basis: Algebra, x: float, y: float, z: float) -> MV:
    raise ValueError(
        "Translators require conformal embedding (N3); not available in E3."
    )


def create_dilator(basis: Algebra, factor: float) -> MV:
    raise ValueError("Dilators require conformal embedding (N3); not available in E3.")


def create_inversion(basis: Algebra, center: Point, radius: float = 1.0) -> MV:
    raise ValueError(
        "Inversions require conformal embedding (N3); not available in E3."
    )


def create_motor(basis: Algebra, rotor, translator) -> MV:
    raise ValueError("Motors require conformal embedding (N3); not available in E3.")


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    raise ValueError(
        "General rotors require conformal embedding (N3); not available in E3."
    )


def create_reflection_origin(basis: Algebra) -> MV:
    raise ValueError(
        "Reflection about the origin requires projective (P3) embedding; "
        "not available in E3 (no e₄ dimension)."
    )
