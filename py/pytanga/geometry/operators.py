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
from dataclasses import dataclass, field
from typing import Optional

from .entities import Direction, Plane, Point


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
    """A uniform dilation (scaling) about an origin point.

    Form: ``D_t = T · D · T̃`` where T translates from the global origin
    to the dilation center and ``D = 1 + (1−d)/(1+d)·E`` is the
    origin‑centered dilator (E = e∞∧e₀, Perwass).

    When ``origin=(0,0,0)``, this is a pure dilator about the origin:
    ``D = 1 + (1−d)/(1+d)·E``, sandwich ``D·p·D̃`` scales p by factor d.

    Supported algebras: N3/N2 only (needs E = e∞∧e₀)
    """

    factor: float
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))

    def __repr__(self) -> str:
        if self.origin.x == 0 and self.origin.y == 0 and self.origin.z == 0:
            return f"Dilator(×{self.factor:.2f})"
        return f"Dilator(×{self.factor:.2f} at {self.origin})"


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
    """A rotation about an arbitrary origin point.

    The underlying MV is ``G = T · R · T̃`` where *T* translates from
    the global origin to the rotation center and *R* is the rotor.

    In 2D the axis is always ``Dir(0, 0, 1)`` and origin z=0.
    """

    angle: float
    axis: Direction
    origin: Point = field(default_factory=lambda: Point(0, 0, 0))

    def __repr__(self) -> str:
        deg = math.degrees(self.angle)
        return f"GenRotor({deg:.1f}° about {self.axis} at {self.origin})"


@dataclass(frozen=True)
class TripleReflection:
    """Three successive plane reflections — reflection × rotor/translator.

    Because three reflections can be grouped as (rotor + reflection)
    or (translator + reflection) or (general rotor + reflection) in
    multiple ways, the decomposition into rotor+translator is not unique.
    This class preserves the raw plane information for downstream use.
    """

    planes: tuple[Plane, Plane, Plane]

    def __repr__(self) -> str:
        return f"TripleRefl({self.planes[0]}, {self.planes[1]}, {self.planes[2]})"


@dataclass(frozen=True)
class VersorFactors:
    """Unclassified versor — raw grade-1 factors from blade factorization.

    Used as a fallback when a versor cannot be classified as a specific
    operator (e.g. mixed dilator+rotor combinations in N3/N2).
    """

    factors: tuple = ()  # tuple of MV (grade-1 vectors)

    def __repr__(self) -> str:
        return f"VersorFactors({len(self.factors)} factors)"


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
    | TripleReflection
    | VersorFactors
)
