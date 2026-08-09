# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase E tests — type checks and coefficient methods."""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


class TestIsVector:
    def test_is_vector_true(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0})
        assert mv.is_vector is True

    def test_is_vector_false_mixed(self, alg):
        mv = alg.multivector({"e1": 1.0, "e12": 2.0})
        assert mv.is_vector is False

    def test_is_vector_scalar_not_vector(self, alg):
        mv = alg.multivector({"s": 5.0})
        assert mv.is_vector is False


class TestIsBase:
    def test_is_base_true(self, alg):
        mv = alg.multivector({"e1": 1.0})
        assert mv.is_base is True

    def test_is_base_scalar(self, alg):
        mv = alg.multivector({"s": 1.0})
        assert mv.is_base is True

    def test_is_base_false_coefficient(self, alg):
        mv = alg.multivector({"e1": 2.0})
        assert mv.is_base is False

    def test_is_base_false_multiple_blades(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 1.0})
        assert mv.is_base is False


class TestIsBlade:
    def test_is_blade_scalar(self, alg):
        mv = alg.multivector({"s": 5.0})
        assert mv.is_blade is True

    def test_is_blade_vector(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": 4.0})
        assert mv.is_blade is True

    def test_is_blade_bivector(self, alg):
        # e12 is a blade (simple bivector)
        mv = alg.multivector({"e12": 1.0})
        assert mv.is_blade is True

    def test_is_blade_false_mixed_grade(self, alg):
        mv = alg.multivector({"e1": 1.0, "e12": 2.0})
        assert mv.is_blade is False


class TestComponents:
    def test_components(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e12": 3.0})
        comps = mv.components()
        assert len(comps) == 3
        has_scalar = any(c["s"] == pytest.approx(1.0) for c in comps)
        has_e1 = any(c["e1"] == pytest.approx(2.0) for c in comps)
        has_e12 = any(c["e12"] == pytest.approx(3.0) for c in comps)
        assert has_scalar and has_e1 and has_e12

    def test_components_zero(self, alg):
        mv = alg.multivector()
        assert mv.components() == []


class TestGetCoefs:
    def test_get_coefs_grade1(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0, "e3": 3.0})
        coefs = mv.get_coefs(1)
        assert coefs == pytest.approx([1.0, 2.0, 3.0])

    def test_get_coefs_grade0(self, alg):
        mv = alg.multivector({"s": 5.0})
        coefs = mv.get_coefs(0)
        assert coefs == pytest.approx([5.0])

    def test_get_coefs_missing_grade(self, alg):
        mv = alg.multivector({"e1": 1.0})
        coefs_g2 = mv.get_coefs(2)
        assert all(c == 0.0 for c in coefs_g2)


class TestBladeCoefs:
    def test_blade_coefs_all(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0})
        all_coefs = mv.blade_coefs()
        assert len(all_coefs) == 8  # 2^3
        assert all_coefs[0] == pytest.approx(1.0)

    def test_blade_coefs_with_list(self, alg):
        mv = alg.multivector({"e1": 2.0, "e2": 3.0, "e12": 4.0})
        blades = [
            alg.multivector({"e1": 1.0}),
            alg.multivector({"e12": 1.0}),
        ]
        coefs = mv.blade_coefs(blades)
        assert coefs[0] == pytest.approx(2.0)
        assert coefs[1] == pytest.approx(4.0)
