# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared PGA2 helper functions for creation and analysis modules.

PGA2 is modelled via the 4D null‑vector embedding (dim=4).
Blade IDs are sourced from ``BasisPGA2`` as the single source of truth.
"""

from __future__ import annotations

from functools import cache

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


@cache
def _pga2_pinv(alg: Algebra) -> MV:
    """Pseudo‑inverse of the 3D PGA pseudoscalar I₃ = e₁∧e₂∧e₀."""
    I3 = alg.e1.op(alg.e2).op(_get_e0(alg))
    return I3.blade_pseudo_inverse()


def _pga2_dual(mv: MV) -> MV:
    """3D PGA dual using pseudo‑inverse of the PGA pseudoscalar.

    In PGA2 (2D Euclidean + 1D projective), the pseudoscalar is
    I₃ = e₁∧e₂∧e₀ (grade 3).  The dual maps:
      - grade-1 points (IPNS) → grade-2 bivectors (OPNS) and vice versa
      - grade-0 scalars → grade-3 trivectors (pseudoscalar) and vice versa
    """
    return mv.ip(_pga2_pinv(mv.algebra))


def _get_e0_coeff(mv: MV) -> float:
    """Extract the e₀ coefficient from a grade‑1 IPNS vector.

    Uses the algebraic identity ⟨e₀ · e0_inv⟩₀ = 1, so::

        α = ⟨mv · e0_inv⟩₀

    On ``BasisPGA2`` instances this is exactly the coefficient of the
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
