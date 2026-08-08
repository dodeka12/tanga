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

    # ══════════════════════════════════════════════════════════════
    # J‑map / Hodge star — complement dual for the 4D PGA subspace
    # ══════════════════════════════════════════════════════════════
    #
    # The 4D pseudoscalar I₄ = e₀∧e₁∧e₂∧e₃ is null (I₄² = 0), so the
    # metric dual A·I⁻¹ does not exist.  Instead we use a complement
    # map that sends each basis blade to its index‑complement,
    # satisfying  e_A ∧ J(e_A) = +I₄ .
    #
    # In the 5D embedding e₀ = ep + em, each 4D blade containing e₀
    # splits into two 5D blades (one with ep, one with em).  Each
    # contributes half of the dual result.
    #
    # The mapping follows Gunn's J‑map / Dorst's Hodge star
    # (PGA4CS §9.1, Table 4):
    #
    #   J(1)     = e₀₁₂₃      J(e₀₁₂₃) = 1
    #   J(e₀)    = e₁₂₃        J(e₁₂₃)  = -e₀
    #   J(e₁)    = -e₀₂₃       J(e₀₂₃)  = e₁
    #   J(e₂)    = e₀₁₃        J(e₀₁₃)  = -e₂
    #   J(e₃)    = -e₀₁₂       J(e₀₁₂)  = e₃
    #   J(e₀₁)   = e₂₃         J(e₂₃)   = e₀₁
    #   J(e₀₂)   = -e₁₃        J(e₁₃)   = -e₀₂
    #   J(e₀₃)   = e₁₂         J(e₁₂)   = e₀₃

    _DUAL_MAP: dict[int, dict[int, float]] = {
        # Grade 0 (scalar)
        0: {15: 1.0, 23: 1.0},  # J(1) = I₄ = ep∧e₁₂₃ + em∧e₁₂₃
        # Grade 1 — pure Euclidean planes
        1: {14: -1.0, 22: -1.0},  # J(e₁) = -e₀₂₃
        2: {13: 1.0, 21: 1.0},  # J(e₂) = e₀₁₃
        4: {11: -1.0, 19: -1.0},  # J(e₃) = -e₀₁₂
        # Grade 1 — e₀ halves (ep, em)
        8: {7: 0.5},  # J(ep) = e₁₂₃/2
        16: {7: 0.5},  # J(em) = e₁₂₃/2
        # Grade 2 — pure Euclidean bivectors
        3: {12: 1.0, 20: 1.0},  # J(e₁₂) = e₀₃
        5: {10: -1.0, 18: -1.0},  # J(e₁₃) = -e₀₂
        6: {9: 1.0, 17: 1.0},  # J(e₂₃) = e₀₁
        # Grade 2 — vanishing line halves
        9: {6: 0.5},  # J(e₁∧ep) = e₂₃/2
        17: {6: 0.5},  # J(e₁∧em)
        10: {5: -0.5},  # J(e₂∧ep) = -e₁₃/2
        18: {5: -0.5},  # J(e₂∧em)
        12: {3: 0.5},  # J(e₃∧ep) = e₁₂/2
        20: {3: 0.5},  # J(e₃∧em)
        # Grade 3 — pure Euclidean trivector
        7: {8: -1.0, 16: -1.0},  # J(e₁₂₃) = -e₀
        # Grade 3 — point halves
        11: {4: 0.5},  # J(e₁₂∧ep) = e₃/2
        19: {4: 0.5},  # J(e₁₂∧em)
        13: {2: -0.5},  # J(e₁₃∧ep) = -e₂/2
        21: {2: -0.5},  # J(e₁₃∧em)
        14: {1: 0.5},  # J(e₂₃∧ep) = e₁/2
        22: {1: 0.5},  # J(e₂₃∧em)
        # Grade 4 — pseudoscalar halves
        15: {0: 0.5},  # J(e₁₂₃∧ep) = 1/2
        23: {0: 0.5},  # J(e₁₂₃∧em)
    }

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

    # ── PGA‑specific dual ─────────────────────────────────────────

    def dual(self, a: MV) -> MV:
        """4D PGA complement dual (J‑map / Hodge star).

        Overrides ``Algebra.dual()`` which computes ``★A = A·I⁻¹`` using
        the 5D pseudoscalar.  In PGA the 4D pseudoscalar ``I₄ = e₀∧e₁∧e₂∧e₃``
        is null (``I₄² = 0``), so the metric dual does not exist.  Instead
        we use a combinatorial complement map that swaps each basis blade
        with its index‑complement, satisfying ``e_A ∧ J(e_A) = +I₄``.

        This is Gunn's J‑map / Dorst's Hodge star (§9.1, PGA4CS Table 4).

        The 5D embedding ``e₀ = ep + em`` is handled by splitting each
        4D blade into halves.
        """
        result: dict[int, float] = {}
        for blade_id, coeff in a._impl.to_dict().items():
            dm = self._DUAL_MAP.get(blade_id)
            if dm is None:
                continue
            for dual_id, factor in dm.items():
                result[dual_id] = result.get(dual_id, 0.0) + coeff * factor
        return self.multivector(result)

    # ── convenience constructors ──────────────────────────────────

    def point(self, x: float, y: float, z: float) -> MV:
        """Point in IPNS / dual form: ``x·e₁ + y·e₂ + z·e₃ + e₀``.

        The OPNS form (grade‑3 trivector) is obtained via ``.dual()``
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
        """Explicit display basis — PGA4CS Table 4 naming convention.

        Blades are named with e₀ first so that the dual map signs are
        uniform per block of four (Dorst & De Keninck, §9.1).

        Each entry is ``(name, blade, pinv, blade_id | None)``.
        """
        e0, e1, e2, e3, e0i = self.e0, self.e1, self.e2, self.e3, self.e0_inv

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
            _entry("e3", e3),
            # this is not in PGA3 and should not occur
            _entry("e0i", e0i),
            # Grade 2 — bivectors
            _entry("e01", e0.op(e1)),
            _entry("e02", e0.op(e2)),
            _entry("e03", e0.op(e3)),
            _entry("e23", e2.op(e3)),
            _entry("e31", e3.op(e1)),
            _entry("e12", e1.op(e2)),
            # this is not in PGA3 and should not occur
            _entry("ei1", e0i.op(e1)),
            _entry("ei2", e0i.op(e2)),
            _entry("ei3", e0i.op(e3)),
            _entry("E", e0.op(e0i)),
            # Grade 3 — trivectors  (PGA4CS Table 4 order)
            _entry("e032", e0.op(e3).op(e2)),
            _entry("e013", e0.op(e1).op(e3)),
            _entry("e021", e0.op(e2).op(e1)),
            _entry("e123", e1.op(e2).op(e3)),
            # this is not in PGA3 and should not occur
            _entry("ei32", e0i.op(e3).op(e2)),
            _entry("ei13", e0i.op(e1).op(e3)),
            _entry("ei21", e0i.op(e2).op(e1)),
            # Grade 4 — pseudoscalar
            _entry("I", e0.op(e1).op(e2).op(e3)),
            # this is not in PGA3 and should not occur
            _entry("Ii", e0i.op(e1).op(e2).op(e3)),
            _entry("I5", e0.op(e0i).op(e1).op(e2).op(e3)),
        ]
