# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for blade operations exposed from MV_Blade_Ops.h."""

import pytest
import numpy as np
import pytanga
from pytanga.basis import BasisE3


@pytest.fixture(scope="module")
def e3():
    """E3 basis — cached for the whole test module."""
    return BasisE3()


# ---------------------------------------------------------------------------
# InverseBlade tests
# ---------------------------------------------------------------------------
def test_blade_inverse_vector(e3):
    """InverseBlade of a vector e1 should give e1 itself."""
    e1 = e3.e1
    inv = e1.blade_inverse()

    chk = e1 * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "GP(e1, inv(e1)) scalar should be 1"


def test_blade_inverse_bivector(e3):
    """InverseBlade of a bivector e1^e2."""
    e1 = e3.e1
    e2 = e3.e2
    bivec = e1 ^ e2
    inv = bivec.blade_inverse()

    chk = bivec * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "Scalar part of biv * inv(biv) should be 1"


# ---------------------------------------------------------------------------
# PseudoInverseBlade tests
# ---------------------------------------------------------------------------
def test_blade_pseudo_inverse_vector(e3):
    """PseudoInverseBlade of e1 (same as inverse in Euclidean E3)."""
    e1 = e3.e1
    inv = e1.blade_pseudo_inverse()

    chk = e1 * inv
    assert abs(chk.scalar - 1.0) < 1e-8, "Scalar part of e1 * pseudoInv(e1) should be 1"


# ---------------------------------------------------------------------------
# Project tests
# ---------------------------------------------------------------------------
def test_project_vector_onto_bivector(e3):
    """Project e1+e2 onto bivector e1^e2 — should recover full vector."""
    e1 = e3.e1
    e2 = e3.e2
    n_blade = e1 ^ e2
    a = e1 + e2

    proj = a.project(n_blade)
    diff = proj - a
    assert diff.mag < 1e-8, "Project of e1+e2 onto e1^e2 should recover e1+e2"


# ---------------------------------------------------------------------------
# Reject tests
# ---------------------------------------------------------------------------
def test_reject_vector_from_bivector(e3):
    """Reject e1+e2+e3 from e1^e2 — should give e3."""
    e1 = e3.e1
    e2 = e3.e2
    e3v = e3.e3

    n_blade = e1 ^ e2
    a = e1 + e2 + e3v

    rej = a.reject(n_blade)
    diff = rej - e3v
    assert diff.mag < 1e-8, "Reject of e1+e2+e3 from e1^e2 should be e3"


def test_project_reject_reconstruction(e3):
    """Project + Reject should reconstruct the original multivector."""
    e1 = e3.e1
    e2 = e3.e2
    e3v = e3.e3
    a = e1 * 2 + e2 * 3 + e3v * 4
    n_blade = e3v

    proj = a.project(n_blade)
    rej = a.reject(n_blade)
    s = proj + rej
    diff = s - a
    assert diff.mag < 1e-8, "Proj + Rej should reconstruct A"


# ---------------------------------------------------------------------------
# FactorizeBlade tests
# ---------------------------------------------------------------------------
def test_factorize_blade(e3):
    """Factorize bivector e1^e2 into two orthogonal vectors."""
    e1 = e3.e1
    e2 = e3.e2
    bivec = e1 ^ e2

    factors = bivec.blade_factorize()
    assert len(factors) == 2, "Bivector should factor into 2 vectors"

    reconstructed = factors[0] ^ factors[1]
    # IP(reconstructed, reverse(original)) should equal mag(original)*mag(reconstructed)
    ip_val = (reconstructed.ip_rev(bivec, rev_self=False, rev_other=True)).scalar
    expected = bivec.mag * reconstructed.mag
    assert abs(ip_val - expected) < 1e-8, (
        "Factorized vectors should reconstruct original blade (up to scale)"
    )


# ---------------------------------------------------------------------------
# Join tests
# ---------------------------------------------------------------------------
def test_join_adjacent(e3):
    """Join of e1 and e2 should contain both vectors."""
    e1 = e3.e1
    e2 = e3.e2
    j = e1.blade_join(e2)

    rej1 = e1.reject(j)
    assert rej1.mag < 1e-8, "Rejection of e1 from Join(e1, e2) should be zero"

    rej2 = e2.reject(j)
    assert rej2.mag < 1e-8, "Rejection of e2 from Join(e1, e2) should be zero"


def test_join_disjoint(e3):
    """Join of e1 and e3 (disjoint) should contain both."""
    e1 = e3.e1
    e3v = e3.e3
    j = e1.blade_join(e3v)

    rej1 = e1.reject(j)
    assert rej1.mag < 1e-8, "Join(e1, e3) should contain e1"

    rej3 = e3v.reject(j)
    assert rej3.mag < 1e-8, "Join(e1, e3) should contain e3"


# ---------------------------------------------------------------------------
# FactorizeVersor tests
# NOTE: FactorizeVersor internally calls GetGradeProjection which relies on
# ForEachBladePair iteration. This works on dense multivector types
# (CMultivector) but does not correctly iterate over sparse types
# (CDynamicMultivector) when the target MV starts empty,
# because ForEachBladePair only visits blades already present in the target.
# These tests are marked as expected failures until either a dense MV type
# is available or the algorithm is adapted for sparse MVs.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    reason="FactorizeVersor requires dense MV type (CMultivector); "
           "CDynamicMultivector's ForEachBladePair does not iterate over "
           "blades absent from the target MV, causing GetGradeProjection "
           "to return an empty result on a fresh target."
)
def test_factorize_versor(e3):
    """Factorize versor e1 * e2 (geometric product of two vectors)."""
    e1 = e3.e1
    e2 = e3.e2
    versor = e1 * e2  # e1*e2 = e1^e2 since orthogonal

    scale, factors = versor.blade_factorize_versor()
    assert len(factors) >= 2, "Versor e1*e2 should produce at least 2 factors"

    # Reconstruct: factors are extracted right-to-left, so reconstruct in REVERSE order
    reconstructed = scale
    for f in reversed(factors):
        reconstructed = reconstructed * f

    diff = reconstructed - versor
    assert diff.mag < 1e-8, "Reconstructed versor should equal original V"


@pytest.mark.xfail(
    reason="Same sparse-MV / GetGradeProjection limitation as test_factorize_versor."
)
def test_factorize_versor_g5():
    """Factorize a random versor in G(5)."""
    alg = pytanga.Algebra(5, 0)
    rng = np.random.default_rng(42)

    # Start with scalar 1, then multiply by 4 random vectors (matching C++ test)
    versor = alg.multivector({0: 1.0})

    for _ in range(4):
        vec = alg()
        for bit in range(5):
            val = rng.uniform(-2.0, 2.0)
            if abs(val) > 1e-12:
                vec[1 << bit] = val
        versor = versor * vec

    scale, factors = versor.blade_factorize_versor()

    # Reconstruct in reverse order
    reconstructed = scale
    for f in reversed(factors):
        reconstructed = reconstructed * f

    diff = reconstructed - versor
    assert diff.mag < 1e-4, "G(5) random versor reconstruction should match original"