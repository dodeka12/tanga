# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Opacity transfer-function registry for the SDF viewer (Phase 12).

Mirrors the Phase 3 distance-function registry contract: a fixed set of
distance→opacity transfers, keyed by name, selected from the backend and
recompiled into the shader with no branching. The per-object ``opacity`` doubles
as the falloff breadth ``ε`` for the non-``step`` transfers (see
``templates/sdf/algebra/opacities.js``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class OpacityTransferMeta:
    """Static metadata for one opacity transfer function."""

    glsl_name: str
    # GLSL parameter names (with their types), e.g. ("float epsilon",).
    params: tuple[str, ...]
    description: str


class OpacityTransfer(Enum):
    """Fixed opacity transfers; ``value`` is the shared registry key."""

    STEP = "step"
    LINEAR = "linear"
    SIGMOID = "sigmoid"

    @property
    def meta(self) -> OpacityTransferMeta:
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

    @classmethod
    def default(cls) -> "OpacityTransfer":
        return cls.STEP


_META: dict[OpacityTransfer, OpacityTransferMeta] = {
    OpacityTransfer.STEP: OpacityTransferMeta(
        glsl_name="opacityOfStep",
        params=(),
        description="Crisp solid: opaque inside, transparent outside.",
    ),
    OpacityTransfer.LINEAR: OpacityTransferMeta(
        glsl_name="opacityOfLinear",
        params=("float epsilon",),
        description="Soft band around the zero-surface (falloff breadth ε).",
    ),
    OpacityTransfer.SIGMOID: OpacityTransferMeta(
        glsl_name="opacityOfSigmoid",
        params=("float epsilon",),
        description="Smooth soft edge (falloff breadth ε).",
    ),
}
