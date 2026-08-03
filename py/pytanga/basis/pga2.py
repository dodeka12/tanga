# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisPGA2 — Gunn/Dorst 3D PGA via 4D null‑vector embedding.

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
(ep, em) generates the 4‑dimensional algebra G(4, 0b1000); the
subspace {e₁, e₂, e₀} is algebraically isomorphic to the
Gunn/Dorst 3D PGA (2D Euclidean + 1D projective).
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisPGA2(Algebra):
    """Gunn/Dorst 3D PGA via 4D null‑vector embedding (2D Euclidean geometry).

    Attributes:
        e0: The Gunn/Dorst null vector (embedding: ep + em).
        e0_inv: Inverse of e0 (embedding: 0.5·ep − 0.5·em).
        e1, e2: Euclidean basis vectors.
        ep, em: Internal 4D embedding vectors (private; prefer e0).
    """

    # Blade bitmask IDs (dim=4: e₁=1, e₂=2, ep=4, em=8)
    E1: int = 1
    E2: int = 2
    EP: int = 4  # ep = e3,  ep² = +1 (internal embedding)
    EM: int = 8  # em = e4,  em² = -1 (internal embedding)
    E12: int = 3

    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(4, 0b1000, dtype, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.ep = mv({self.EP: 1})  # internal — e3
        self.em = mv({self.EM: 1})  # internal — e4
        # e0 = ep + em — the Gunn/Dorst null vector
        self.e0 = mv({self.EP: 1.0, self.EM: 1.0})
        # e0_inv = 0.5·ep − 0.5·em  →  ⟨e0·e0_inv⟩₀ = 1
        self.e0_inv = mv({self.EP: 0.5, self.EM: -0.5})

    # ── convenience constructors ──────────────────────────────────

    def point(self, x: float, y: float) -> MV:
        """Point in IPNS / dual form: ``x·e₁ + y·e₂ + e₀``.

        The OPNS form (grade‑2 bivector) is obtained via ``_pga2_dual(mv)``
        or by wedging two orthogonal lines (planes in 2D) through the point.
        """
        return self.multivector({1: x, 2: y, self.EP: 1.0, self.EM: 1.0})

    def direction(self, x: float, y: float) -> MV:
        """Direction / ideal point (IPNS): ``x·e₁ + y·e₂``
        (no e₀ component)."""
        return self.multivector({1: x, 2: y})

    def line(self, nx: float, ny: float, d: float = 0.0) -> MV:
        """Line in 2D (PGA line = grade‑1): ``nx·e₁ + ny·e₂ + d·e₀``.

        *d* is the signed distance from the origin.
        """
        return self.multivector({1: nx, 2: ny, self.EP: d, self.EM: d})

    # ── display ───────────────────────────────────────────────────

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis — e₀ as the null generator."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2), ("e0", self.e0)],
            self,
        )
