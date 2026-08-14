# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisP2 — Projective 2D basis (G(3, 0), homogeneous coordinates)."""

from __future__ import annotations

import math
from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisP2(Algebra):
    """Projective 2D geometric algebra G(3, 0) with named blade attributes."""

    # Blade bitmask IDs (dim=3: e₁=1, e₂=2, e₃=4)
    E1: int = 1
    E2: int = 2
    E3: int = 4  # homogeneous direction
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7

    def __init__(
        self,
        dtype: str = "float64",
        seed: int | None = None,
        opns: bool = True,
        **kw,
    ) -> None:
        super().__init__(3, 0, dtype, seed=seed, opns=opns, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})  # homogeneous direction
        self.e123 = mv({7: 1})
        self.I = mv({self.pseudoscalar_id: 1})

    def point(self, x: float, y: float) -> MV:
        """Homogeneous point: x·e1 + y·e2 + e3."""
        return self.multivector({1: x, 2: y, 4: 1})

    def direction(self, x: float, y: float) -> MV:
        """Homogeneous direction: x·e1 + y·e2."""
        return self.multivector({1: x, 2: y})

    def rnd_point(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
    ) -> MV:
        """Random homogeneous point: x·e1 + y·e2 + e3."""
        return self.point(
            self.rng.uniform(x_range[0], x_range[1]),
            self.rng.uniform(y_range[0], y_range[1]),
        )

    def rnd_direction(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
    ) -> MV:
        """Random homogeneous direction: x·e1 + y·e2."""
        return self.direction(
            self.rng.uniform(x_range[0], x_range[1]),
            self.rng.uniform(y_range[0], y_range[1]),
        )

    def rotor(self, theta: float, axis: MV) -> MV:
        """Rotor for rotation by angle theta about the given axis."""
        axis = axis.normalized()
        plane = self.e123 | axis
        return math.cos(theta / 2.0) + plane * math.sin(theta / 2.0)

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis for all 2^3 = 8 blades (grades 0–3)."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2), ("e3", self.e3)],
            self,
        )
