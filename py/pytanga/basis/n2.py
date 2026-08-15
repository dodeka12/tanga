# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisN2 — Null 2D algebra (G(4, 0b1000)) with named blade attributes.

Mirrors CBasisN2 from the C++ library.  ep (e3) squares to +1, em (e4)
squares to -1.  The composed null vectors einf and eo follow the definitions
in _CBasisN3::_Init():

    einf = ep + em          → {4: 1.0,  8: 1.0}
    eo   = 0.5·em - 0.5·ep  → {4: -0.5, 8: 0.5}
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra

# Blade IDs for the two extra dimensions in G(4, 0b1000).
_EP: int = 4  # ep = e3,  ep² = +1
_EM: int = 8  # em = e4,  em² = -1


class BasisN2(Algebra):
    """Null 2D algebra G(4, 0b1000) — raw named blades, no geometric interpretation."""

    # Blade bitmask IDs (dim=4: e₁=1, e₂=2, ep=4, em=8)
    E1: int = 1
    E2: int = 2
    EP: int = 4  # ep = e3,  ep² = +1
    EM: int = 8  # em = e4,  em² = -1
    E12: int = 3

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(4, 0b1000, dtype, opns=opns, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.ep = mv({_EP: 1})
        self.em = mv({_EM: 1})
        # Composed null vectors (from _CBasisN3::_Init())
        self.einf = mv({_EP: 1.0, _EM: 1.0})  # ep + em
        self.eo = mv({_EP: -0.5, _EM: 0.5})  # 0.5·em - 0.5·ep
        self.I = mv({self.pseudoscalar_id: 1})
        self.E = self.einf ^ self.eo

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis for all 2^4 = 16 blades (grades 0–4).

        The grade-1 generators are {e1, e2, einf, eo}.  Null blades
        (those with ``ip(B,B) = 0``) use cross-inner-products with the
        einf ↔ eo swapped blade for coefficient extraction.
        """
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [
                ("e1", self.e1),
                ("e2", self.e2),
                ("einf", self.einf),
                ("eo", self.eo),
            ],
            self,
        )
