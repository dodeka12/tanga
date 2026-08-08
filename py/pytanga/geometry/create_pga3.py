# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA3 entity/operator creation — converts dataclasses to MVs.

Implements the Gunn/Dorst plane‑based PGA model (G(3, 0, 1)) within the
5D algebra via the null‑vector embedding e₀ = ep + em.  This embedding is
necessary because TANGA does not support zero‑squaring basis vectors
natively; see ``docs/py/basis/pga_null_embedding.md``.

References:
  Gunn, *Geometric algebras for Euclidean geometry* (arXiv:1411.6502, 2016)
  Dorst, *A Guided Tour to the Plane‑Based Geometric Algebra PGA* (2020)
  ``docs/py/basis/pga_null_embedding.md``
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._pga3_utils import (
    E1,
    E2,
    E3,
    E12,
    E13,
    E23,
    E123,
    EM,
    EP,
    _get_e0,
)
from .entities import Direction, Plane, Point
from .operators import GeneralRotor, ReflectionLine, ReflectionOrigin, Rotor, Translator

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV


# ── Entities ──────────────────────────────────────────────────


def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Create a PGA3 point.

    *opns=True* (default):  grade‑3 trivector (intersection of three planes
      ``(e₁ - x·e₀) ∧ (e₂ - y·e₀) ∧ (e₃ - z·e₀)``).

    *opns=False* (IPNS):  grade‑1 vector ``x·e₁ + y·e₂ + z·e₃ + e₀``.
    """
    p_ipns = basis.multivector({E1: x, E2: y, E3: z, EP: 1.0, EM: 1.0})
    if not opns:
        # IPNS (dual) form
        return p_ipns

    return p_ipns.dual()


def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Create a PGA3 direction (ideal point).

    *opns=True*:  grade‑3 trivector (same construction as point but
      the dual has no e₀ component).

    *opns=False* (IPNS):  grade‑1 vector ``x·e₁ + y·e₂ + z·e₃``.
    """
    d_ipns = basis.multivector({E1: -x, E2: -y, E3: -z})
    if not opns:
        return d_ipns

    return d_ipns.dual()


