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
        e0_recip: Reciprocal of e0 (embedding: 0.5·ep − 0.5·em).
        e1, e2: Euclidean basis vectors.
        ep, em: Internal 4D embedding vectors (private; prefer e0).
    """

    # User-facing meet/join follow the Gunn/Dorst convention
    # (meet = intersection ∧, join = union/span ∨).
    _swap_meet_join: bool = True

    # Blade bitmask IDs (dim=4: e₁=1, e₂=2, ep=4, em=8)
    E1: int = 1
    E2: int = 2
    EP: int = 4  # ep = e3,  ep² = +1 (internal embedding)
    EM: int = 8  # em = e4,  em² = -1 (internal embedding)
    E12: int = 3

    # ══════════════════════════════════════════════════════════════
    # J‑map / Hodge star — complement dual for the 3D PGA subspace
    # ══════════════════════════════════════════════════════════════
    #
    # The 3D pseudoscalar I₃ = e₀∧e₁∧e₂ is null (I₃² = 0), so the
    # metric dual A·I⁻¹ does not exist.  Instead we use a complement
    # map satisfying  e_A ∧ J(e_A) = +I₃ .
    #
    # In the 4D embedding e₀ = ep + em, each 3D blade containing e₀
    # splits into two 4D blades (one with ep, one with em).
    #
    #   J(1)     = e₀₁₂       J(e₀₁₂)  = 1
    #   J(e₀)    = e₁₂         J(e₁₂)   = e₀
    #   J(e₁)    = -e₀₂        J(e₀₂)   = e₁
    #   J(e₂)    = e₀₁         J(e₀₁)   = -e₂

    _DUAL_MAP: dict[int, dict[int, float]] = {
        # Grade 0 (scalar)
        0: {7: 1.0, 11: 1.0},  # J(1) = I₃ = ep∧e₁₂ + em∧e₁₂
        # Grade 1 — pure Euclidean lines
        1: {6: -1.0, 10: -1.0},  # J(e₁) = -e₀₂
        2: {5: 1.0, 9: 1.0},  # J(e₂) = e₀₁
        # Grade 1 — e₀ halves (ep, em)
        4: {3: -0.5},  # J(ep) = J(e₀)/2 = -e₁₂/2
        8: {3: -0.5},  # J(em) = J(e₀)/2 = -e₁₂/2
        # Grade 2 — pure Euclidean bivector
        3: {4: -1.0, 8: -1.0},  # J(e₁₂) = -e₀  (PGA4CS convention)
        # Grade 2 — vanishing line halves
        5: {2: 0.5},  # J(ep∧e₁) = e₂/2
        9: {2: 0.5},  # J(em∧e₁) = e₂/2
        6: {1: -0.5},  # J(ep∧e₂) = -e₁/2
        10: {1: -0.5},  # J(em∧e₂) = -e₁/2
        # Grade 3 — pseudoscalar halves
        7: {0: 0.5},  # J(ep∧e₁₂) = 1/2
        11: {0: 0.5},  # J(em∧e₁₂) = 1/2
    }

    def __init__(self, dtype: str = "float64", opns: bool = True, **kw) -> None:
        super().__init__(4, 0b1000, dtype, opns=opns, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.ep = mv({self.EP: 1})  # internal — e3
        self.em = mv({self.EM: 1})  # internal — e4
        # e0 = ep + em — the Gunn/Dorst null vector
        self.e0 = mv({self.EP: 1.0, self.EM: 1.0})
        # e0_recip = 0.5·ep − 0.5·em  →  ⟨e0·e0_recip⟩₀ = 1
        self.e0_recip = mv({self.EP: 0.5, self.EM: -0.5})

    # ── PGA‑specific dual ─────────────────────────────────────────

    def dual(self, a: MV) -> MV:
        """3D PGA complement dual (J‑map / Hodge star).

        Overrides ``Algebra.dual()`` which computes ``★A = A·I⁻¹`` using
        the 4D pseudoscalar.  In PGA the 3D pseudoscalar ``I₃ = e₀∧e₁∧e₂``
        is null (``I₃² = 0``), so the metric dual does not exist.  Instead
        we use a combinatorial complement map.

        The 4D embedding ``e₀ = ep + em`` is handled by splitting each
        3D blade into halves.
        """
        result: dict[int, float] = {}
        for blade_id, coeff in a._impl.to_dict().items():
            dm = self._DUAL_MAP.get(blade_id)
            if dm is None:
                continue
            for dual_id, factor in dm.items():
                result[dual_id] = result.get(dual_id, 0.0) + coeff * factor
        return self.multivector(result)

    def undual(self, a: MV) -> MV:
        """Inverse of the signed dual.  In PGA the J‑map is its own inverse,
        so ``undual == dual``.
        """
        return self.dual(a)

    # ── display ───────────────────────────────────────────────────

    @cached_property
    def _display_basis(self) -> list:
        """Explicit display basis — e₀ first, PGA4CS convention.

        Each entry is ``(name, blade, pinv, blade_id | None)``.
        """
        e0, e1, e2, e0i = self.e0, self.e1, self.e2, self.e0_recip

        def _entry(name, blade):
            pinv = self.blade_pseudo_inverse(blade)
            bid = None
            raw = {
                k: v
                for bn, v in blade.to_dict().items()
                for k in [0 if bn == "s" else self.blade_id(bn)]
            }
            nz = [(k, v) for k, v in raw.items() if abs(v) > 1e-10]
            if len(nz) == 1 and abs(nz[0][1] - 1.0) < 1e-10:
                bid = nz[0][0]
            return (name, blade, pinv, bid)

        return [
            # Grade 0
            ("s", self.multivector({0: 1.0}), None, 0),
            # Grade 1 — vectors
            _entry("e0", e0),
            _entry("e1", e1),
            _entry("e2", e2),
            # this is not in PGA2 and should not occur
            _entry("ei", e0i),
            # Grade 2 — bivectors
            _entry("e10", e1.op(e0)),
            _entry("e20", e2.op(e0)),
            _entry("e12", e1.op(e2)),
            # this is not in PGA2 and should not occur
            _entry("ei1", e0i.op(e1)),
            _entry("ei2", e0i.op(e2)),
            _entry("E", e0.op(e0i)),
            # Grade 3 — pseudoscalar
            _entry("I", e0.op(e1).op(e2)),
            # this is not in PGA2 and should not occur
            _entry("Ii", e0i.op(e1).op(e2)),
            _entry("I4", e0.op(e0i).op(e1).op(e2)),
        ]
