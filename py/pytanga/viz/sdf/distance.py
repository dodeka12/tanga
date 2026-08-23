# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Distance-function registry for the SDF viewer's algebra path.

Defines the fixed, algebra-agnostic set of distance functions that map a result
multivector coefficient vector ``r[]`` (from ``M·a``) to a scalar signed
distance. The enum value strings are the keys shared with the frontend's GLSL
snippet registry (``templates/sdf/algebra/distances.glsl``); a change to the
active distance function triggers a shader recompile on the frontend.

The same "name-keyed registry + recompile-on-change" mechanism is reused,
unchanged, for the opacity transfer axis (Phase 12).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class DistanceFunctionMeta:
    """Static metadata for one distance function."""

    glsl_name: str
    # GLSL parameter names (with their types), e.g. ("int k",).
    params: tuple[str, ...]
    description: str


class DistanceFunction(Enum):
    """Fixed distance functions; ``value`` is the shared registry key."""

    SCALAR_PSEUDO = "scalar_pseudo"
    MAGNITUDE = "magnitude"
    SCALAR = "scalar"
    GRADE = "grade"
    COMPONENT = "component"

    @property
    def meta(self) -> DistanceFunctionMeta:
        return _META[self]

    @property
    def glsl_name(self) -> str:
        return self.meta.glsl_name

    @property
    def params(self) -> tuple[str, ...]:
        return self.meta.params

    @property
    def description(self) -> str:
        return self.meta.description

    @property
    def signed(self) -> bool:
        """True if this distance function yields a signed distance.

        ``intersection``/``subtract`` (which negate and ``max`` distances)
        require a signed distance; ``magnitude`` and ``grade`` are unsigned
        (norm-of-vector), so they are unsuited to those boolean ops.
        """
        return self in (
            DistanceFunction.SCALAR_PSEUDO,
            DistanceFunction.SCALAR,
            DistanceFunction.COMPONENT,
        )

    @classmethod
    def default(cls) -> "DistanceFunction":
        return cls.SCALAR_PSEUDO


_META: dict[DistanceFunction, DistanceFunctionMeta] = {
    DistanceFunction.SCALAR_PSEUDO: DistanceFunctionMeta(
        glsl_name="distOfScalarPseudo",
        params=(),
        description=(
            "Signed: scalar + pseudoscalar blades (r[0] + r[I]) plus the "
            "magnitude of every other grade. Usable for boolean subtraction."
        ),
    ),
    DistanceFunction.MAGNITUDE: DistanceFunctionMeta(
        glsl_name="distOfMagnitude",
        params=(),
        description=(
            "Unsigned: the Euclidean norm of the whole coefficient vector. "
            "Only the zero-set is defined; unsuited to booleans."
        ),
    ),
    DistanceFunction.SCALAR: DistanceFunctionMeta(
        glsl_name="distOfScalar",
        params=(),
        description=(
            "Signed raw scalar blade (r[0]); degenerate when the scalar blade "
            "is never populated."
        ),
    ),
    DistanceFunction.GRADE: DistanceFunctionMeta(
        glsl_name="distOfGrade",
        params=("int k",),
        description="Norm of the grade-k slice of the result vector.",
    ),
    DistanceFunction.COMPONENT: DistanceFunctionMeta(
        glsl_name="distOfComponent",
        params=("int blade_id",),
        description="A single result blade coefficient r[blade_id].",
    ),
}