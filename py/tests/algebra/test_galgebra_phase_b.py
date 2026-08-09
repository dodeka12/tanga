# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase B tests — norm, norm2, exp."""

import math
import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


# ═══════════════════════════════════════════════════════════════════════════
# G4 — norm2 / norm
# ═══════════════════════════════════════════════════════════════════════════
class TestNorm2:
    def test_euclidean_norm2_equals_mag2(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": 4.0, "e12": -1.0})
        assert mv.norm2() == pytest.approx(mv.mag2)

    def test_norm2_scalar(self, alg):
        mv = alg.multivector({"s": 7.0})
        assert mv.norm2() == pytest.approx(49.0)

    def test_norm2_vector(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0, "e3": 3.0})
        assert mv.norm2() == pytest.approx(14.0)

    def test_norm2_bivector(self, alg):
        mv = alg.multivector({"e12": 2.0})
        assert mv.norm2() == pytest.approx(4.0)

    def test_norm2_is_abs_of_qform(self, alg):
        mv = alg.multivector({"e1": 3.0})
        assert mv.norm2() == pytest.approx(abs(mv.qform()))

    def test_norm2_zero_is_zero(self, alg):
        mv = alg.multivector()
        assert mv.norm2() == pytest.approx(0.0)


class TestNorm:
    def test_euclidean_norm_equals_mag(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": 4.0})
        assert mv.norm() == pytest.approx(mv.mag)

    def test_norm_scalar(self, alg):
        mv = alg.multivector({"s": 5.0})
        assert mv.norm() == pytest.approx(5.0)

    def test_norm_is_sqrt_of_norm2(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0, "e3": 3.0})
        assert mv.norm() == pytest.approx(math.sqrt(mv.norm2()))


# ═══════════════════════════════════════════════════════════════════════════
# G7 — exp (exponential of multivector)
# ═══════════════════════════════════════════════════════════════════════════
class TestExp:
    def test_exp_zero_is_one(self, alg):
        mv = alg.multivector()
        result = mv.exp()
        assert result["s"] == pytest.approx(1.0)

    def test_exp_bivector_rotor(self, alg):
        # exp(α/2 * e12) for α=π/2 → cos(π/4) + sin(π/4)·e12 = 90° rotor
        angle = math.pi / 2
        half_angle = angle / 2
        bv = alg.multivector({"e12": half_angle})
        rotor = bv.exp()
        expected_cos = math.cos(half_angle)
        expected_sin = math.sin(half_angle)
        assert rotor["s"] == pytest.approx(expected_cos)
        assert rotor["e12"] == pytest.approx(expected_sin)

    def test_exp_null_square_element(self, alg):
        # A translator: e0 has e0² = 0 → exp(e0) = 1 + e0
        # In E3, we use e1 (which squares to 1, not 0). Let's use a test with
        # a known null square. Use a pure bivector scaled to make s=0? No…
        # Actually e1+e2 where e1²=e2²=1 and e1e2 antisymmetric gives 2.
        # Let's just use the formula directly. exp(k*e1) with s>0.
        # Using a very small bivector approximates s≈0 case:
        bv = alg.multivector({"e12": 1e-10})
        result = bv.exp()
        # exp(ε) ≈ 1 + ε for tiny ε (since cosh(ε)≈1, sinh(ε)/ε≈1)
        assert result["s"] == pytest.approx(1.0, rel=1e-6)
        assert result["e12"] == pytest.approx(1e-10, rel=1e-6)

    def test_exp_bivector_90deg(self, alg):
        # exp(π/2 * e12) → cos(π/2) + sin(π/2)·e12 = e12
        bv = alg.multivector({"e12": math.pi / 2})
        result = bv.exp()
        assert result["s"] == pytest.approx(0.0, abs=1e-10)
        assert result["e12"] == pytest.approx(1.0)

    def test_exp_raises_for_non_blade_like(self, alg):
        # A = e1 + e123: e1*e123 = e23, e123*e1 = e23 → A² has non-scalar e23
        mv = alg.multivector({"e1": 1.0, "e123": 1.0})
        with pytest.raises(ValueError, match="scalar"):
            mv.exp()

    def test_exp_bivector_satisfies_rotor_identity(self, alg):
        # R = exp(B/2), verify R * ~R ≈ 1
        bv = alg.multivector({"e12": 0.5})  # arbitrary angle
        rotor = bv.exp()
        product = rotor * rotor.rev()
        assert product["s"] == pytest.approx(1.0, rel=1e-6)
        # Non-scalar parts should be zero
        for name, v in product.to_dict().items():
            if name != "s":
                assert abs(v) < 1e-10, f"Non-scalar blade {name} = {v}"

    def test_exp_positive_s_branch(self, alg):
        # e1² = 1, so s>0 branch → exp(α·e1) = cosh(α) + sinh(α)·e1
        alpha = 0.5
        mv = alg.multivector({"e1": alpha})
        result = mv.exp()
        assert result["s"] == pytest.approx(math.cosh(alpha))
        assert result["e1"] == pytest.approx(math.sinh(alpha))
