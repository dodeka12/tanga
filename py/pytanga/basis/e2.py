# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisE2 — Euclidean 2D basis (G(2, 0))."""

from __future__ import annotations

import math
from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisE2(Algebra):
    """Euclidean 2D geometric algebra G(2, 0) with named blade attributes."""

    # Blade bitmask IDs (dim=2)
    E1: int = 1
    E2: int = 2
    E12: int = 3

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(2, 0, dtype, opns=opns, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e12 = self.op(self.e1, self.e2)
        self.I = mv({self.pseudoscalar_id: 1})

    def vector(self, x: float, y: float) -> MV:
        """Create a 2D vector: x·e1 + y·e2."""
        return self.multivector({1: x, 2: y})

    def rnd_vector(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
    ) -> MV:
        """Random 2D vector: x·e1 + y·e2."""
        return self.vector(
            self.rng.uniform(x_range[0], x_range[1]),
            self.rng.uniform(y_range[0], y_range[1]),
        )

    def rotor(self, theta: float, axis: MV) -> MV:
        """Rotor for rotation by angle ``theta`` about the given *axis* bivector.

        In 2D the axis is always a multiple of e12.
        """
        axis = axis.normalized()
        return math.cos(theta / 2.0) + axis * math.sin(theta / 2.0)

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis for all 2^2 = 4 blades (grades 0–2)."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2)],
            self,
        )
