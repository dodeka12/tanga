# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared PGA3 helper functions for creation and analysis modules.

PGA3 is modelled via the 5D null‑vector embedding (dim=5).
Blade IDs are sourced from ``BasisPGA3`` as the single source of truth.

The 4D PGA complement dual (J‑map / Hodge star) is defined in
``BasisPGA3.dual()`` — geometry modules should use
``mv.algebra.dual(mv)`` or simply ``mv.dual()``.
"""

from __future__ import annotations

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV
from pytanga.basis.pga3 import BasisPGA3

# Blade IDs for the 5D embedding (sourced from BasisPGA3)
E1 = BasisPGA3.E1
E2 = BasisPGA3.E2
E3 = BasisPGA3.E3
EP = BasisPGA3.EP
EM = BasisPGA3.EM
E12 = BasisPGA3.E12
E13 = BasisPGA3.E13
E23 = BasisPGA3.E23
E123 = BasisPGA3.E123


def _get_e0(alg: Algebra) -> MV:
    """Return the null vector e₀ (Gunn/Dorst PGA convention).

    In the 5D embedding, e₀ = ep + em.  Prefers ``alg.e0`` if available
    (BasisPGA3); falls back to manual construction from blade IDs (generic
    Algebra instances).
    """
    if hasattr(alg, "e0"):
        return alg.e0
    return alg.multivector({EP: 1.0, EM: 1.0})


def _get_e0_coeff(mv: MV) -> float:
    """Extract the e₀ coefficient from a grade‑1 IPNS vector.

    Uses the algebraic identity ⟨e₀ · e0_inv⟩₀ = 1, so::

        α = ⟨mv · e0_inv⟩₀

    On ``BasisPGA3`` instances this is exactly the coefficient of the
    e₀ component.  For other algebras the correct dual vector is
    constructed from blade IDs.

    Returns:
        The e₀ coefficient of the grade‑1 portion of *mv*.
    """
    alg = mv.algebra
    if hasattr(alg, "e0_inv"):
        e0_inv = alg.e0_inv
    else:
        e0_inv = alg.multivector({EP: 0.5, EM: -0.5})
    return float(mv.sp(e0_inv))
