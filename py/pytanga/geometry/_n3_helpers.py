# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared N3 helper functions for creation and analysis modules.

Provides algebraic extraction of null-vector components (e∞ and e₀)
without relying on raw blade IDs of the ep/em embedding.

Reference: Perwass, "Geometric Algebra with Applications in Engineering",
           Chapter "Conformal Space".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytanga.basis.n3 import BasisN3

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs from BasisN3 as the single source of truth.
E1 = BasisN3.E1
E2 = BasisN3.E2
E3 = BasisN3.E3
E12 = BasisN3.E12
E13 = BasisN3.E13
E23 = BasisN3.E23
E123 = BasisN3.E123


def get_einf(basis: Algebra) -> MV:
    """Return the point-at-infinity null vector e∞."""
    return basis.einf


def get_eo(basis: Algebra) -> MV:
    """Return the origin null vector e₀."""
    return basis.eo


def einf_coeff(mv: MV, eo: MV) -> float:
    """e∞ coefficient of *mv* = −mv·e₀ (since e∞·e₀ = −1)."""
    return -float(mv.sp(eo))


def eo_coeff(mv: MV, einf: MV) -> float:
    """e₀ coefficient of *mv* = −mv·e∞."""
    return -float(mv.sp(einf))


def eucl_part(mv: MV, einf: MV, eo: MV) -> tuple[float, float, float]:
    """Euclidean (e₁, e₂, e₃) coefficients of a grade-1 blade.

    Subtracts the null components to recover the pure Euclidean part:
        x = mv − einf_c·e∞ − eo_c·e₀
    """
    einf_c = einf_coeff(mv, eo)
    eo_c = eo_coeff(mv, einf)
    return (
        float(mv[E1]) - einf_c * float(einf[E1]) - eo_c * float(eo[E1]),
        float(mv[E2]) - einf_c * float(einf[E2]) - eo_c * float(eo[E2]),
        float(mv[E3]) - einf_c * float(einf[E3]) - eo_c * float(eo[E3]),
    )


def translator_coeffs(mv: MV, basis: Algebra) -> tuple[float, float, float]:
    """Extract (dx, dy, dz) from a translator versor via algebraic extraction.

    For T = 1 − ½·t·e∞, the translation vector is:
        tᵢ = −2 · mv·(eᵢ∧e₀) / mv[0]

    Uses the algebraic identity (eᵢ∧e∞)·(eᵢ∧e₀) = 1, giving
    mv·(eᵢ∧e₀) = −½·tᵢ, so tᵢ = −2 · mv·(eᵢ∧e₀) / mv[0].

    Replaces the fragile:  dx = −2.0 * float(mv[9]) / scal
    """
    eo = get_eo(basis)
    scal = float(mv[0])
    if abs(scal) < 1e-15:
        raise ValueError("Translator has zero scalar component")

    e1_e0 = basis.e1.op(eo)  # e₁∧e₀
    e2_e0 = basis.e2.op(eo)  # e₂∧e₀
    e3_e0 = basis.e3.op(eo)  # e₃∧e₀

    return (
        -2.0 * float(mv.sp(e1_e0)) / scal,
        -2.0 * float(mv.sp(e2_e0)) / scal,
        -2.0 * float(mv.sp(e3_e0)) / scal,
    )


def has_translator_components(mv: MV, basis: Algebra) -> bool:
    """Check if *mv* has eᵢ∧e∞ bivector components."""
    try:
        tx, ty, tz = translator_coeffs(mv, basis)
    except ValueError:
        return False
    return abs(tx) + abs(ty) + abs(tz) > 1e-15


def has_E_component(mv: MV, basis: Algebra) -> bool:
    """Check if *mv* has an e∞∧e₀ component (E = e∞∧e₀).

    Since E² = (e∞∧e₀)·(e∞∧e₀) = 1, the E coefficient in mv
    is given directly by mv·E.
    """
    einf = get_einf(basis)
    eo = get_eo(basis)
    E = einf.op(eo)  # e∞∧e₀
    coeff = float(mv.sp(E))
    return abs(coeff) > 1e-15


def E_coefficient(mv: MV, basis: Algebra) -> float:
    """Extract the e∞∧e₀ bivector coefficient from *mv*.

    E² = (e∞∧e₀)·(e∞∧e₀) = 1, so the E coefficient in mv
    is given directly by mv·E.
    """
    einf = get_einf(basis)
    eo = get_eo(basis)
    E = einf.op(eo)
    return float(mv.sp(E))


def bivec_has_null(factor: MV, einf: MV, eo: MV) -> bool:
    """True if a bivector factor has e∞ or e₀ component."""
    return abs(einf_coeff(factor, eo)) > 1e-15 or abs(eo_coeff(factor, einf)) > 1e-15
