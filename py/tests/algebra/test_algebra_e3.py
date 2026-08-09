# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""
Integration tests for G(3,0,0) — the 3D Euclidean geometric algebra.
These tests compile the binding on first run (may take ~10 s).
"""

import math
import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


class TestConstants:
    def test_algebra_dim(self, alg):
        assert alg.algebra_dim == 8   # 2^3

    def test_pseudoscalar_id(self, alg):
        assert alg.pseudoscalar_id == 7   # 0b111


class TestBasisVectorSquares:
    """In G(3,0), every basis vector squares to +1."""

    @pytest.mark.parametrize("name", ["e1", "e2", "e3"])
    def test_vector_squares_to_positive_scalar(self, alg, name):
        e = alg.multivector({name: 1.0})
        sq = e * e
        assert abs(sq["s"] - 1.0) < 1e-9
        assert sq["e1"] == pytest.approx(0.0, abs=1e-9)

    def test_e1_e2_anticommute(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 * e2)["e12"] == pytest.approx( 1.0, abs=1e-9)
        assert (e2 * e1)["e12"] == pytest.approx(-1.0, abs=1e-9)


class TestOuterProduct:
    def test_e1_wedge_e2_gives_e12(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        result = e1 ^ e2
        assert result["e12"] == pytest.approx(1.0, abs=1e-9)

    def test_wedge_with_self_is_zero(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        result = e1 ^ e1
        assert result._impl.blade_count() == 0


class TestInverse:
    def test_inv_e12(self, alg):
        """In G(3,0), e12 * e12 = -1, so inv(e12) = -e12."""
        e12    = alg.multivector({"e12": 1.0})
        inv_e12 = ~e12
        assert inv_e12["e12"] == pytest.approx(-1.0, abs=1e-9)

    def test_mv_times_inv_is_scalar_one(self, alg):
        """a * inv(a) should give scalar 1 (up to precision)."""
        a = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": -1.0})
        result = a * a.inv()
        assert result["s"] == pytest.approx(1.0, abs=1e-9)
        # All non-scalar components should vanish
        for k, v in result._impl.to_dict().items():
            if k != 0:
                assert abs(v) < 1e-9, f"Non-scalar blade {k} = {v}"


class TestOperatorOverloads:
    def test_mul_operator(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 * e2)["e12"] == pytest.approx(1.0, abs=1e-9)

    def test_xor_operator(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        assert (e1 ^ e2)["e12"] == pytest.approx(1.0, abs=1e-9)


class TestRepr:
    def test_repr_nonzero(self, alg):
        mv = alg.multivector({"e1": 1.0})
        assert "e1" in repr(mv)

    def test_repr_zero(self, alg):
        mv = alg.multivector()
        assert repr(mv) == "0"


class TestMultivectorTupleKeys:
    """alg.multivector({(i, j, ...): coeff}) — 1-based index tuples."""

    def test_scalar_via_zero_tuple(self, alg):
        mv = alg.multivector({(0,): 5.0})
        assert mv["s"] == pytest.approx(5.0)

    def test_scalar_via_empty_tuple(self, alg):
        mv = alg.multivector({(): 3.0})
        assert mv["s"] == pytest.approx(3.0)

    def test_grade1_blade(self, alg):
        mv = alg.multivector({(2,): 1.0})
        assert mv["e2"] == pytest.approx(1.0)
        assert mv["e1"] == pytest.approx(0.0, abs=1e-9)

    def test_grade2_blade(self, alg):
        # (1, 2) → e1 ∧ e2 → bitmask 0b11 = 3 → "e12"
        mv = alg.multivector({(1, 2): -0.5})
        assert mv["e12"] == pytest.approx(-0.5)

    def test_grade3_blade(self, alg):
        # (1, 2, 3) → e123 → pseudoscalar in G(3)
        mv = alg.multivector({(1, 2, 3): 2.0})
        assert mv["I"] == pytest.approx(2.0)

    def test_mixed_grades(self, alg):
        mv = alg.multivector({(0,): 1.0, (1,): 2.0, (1, 2): 3.0})
        assert mv["s"]   == pytest.approx(1.0)
        assert mv["e1"]  == pytest.approx(2.0)
        assert mv["e12"] == pytest.approx(3.0)

    def test_invalid_index_zero_raises(self, alg):
        # 0 is only valid as a singleton (0,) meaning scalar
        with pytest.raises(ValueError, match="scalar"):
            alg.multivector({(0, 1): 1.0})

    def test_index_out_of_range_raises(self, alg):
        with pytest.raises(ValueError):
            alg.multivector({(4,): 1.0})   # dim=3, so e4 doesn't exist


class TestPrecision:
    """Phase 0 — ``precision`` property on Algebra controls is_zero / is_scalar / prune."""

    def test_default_precision(self, alg):
        assert alg.precision == 1e-10

    def test_custom_precision(self):
        a = pytanga.Algebra(dim=3, sig=0, precision=1e-8)
        assert a.precision == 1e-8

    def test_set_precision(self, alg):
        alg.precision = 1e-12
        assert alg.precision == 1e-12
        alg.precision = 1e-10  # restore default for other tests

    def test_is_zero_with_tiny_values(self, alg):
        mv = alg.multivector({"e1": 1e-13, "e2": 1e-13})
        # Default precision is 1e-10, so these tiny values should be treated as zero
        assert mv.is_zero is True

    def test_is_zero_above_precision(self, alg):
        mv = alg.multivector({"e1": 1e-9})
        assert mv.is_zero is False

    def test_is_scalar_with_tiny_non_scalar(self, alg):
        mv = alg.multivector({"s": 5.0, "e1": 1e-13})
        # Default precision is 1e-10; e1 is tiny, so it is scalar
        assert mv.is_scalar is True

    def test_is_scalar_with_non_scalar_above_precision(self, alg):
        mv = alg.multivector({"s": 5.0, "e1": 1e-9})
        assert mv.is_scalar is False

    def test_prune_removes_tiny_coefficients(self, alg):
        mv = alg.multivector({"s": 5.0, "e1": 1e-13, "e2": 1e-13})
        mv.prune()
        assert mv["s"] == pytest.approx(5.0)
        assert mv["e1"] == pytest.approx(0.0, abs=1e-15)
        assert mv["e2"] == pytest.approx(0.0, abs=1e-15)

    def test_prune_keeps_above_precision(self, alg):
        mv = alg.multivector({"s": 5.0, "e1": 1e-9})
        mv.prune()
        assert mv["s"] == pytest.approx(5.0)
        assert mv["e1"] == pytest.approx(1e-9)

    def test_custom_precision_prune(self):
        a = pytanga.Algebra(dim=3, sig=0, precision=1e-6)
        mv = a.multivector({"s": 5.0, "e1": 1e-7})
        mv.prune()
        assert mv["s"] == pytest.approx(5.0)
        # 1e-7 < 1e-6 precision, so e1 should be pruned
        assert mv["e1"] == pytest.approx(0.0, abs=1e-15)


class TestMultivectorStringInput:
    """alg.multivector("coeff e... + ...") — string expression."""

    def test_scalar_only(self, alg):
        mv = alg.multivector("7")
        assert mv["s"] == pytest.approx(7.0)

    def test_single_blade(self, alg):
        mv = alg.multivector("e1")
        assert mv["e1"] == pytest.approx(1.0)

    def test_blade_with_coefficient(self, alg):
        mv = alg.multivector("4 e2")
        assert mv["e2"] == pytest.approx(4.0)

    def test_negative_coefficient(self, alg):
        mv = alg.multivector("-3 e1")
        assert mv["e1"] == pytest.approx(-3.0)

    def test_bare_negative_blade(self, alg):
        mv = alg.multivector("-e2")
        assert mv["e2"] == pytest.approx(-1.0)

    def test_sum_of_terms(self, alg):
        mv = alg.multivector("2.3 + 4 e2 + 5 e1,2")
        assert mv["s"]   == pytest.approx(2.3)
        assert mv["e2"]  == pytest.approx(4.0)
        assert mv["e12"] == pytest.approx(5.0)

    def test_comma_separated_high_dim_blade(self, alg):
        # e1,2 = e12 in G(3)
        mv = alg.multivector("e1,2")
        assert mv["e12"] == pytest.approx(1.0)

    def test_negative_blade_no_coeff(self, alg):
        mv = alg.multivector("e1 - e2")
        assert mv["e1"] == pytest.approx( 1.0)
        assert mv["e2"] == pytest.approx(-1.0)

    def test_star_separator(self, alg):
        mv = alg.multivector("3*e1")
        assert mv["e1"] == pytest.approx(3.0)

    def test_scalar_plus_blade(self, alg):
        mv = alg.multivector("1 + e12")
        assert mv["s"]   == pytest.approx(1.0)
        assert mv["e12"] == pytest.approx(1.0)

    def test_compact_bivector_name(self, alg):
        # "e12" without comma — compact form valid for dim ≤ 9
        mv = alg.multivector("5 e12")
        assert mv["e12"] == pytest.approx(5.0)

    def test_full_multivector(self, alg):
        mv = alg.multivector("1 e1 + 2 e2 - 3 e3 + 4 e12")
        assert mv["e1"]  == pytest.approx( 1.0)
        assert mv["e2"]  == pytest.approx( 2.0)
        assert mv["e3"]  == pytest.approx(-3.0)
        assert mv["e12"] == pytest.approx( 4.0)
