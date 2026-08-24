# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared PGA2 helper functions for creation and analysis modules.

PGA2 is modelled via the 4D null‑vector embedding (dim=4).
Blade IDs are sourced from ``BasisPGA2`` as the single source of truth.

The 3D PGA complement dual (J‑map / Hodge star) is defined in
``BasisPGA2.dual()`` — geometry modules should use
``mv.algebra.dual(mv)`` or simply ``mv.dual()``.
"""

from __future__ import annotations

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV
from pytanga.basis.pga2 import BasisPGA2

# Blade IDs for the 4D embedding (sourced from BasisPGA2)
E1 = BasisPGA2.E1
E2 = BasisPGA2.E2
EP = BasisPGA2.EP
EM = BasisPGA2.EM
E12 = BasisPGA2.E12


def _get_e0(alg: Algebra) -> MV:
    """Return the null vector e₀ (Gunn/Dorst PGA convention).

    In the 4D embedding, e₀ = ep + em.  Prefers ``alg.e0`` if available
    (BasisPGA2); falls back to manual construction from blade IDs (generic
    Algebra instances).
    """
    if hasattr(alg, "e0"):
        return alg.e0
    return alg.multivector({EP: 1.0, EM: 1.0})


def _get_e0_coeff(mv: MV) -> float:
    """Extract the e₀ coefficient from a grade‑1 IPNS vector.

    Uses the algebraic identity ⟨e₀ · e0_recip⟩₀ = 1, so::

        α = ⟨mv · e0_recip⟩₀

    On ``BasisPGA2`` instances this is exactly the coefficient of the
    e₀ component.  For other algebras the correct dual vector is
    constructed from blade IDs.

    Returns:
        The e₀ coefficient of the grade‑1 portion of *mv*.
    """
    alg = mv.algebra
    if hasattr(alg, "e0_recip"):
        e0_recip = alg.e0_recip
    else:
        e0_recip = alg.multivector({EP: 0.5, EM: -0.5})
    return float(mv.sp(e0_recip))
