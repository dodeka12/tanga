# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisN3 — Null 3D algebra (G(5, 0b10000)) with named blade attributes.

Mirrors CBasisN3 from the C++ library.  ep (e4) squares to +1, em (e5)
squares to -1.  The composed null vectors einf and eo follow the definitions
in _CBasisN3::_Init():

    einf = ep + em          → {8: 1.0,  16: 1.0}
    eo   = 0.5·em - 0.5·ep  → {8: -0.5, 16: 0.5}
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra

# Blade IDs for the two extra dimensions in G(5, 0b10000).
_EP: int = 8  # ep = e4,  ep² = +1
_EM: int = 16  # em = e5,  em² = -1


class BasisN3(Algebra):
    """Null 3D algebra G(5, 0b10000) — raw named blades, no geometric interpretation."""

    # Blade bitmask IDs (dim=5: e₁=1, e₂=2, e₃=4, ep=8, em=16)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    EP: int = 8  # ep = e4,  ep² = +1
    EM: int = 16  # em = e5,  em² = -1
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(5, 0b10000, dtype, opns=opns, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})
        self.ep = mv({_EP: 1})
        self.em = mv({_EM: 1})
        # Composed null vectors (from _CBasisN3::_Init())
        self.einf = mv({_EP: 1.0, _EM: 1.0})  # ep + em
        self.eo = mv({_EP: -0.5, _EM: 0.5})  # 0.5·em - 0.5·ep
        self.I = mv({self.pseudoscalar_id: 1})
        self.E = self.einf ^ self.eo

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis for all 2^5 = 32 blades (grades 0–5).

        The grade-1 generators are {e1, e2, e3, einf, eo}.  Null blades
        (those with ``ip(B,B) = 0``) use cross-inner-products with the
        einf ↔ eo swapped blade for coefficient extraction.
        """
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [
                ("e1", self.e1),
                ("e2", self.e2),
                ("e3", self.e3),
                ("einf", self.einf),
                ("eo", self.eo),
            ],
            self,
        )
