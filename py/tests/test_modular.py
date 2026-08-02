# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
Tests for G(3,0) with dtype='int64' and CCongruence_HMod.
Mirrors the pattern in source/Tan.App.Test/Test_Crypt_03.cpp.
"""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0, dtype="int64")


MODULUS = 101   # a small prime


class TestIntegerAlgebra:
    def test_algebra_dim(self, alg):
        assert alg.algebra_dim == 8

    def test_gp_integer_coefficients(self, alg):
        e1 = alg.multivector({"e1": 3})
        e2 = alg.multivector({"e2": 5})
        result = e1 * e2
        # 3*e1 * 5*e2 = 15*e12; no modulus applied to gp itself
        assert result["e12"] == 15

    def test_inv_requires_modulus(self, alg):
        e1 = alg.multivector({"e1": 1})
        with pytest.raises((ValueError, TypeError)):
            alg.inv(e1)   # must fail: no modulus provided

    def test_inv_modular(self, alg):
        """a * inv(a, p) should give scalar congruent to 1 (mod p)."""
        a = alg.multivector({"e1": 3, "e2": 7})
        inv_a = alg.inv(a, MODULUS)
        result = a * inv_a
        # Scalar coefficient should be 1 mod MODULUS
        scalar = result["s"] % MODULUS
        assert scalar == 1

    def test_not_invertible_raises(self, alg):
        zero_mv = alg.multivector()   # zero multivector
        with pytest.raises(RuntimeError):
            alg.inv(zero_mv, MODULUS)
