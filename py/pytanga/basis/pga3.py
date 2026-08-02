# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisPGA3 — Gunn/Dorst 4D PGA via 5D null‑vector embedding.

Implements the plane‑based projective geometric algebra described in:

- Charles Gunn, *Geometric algebras for Euclidean geometry*,
  arXiv:1411.6502 (2016).

- Leo Dorst, *A Guided Tour to the Plane‑Based Geometric Algebra PGA*,
  bivector.net/PGA4CS.html (2020).

The Gunn/Dorst model uses a single null basis vector ``e₀`` with
``e₀² = 0``.  Since TANGA's Clifford algebra only supports metric
signatures with squares ±1, the null vector is modelled via the
embedding

    e₀ → ep + em,   ep² = +1, em² = -1,

as documented in ``docs/py/basis/pga_null_embedding.md``.  The pair
(ep, em) generates the 5‑dimensional algebra G(5, 0b10000); the
subspace {e₁, e₂, e₃, e₀} is algebraically isomorphic to the
Gunn/Dorst 4D PGA.
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisPGA3(Algebra):
    """Gunn/Dorst 4D PGA via 5D null‑vector embedding.

    Attributes:
        e0: The Gunn/Dorst null vector (embedding: ep + em).
        e0_inv: Inverse of e0 (embedding: 0.5·ep − 0.5·em).
        e1, e2, e3: Euclidean basis vectors.
        ep, em: Internal 5D embedding vectors (private; prefer e0).
    """

    # Blade bitmask IDs (dim=5: e₁=1, e₂=2, e₃=4, ep=8, em=16)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    EP: int = 8  # ep = e4,  ep² = +1 (internal embedding)
    EM: int = 16  # em = e5,  em² = -1 (internal embedding)
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7

    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(5, 0b10000, dtype, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})
        self.ep = mv({self.EP: 1})  # internal — e4
        self.em = mv({self.EM: 1})  # internal — e5
        # e0 = ep + em — the Gunn/Dorst null vector
        self.e0 = mv({self.EP: 1.0, self.EM: 1.0})
        # e0_inv = 0.5·ep − 0.5·em  →  ⟨e0·e0_inv⟩₀ = 1
        self.e0_inv = mv({self.EP: 0.5, self.EM: -0.5})

    # ── convenience constructors ──────────────────────────────────

    def point(self, x: float, y: float, z: float) -> MV:
        """Point in IPNS / dual form: ``x·e₁ + y·e₂ + z·e₃ + e₀``.

        The OPNS form (grade‑3 trivector) is obtained via ``_pga3_dual(mv)``
        or by wedging three orthogonal planes through the point.
        """
        return self.multivector({1: x, 2: y, 4: z, self.EP: 1.0, self.EM: 1.0})

    def direction(self, x: float, y: float, z: float) -> MV:
        """Direction / ideal point (IPNS): ``x·e₁ + y·e₂ + z·e₃``
        (no e₀ component)."""
        return self.multivector({1: x, 2: y, 4: z})

    def plane(self, nx: float, ny: float, nz: float, d: float = 0.0) -> MV:
        """Plane (grade‑1): ``nx·e₁ + ny·e₂ + nz·e₃ + d·e₀``.

        *d* is the signed distance from the origin.
        """
        return self.multivector({1: nx, 2: ny, 4: nz, self.EP: d, self.EM: d})

    # ── display ───────────────────────────────────────────────────

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis — e₀ as the null generator."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2), ("e3", self.e3), ("e0", self.e0)],
            self,
        )
