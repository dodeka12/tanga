# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Quadric-space bases — Euclidean-rescaled ``Algebra(6, 0)`` / ``Algebra(10, 0)``.

Perwass's projective conic space ``CA{6}`` (and its 3D quadric generalisation
``CA{10}``) uses a non-Euclidean basis ``e₁…e₆`` with squared norms
``(1, 1, 2, 2, 2, 1)``.  Here the basis is rescaled to Euclidean vectors
``b₁…b₆`` (all ``bᵢ·bᵢ = 1``, via ``b₃₄₅ = e₃₄₅/√2``) so that the plain
``Algebra(6, 0)`` / ``Algebra(10, 0)`` metric can be used unchanged.  The
``√2/2`` factors live only in :mod:`pytanga.quadric._embedding` and
:mod:`pytanga.quadric._mapping`.
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra


class BasisQ2(Algebra):
    """2D projective quadric space ``CA{6}`` — Euclidean-rescaled ``G(6, 0)``.

    Blade bitmask IDs: ``b1=1, b2=2, b3=4, b4=8, b5=16, b6=32``.
    """

    B1: int = 1
    B2: int = 2
    B3: int = 4
    B4: int = 8
    B5: int = 16
    B6: int = 32

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(6, 0, dtype, opns=opns, **kw)
        mv = self.multivector
        self.b1 = mv({1: 1})
        self.b2 = mv({2: 1})
        self.b3 = mv({4: 1})
        self.b4 = mv({8: 1})
        self.b5 = mv({16: 1})
        self.b6 = mv({32: 1})
        self.I = mv({self.pseudoscalar_id: 1})

    @cached_property
    def _display_basis(self) -> list:
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [
                ("b1", self.b1),
                ("b2", self.b2),
                ("b3", self.b3),
                ("b4", self.b4),
                ("b5", self.b5),
                ("b6", self.b6),
            ],
            self,
        )


class BasisQ3(Algebra):
    """3D projective quadric space — Euclidean-rescaled ``G(10, 0)``.

    Blade bitmask IDs: ``b1=1, b2=2, b3=4, b4=8, b5=16, b6=32, b7=64, b8=128,
    b9=256, b10=512``.
    """

    B1: int = 1
    B2: int = 2
    B3: int = 4
    B4: int = 8
    B5: int = 16
    B6: int = 32
    B7: int = 64
    B8: int = 128
    B9: int = 256
    B10: int = 512

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(10, 0, dtype, opns=opns, **kw)
        mv = self.multivector
        self.b1 = mv({1: 1})
        self.b2 = mv({2: 1})
        self.b3 = mv({4: 1})
        self.b4 = mv({8: 1})
        self.b5 = mv({16: 1})
        self.b6 = mv({32: 1})
        self.b7 = mv({64: 1})
        self.b8 = mv({128: 1})
        self.b9 = mv({256: 1})
        self.b10 = mv({512: 1})
        self.I = mv({self.pseudoscalar_id: 1})

    @cached_property
    def _display_basis(self) -> list:
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [
                ("b1", self.b1),
                ("b2", self.b2),
                ("b3", self.b3),
                ("b4", self.b4),
                ("b5", self.b5),
                ("b6", self.b6),
                ("b7", self.b7),
                ("b8", self.b8),
                ("b9", self.b9),
                ("b10", self.b10),
            ],
            self,
        )