def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Create a PGA3 line (grade‑2 bivector = intersection of two planes).

    The line is the intersection of two planes that both contain the
    line: one with normal orthogonal to the direction, and one with
    the direction itself as normal (plane perpendicular to direction).
    """
    dx, dy, dz = direction.x, direction.y, direction.z

    # Choose a direction n1 perpendicular to the line direction
    if abs(dx) < 0.9:
        n1 = (0.0, dz, -dy)
    elif abs(dy) < 0.9:
        n1 = (dz, 0.0, -dx)
    else:
        n1 = (dy, -dx, 0.0)
    # Ensure n1 is not degenerately zero
    if n1[0] == 0.0 and n1[1] == 0.0 and n1[2] == 0.0:
        n1 = (0.0, 1.0, 0.0)

    n1_norm = math.sqrt(n1[0] ** 2 + n1[1] ** 2 + n1[2] ** 2)
    n1 = (n1[0] / n1_norm, n1[1] / n1_norm, n1[2] / n1_norm)

    # Second normal = direction × n1
    n2x = dy * n1[2] - dz * n1[1]
    n2y = dz * n1[0] - dx * n1[2]
    n2z = dx * n1[1] - dy * n1[0]

    # Signed distances: n·origin
    d1 = n1[0] * origin.x + n1[1] * origin.y + n1[2] * origin.z
    d2 = n2x * origin.x + n2y * origin.y + n2z * origin.z

    if not opns:
        # IPNS form: dual of OPNS
        mv = create_line(basis, origin, direction, opns=True)
        return mv.dual()

    # OPNS: wedge of two planes
    p1 = basis.multivector({E1: n1[0], E2: n1[1], E3: n1[2], EP: d1, EM: d1})
    p2 = basis.multivector({E1: n2x, E2: n2y, E3: n2z, EP: d2, EM: d2})
    return p1.op(p2)


def create_plane(basis: Algebra, plane: Plane, *, opns: bool = True) -> MV:
    """Create a PGA3 plane.

    *opns=True* (default):  grade‑1 vector ``nx·e₁ + ny·e₂ + nz·e₃ + d·e₀``
      where *d* is the signed distance from origin.

    *opns=False* (IPNS):  5D ``dual()`` of the OPNS blade.
    """
    nx, ny, nz = plane.normal.x, plane.normal.y, plane.normal.z
    # Signed distance from the origin
    d = -(nx * plane.point.x + ny * plane.point.y + nz * plane.point.z)

    mv = basis.multivector({E1: nx, E2: ny, E3: nz, EP: d, EM: d})
    if not opns:
        mv = mv.dual()
    return mv


def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """PGA3 Space: ``scale · e₁ ∧ e₂ ∧ e₃ ∧ e₀``."""
    if hasattr(basis, "e1"):
        mv = basis.e1.op(basis.e2).op(basis.e3).op(_get_e0(basis)) * scale
    else:
        mv = basis.multivector(
            {
                7: scale,  # e123
                EP: scale,
                EM: scale,  # e₀
            }
        ).grade(4)  # grade-4 part
    if not opns:
        mv = mv.dual()  # IPNS is a scalar
    return mv


# ── Operators (no opns flag) ──────────────────────────────────


def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) + sin(θ/2)·(ax·e₂₃ + ay·e₃₁ + az·e₁₂)``."""
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
    """``T = 1 + 0.5·(dx·e₁∧e₀ + dy·e₂∧e₀ + dz·e₃∧e₀)``."""
    return basis.multivector(
        {
            0: 1.0,
            9: 0.5 * dx,
            17: 0.5 * dx,
            10: 0.5 * dy,
            18: 0.5 * dy,
            12: 0.5 * dz,
            20: 0.5 * dz,
        }
    )


def create_motor(basis: Algebra, rotor: Rotor, translator: Translator) -> MV:
    """``T · R`` = translation followed by rotation."""
    t_mv = create_translator(
        basis, translator.vector.x, translator.vector.y, translator.vector.z
    )
    r_mv = create_rotor(basis, rotor.angle, rotor.axis)
    return t_mv.gp(r_mv)


def create_reflection(basis: Algebra, normal: Direction) -> MV:
    """Grade‑1 reflection vector (Euclidean)."""
    return basis.multivector({E1: normal.x, E2: normal.y, E3: normal.z})


# Alias: the create.py dispatcher calls create_reflection_plane
create_reflection_plane = create_reflection


def create_general_rotor(
    basis: Algebra, angle: float, axis: Direction, origin: Point
) -> MV:
    """General rotor: rotation about an arbitrary origin point.

    ``G = T · R · T̃`` — the conjugation cancels the translator's effect on
    position, leaving a pure rotation about the origin point.

    The result has grades {0, 2} (scalar + bivector), distinguishing it from
    a Motor which also has a grade‑4 term.
    """
    t_mv = create_translator(basis, origin.x, origin.y, origin.z)
    r_mv = create_rotor(basis, angle, axis)
    return t_mv.gp(r_mv).gp(t_mv.rev())


def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection on a line through the origin.

    In PGA3, this is a bivector ``d∧e₀`` (grade 2).
    """
    return basis.multivector(
        {
            9: direction.x,
            17: direction.x,  # e1∧ep, e1∧em
            10: direction.y,
            18: direction.y,  # e2∧ep, e2∧em
            12: direction.z,
            20: direction.z,  # e3∧ep, e3∧em
        }
    )


def create_reflection_origin(basis: Algebra) -> MV:
    """Reflection about the origin.

    In PGA3, this is the trivector ``e₁∧e₂∧e₃`` (grade 3).
    """
    if hasattr(basis, "e1"):
        return basis.e1.op(basis.e2).op(basis.e3)
    return basis.multivector({E123: 1.0}).grade(3)
