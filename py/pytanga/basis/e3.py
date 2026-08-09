# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisE3 — Euclidean 3D basis (G(3, 0))."""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisE3(Algebra):
    """Euclidean 3D geometric algebra G(3, 0) with named blade attributes."""

    # Blade bitmask IDs (Perwass Table GAGeo:G3AlgBasis)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7

    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(3, 0, dtype, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})
        self.e12 = self.op(self.e1, self.e2)
        self.e31 = self.op(self.e3, self.e1)
        self.e13 = -self.e31  # alias matching Perwass notation e₁₃ = −e₃₁
        self.e23 = self.op(self.e2, self.e3)
        self.I = mv({self.pseudoscalar_id: 1})

    def vector(self, x=0.0, y=0.0, z=0.0) -> MV:
        """Create a 3D vector: x·e1 + y·e2 + z·e3.

        Can also be called with a :class:`~pytanga.geometry.entities.Point`
        or :class:`~pytanga.geometry.entities.Direction` as a single argument.
        """
        from pytanga.geometry.entities import Direction, Point

        if isinstance(x, (Point, Direction)):
            return self.multivector({1: x.x, 2: x.y, 4: x.z})
        return self.multivector({1: x, 2: y, 4: z})

    def rnd_vector(
        self,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
        z_range: tuple[float, float],
    ) -> MV:
        """Random 3D vector: x·e1 + y·e2 + z·e3."""
        return self.vector(
            self.rng.uniform(x_range[0], x_range[1]),
            self.rng.uniform(y_range[0], y_range[1]),
            self.rng.uniform(z_range[0], z_range[1]),
        )

    def rotor(self, theta: float, axis: MV) -> MV:
        """Rotor for rotation by angle ``theta`` about the given *axis*.

        Convenience method that delegates to :func:`~pytanga.geometry.create_e3.create_rotor`.
        """
        from pytanga.geometry.create_e3 import create_rotor
        from pytanga.geometry.entities import Direction

        axis = axis.normalized()
        return create_rotor(
            self,
            float(theta),
            Direction(float(axis[1]), float(axis[2]), float(axis[4])),
        )

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis for all 2^3 = 8 blades (grades 0–3)."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2), ("e3", self.e3)],
            self,
        )
