# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared PGA3 helper functions for creation and analysis modules.

PGA3 is modelled via the 5D null‑vector embedding (dim=5).
Blade IDs are sourced from ``BasisPGA3`` as the single source of truth.
"""

from __future__ import annotations

from functools import cache

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


@cache
def _pga3_pinv(alg: Algebra) -> MV:
    """Pseudo‑inverse of the 4D PGA pseudoscalar I₄ = e₁∧e₂∧e₃∧e₀."""
    I4 = alg.e1.op(alg.e2).op(alg.e3).op(_get_e0(alg))
    return I4.blade_pseudo_inverse()


def _pga3_dual(mv: MV) -> MV:
    """4D PGA dual using pseudo‑inverse of the PGA pseudoscalar."""
    return mv.ip(_pga3_pinv(mv.algebra))


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
