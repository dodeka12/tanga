# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase A tests — grade_involution, grade_conj, scalar_product, qform, even/odd."""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


# ═══════════════════════════════════════════════════════════════════════════
# G1 — grade_involution
# ═══════════════════════════════════════════════════════════════════════════
class TestGradeInvolution:
    def test_scalar_unchanged(self, alg):
        mv = alg.multivector({"s": 5.0})
        result = mv.grade_involution()
        assert result["s"] == pytest.approx(5.0)

    def test_vector_negated(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": -2.0})
        result = mv.grade_involution()
        assert result["e1"] == pytest.approx(-3.0)
        assert result["e2"] == pytest.approx(2.0)

    def test_bivector_unchanged(self, alg):
        mv = alg.multivector({"e12": 4.0})
        result = mv.grade_involution()
        assert result["e12"] == pytest.approx(4.0)

    def test_trivector_negated(self, alg):
        mv = alg.multivector({"e123": 2.0})
        result = mv.grade_involution()
        assert result["e123"] == pytest.approx(-2.0)

    def test_ginvol_squared_is_identity(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e12": 3.0, "e123": 4.0})
        result = mv.grade_involution().grade_involution()
        assert (result - mv).is_zero

    def test_ginvol_is_linear(self, alg):
        a = alg.multivector({"e1": 1.0, "e2": 2.0})
        b = alg.multivector({"e12": 3.0})
        g_inv_sum = (a + b).grade_involution()
        g_inv_a = a.grade_involution()
        g_inv_b = b.grade_involution()
        assert (g_inv_sum - (g_inv_a + g_inv_b)).is_zero


# ═══════════════════════════════════════════════════════════════════════════
# G2 — grade_conj (grade‑based Clifford conjugate)
# ═══════════════════════════════════════════════════════════════════════════
class TestGradeConj:
    def test_scalar_unchanged(self, alg):
        mv = alg.multivector({"s": 5.0})
        result = mv.grade_conj()
        assert result["s"] == pytest.approx(5.0)

    def test_vector(self, alg):
        # For grade 1: (−1)^(1·2/2) = (−1)^1 = −1, and rev(k=1) = +1 → net −1
        mv = alg.multivector({"e1": 3.0})
        result = mv.grade_conj()
        assert result["e1"] == pytest.approx(-3.0)

    def test_bivector(self, alg):
        # grade_conj = ginvol.rev. For k=2: ginvol(−)=+, rev(−)=− → net −1
        mv = alg.multivector({"e12": 4.0})
        result = mv.grade_conj()
        assert result["e12"] == pytest.approx(-4.0)

    def test_trivector(self, alg):
        # k=3: ginvol(−)=−, rev(−)=− → net +1
        mv = alg.multivector({"e123": 2.0})
        result = mv.grade_conj()
        assert result["e123"] == pytest.approx(2.0)

    def test_grade_conj_equals_ginvol_rev(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e12": 3.0, "e123": 4.0})
        assert (mv.grade_conj() - mv.grade_involution().rev()).is_zero

    def test_grade_conj_distinct_from_conj(self, alg):
        """grade_conj is metric-independent; conj includes metric sign."""
        mv = alg.multivector({"e1": 1.0, "e12": 2.0})
        # In E3 (all positive metric), conj = rev only (no metric sign)
        # grade_conj has additional grade-based sign
        assert (mv.grade_conj() - mv.conj()).is_zero is False


# ═══════════════════════════════════════════════════════════════════════════
# G3 — scalar_product
# ═══════════════════════════════════════════════════════════════════════════
class TestScalarProduct:
    def test_default_same_as_sp(self, alg):
        a = alg.multivector({"s": 1.0, "e1": 2.0, "e12": 3.0})
        b = alg.multivector({"s": 4.0, "e2": 5.0})
        assert a.scalar_product(b) == pytest.approx(a.sp(b))

    def test_rev_scalar_product(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        e2 = alg.multivector({"e2": 3.0})
        assert e1.scalar_product(e2, rev=True) == pytest.approx(0.0)

    def test_rev_commutes_scalar_product(self, alg):
        a = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0})
        b = alg.multivector({"s": 4.0, "e1": 5.0, "e12": -1.0})
        assert a.scalar_product(b, rev=True) == pytest.approx(a.rev().sp(b))


# ═══════════════════════════════════════════════════════════════════════════
# G5 — qform
# ═══════════════════════════════════════════════════════════════════════════
class TestQForm:
    def test_euclidean_qform_equals_mag2(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": 4.0})
        assert mv.qform() == pytest.approx(mv.mag2)
        assert mv.qform() == pytest.approx(25.0)

    def test_qform_scalar(self, alg):
        mv = alg.multivector({"s": 7.0})
        assert mv.qform() == pytest.approx(49.0)

    def test_qform_bivector(self, alg):
        mv = alg.multivector({"e12": 2.0})
        assert mv.qform() == pytest.approx(4.0)

    def test_qform_equals_rev_sp(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": -1.0})
        assert mv.qform() == pytest.approx(mv.rev().sp(mv))


# ═══════════════════════════════════════════════════════════════════════════
# G6 — even / odd
# ═══════════════════════════════════════════════════════════════════════════
class TestEvenOdd:
    def test_even_extracts_scalar_and_bivector(self, alg):
        mv = alg.multivector(
            {"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0, "e123": 5.0}
        )
        e = mv.even()
        assert e["s"] == pytest.approx(1.0)
        assert e["e12"] == pytest.approx(4.0)
        assert e["e1"] == pytest.approx(0.0, abs=1e-14)
        assert e["e2"] == pytest.approx(0.0, abs=1e-14)

    def test_odd_extracts_vector_and_trivector(self, alg):
        mv = alg.multivector(
            {"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0, "e123": 5.0}
        )
        o = mv.odd()
        assert o["e1"] == pytest.approx(2.0)
        assert o["e2"] == pytest.approx(3.0)
        assert o["e123"] == pytest.approx(5.0)
        assert o["s"] == pytest.approx(0.0, abs=1e-14)
        assert o["e12"] == pytest.approx(0.0, abs=1e-14)

    def test_even_plus_odd_equals_original(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e12": 3.0, "e123": 4.0})
        assert (mv.even() + mv.odd() - mv).is_zero

    def test_even_equals_grade_proj_sum(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0})
        expected = mv.grade(0) + mv.grade(2)
        assert (mv.even() - expected).is_zero

    def test_odd_equals_grade_proj_sum(self, alg):
        mv = alg.multivector({"e1": 2.0, "e2": 3.0, "e123": 4.0})
        expected = mv.grade(1) + mv.grade(3)
        assert (mv.odd() - expected).is_zero
