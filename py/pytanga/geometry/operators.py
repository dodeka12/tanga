# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Algebra-independent operator (versor) data classes.

These data classes represent geometric operators (versors/transformations)
in Euclidean 3D space. They are pure data containers with no dependency
on pytanga.algebra, pytanga.MV, or pytanga.basis. Algebra-specific
conversion between MVs and these operator classes is handled by the
analysis and create modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .entities import Direction, Point


@dataclass(frozen=True)
class ReflectionLine:
    """Reflection on a line through the origin.

    Uses a grade-1 vector (the line direction) as versor.
    Applying ``d a d⁻¹`` keeps the component parallel to d unchanged
    and flips the perpendicular component.

    Supported algebras: E3, P3, N3/PGA3
    """

    direction: Direction

    def __repr__(self) -> str:
        return f"ReflLine(d={self.direction})"


@dataclass(frozen=True)
class ReflectionPlane:
    """Reflection in a plane through the origin.

    Uses a grade-2 bivector (``n·I⁻¹``) as versor, where *n* is the
    plane normal.  Applying ``−B a B̃`` keeps the in-plane component
    unchanged and flips the normal component.

    Supported algebras: E3, P3, N3/PGA3
    """

    normal: Direction

    def __repr__(self) -> str:
        return f"ReflPlane(n={self.normal})"


@dataclass(frozen=True)
class ReflectionOrigin:
    """Reflection about the origin.

    Uses e₄ as versor in P3: applying ``e₄ A e₄`` where A = Hop(a)
    gives ``−a + e₄``, which projects to ``−a``.

    Supported algebras: P3, N3/PGA3
    """

    def __repr__(self) -> str:
        return "ReflOrigin"


@dataclass(frozen=True)
class Inversion:
    """Inversion in a sphere.

    Perwass: ``S = Cop(center) − ½·radius²·e∞`` is the sphere IPNS
    that acts as the inversion operator via ``S X S``.

    Supported algebras: N3 only (needs eo)
    """

    center: Point
    radius: float = 1.0

    def __repr__(self) -> str:
        return f"Inv(c={self.center}, r={self.radius:.2f})"


@dataclass(frozen=True)
class Rotor:
    """A 3D rotation (even-grade versor: scalar + bivector).

    Supported algebras: E3, P3, N3/PGA3
    """

    angle: float
    axis: Direction

    def __repr__(self) -> str:
        deg = math.degrees(self.angle)
        return f"Rotor({deg:.1f}° about {self.axis})"


@dataclass(frozen=True)
class Translator:
    """A translation in 3D space.

    Supported algebras: N3/PGA3
    """

    vector: Direction

    def __repr__(self) -> str:
        return f"Transl({self.vector})"


@dataclass(frozen=True)
class Dilator:
    """A uniform dilation (scaling) about the origin.

    Supported algebras: N3 only (needs E = einfi∧eo)
    """

    factor: float

    def __repr__(self) -> str:
        return f"Dilator(×{self.factor:.2f})"


@dataclass(frozen=True)
class Motor:
    """A rigid body motion: rotation followed by translation.

    Supported algebras: N3/PGA3
    """

    rotor: Rotor
    translator: Translator

    def __repr__(self) -> str:
        return f"Motor({self.rotor}, {self.translator})"


@dataclass(frozen=True)
class GeneralRotor:
    """A general even-grade versor with rotor + translator bivector parts.

    Like a Motor but without the e123i (pseudoscalar-like) term.

    Supported algebras: N3 only (needs eo for full versor analysis)
    """

    rotor: Rotor
    translator: Translator

    def __repr__(self) -> str:
        return f"GenRotor({self.rotor}, {self.translator})"


@dataclass(frozen=True)
class GeneralDilator:
    """A general dilation with optional translation components.

    Supported algebras: N3 only (needs E = einfi∧eo)
    """

    factor: float
    translator: Optional[Translator] = None

    def __repr__(self) -> str:
        t = f", {self.translator}" if self.translator is not None else ""
        return f"GenDilator(×{self.factor:.2f}{t})"


# Backward-compatibility alias: Reflection → ReflectionPlane
Reflection = ReflectionPlane  # deprecated; use ReflectionLine/ReflectionPlane

# Union type for all operators
Operator = (
    ReflectionLine
    | ReflectionPlane
    | ReflectionOrigin
    | Inversion
    | Rotor
    | Translator
    | Dilator
    | Motor
    | GeneralRotor
    | GeneralDilator
)
