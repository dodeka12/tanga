# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase D tests — undual, cp/acp, rc, gp_min, gp_max."""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


# ═══════════════════════════════════════════════════════════════════════════
# G8 — undual
# ═══════════════════════════════════════════════════════════════════════════
class TestUndual:
    def test_undual_is_inverse_of_dual_e3(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": 3.0})
        assert (mv.dual().undual() - mv).is_zero

    def test_undual_of_dual_equals_identity(self, alg):
        mv = alg.multivector({"e1": 1.0, "e3": -1.0, "e12": 2.0})
        roundtrip = mv.dual().undual()
        assert (roundtrip - mv).is_zero

    def test_undual_vector(self, alg):
        # undual(e1) = e1 * I = e1 * e123 = e23
        e1 = alg.multivector({"e1": 1.0})
        result = e1.undual()
        assert result["e23"] == pytest.approx(1.0)

    def test_undual_scalar(self, alg):
        s = alg.multivector({"s": 5.0})
        result = s.undual()
        assert result["e123"] == pytest.approx(5.0)


# ═══════════════════════════════════════════════════════════════════════════
# G9 — cp / acp (commutator & anti-commutator)
# ═══════════════════════════════════════════════════════════════════════════
class TestCommutator:
    def test_cp_vectors(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 1.0})
        result = e1.cp(e2)
        assert result["e12"] == pytest.approx(1.0)

    def test_cp_antisymmetric(self, alg):
        a = alg.multivector({"e1": 2.0, "e2": 3.0, "e12": -1.0})
        b = alg.multivector({"e1": 1.0, "e3": 4.0})
        assert (a.cp(b) + b.cp(a)).is_zero

    def test_acp_symmetric(self, alg):
        a = alg.multivector({"e1": 2.0, "e2": 3.0})
        b = alg.multivector({"e1": 1.0, "e3": 4.0})
        assert (a.acp(b) - b.acp(a)).is_zero

    def test_cp_plus_acp_equals_gp(self, alg):
        a = alg.multivector({"e1": 2.0, "e2": 3.0})
        b = alg.multivector({"e1": 1.0, "e12": -1.0})
        assert (a.cp(b) + a.acp(b) - a * b).is_zero


# ═══════════════════════════════════════════════════════════════════════════
# G10 — right contraction (rc)
# ═══════════════════════════════════════════════════════════════════════════
class TestRightContraction:
    def test_rc_vector_vector(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        e2 = alg.multivector({"e2": 3.0})
        result = e1.rc(e2)
        assert result["s"] == pytest.approx(0.0)

    def test_rc_bivector_vector(self, alg):
        e12 = alg.multivector({"e12": 1.0})
        e1 = alg.multivector({"e1": 2.0})
        result = e12.rc(e1)
        # rc(e12,e1) = ip(e1,e12) * (−1)^{2·(1−2)} = ip(e1,e12) = e2
        assert result["e2"] == pytest.approx(2.0)

    def test_rc_vector_bivector_vanishes(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e12 = alg.multivector({"e12": 1.0})
        result = e1.rc(e12)
        assert result.is_zero

    def test_rc_relation_to_ip(self, alg):
        e1 = alg.multivector({"e1": 1.0})
        e2 = alg.multivector({"e2": 2.0})
        rc_val = e1.rc(e2)
        ip_val = e2.ip(e1)
        assert (rc_val - ip_val).is_zero


# ═══════════════════════════════════════════════════════════════════════════
# G11 — gp_min (Hestenes inner product)
# ═══════════════════════════════════════════════════════════════════════════
class TestGpMin:
    def test_gp_min_vectors(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        e2 = alg.multivector({"e2": 3.0})
        result = e1.gp_min(e2)
        assert result["s"] == pytest.approx(0.0)

    def test_gp_min_same_vector(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        result = e1.gp_min(e1)
        assert result["s"] == pytest.approx(4.0)

    def test_gp_min_bivector_vector(self, alg):
        e12 = alg.multivector({"e12": 1.0})
        e1 = alg.multivector({"e1": 2.0})
        result = e12.gp_min(e1)
        assert result["e2"] == pytest.approx(-2.0)

    def test_gp_min_raises_on_multigrade(self, alg):
        a = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": 3.0})
        b = alg.multivector({"e1": 1.0})
        with pytest.raises(ValueError, match="pure blade"):
            a.gp_min(b)


# ═══════════════════════════════════════════════════════════════════════════
# G12 — gp_max (outermost grade product)
# ═══════════════════════════════════════════════════════════════════════════
class TestGpMax:
    def test_gp_max_vectors_equals_op(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        e2 = alg.multivector({"e2": 3.0})
        result = e1.gp_max(e2)
        assert (result - (e1 ^ e2)).is_zero
        assert result["e12"] == pytest.approx(6.0)

    def test_gp_max_bivector_vector(self, alg):
        e12 = alg.multivector({"e12": 1.0})
        e3 = alg.multivector({"e3": 2.0})
        result = e12.gp_max(e3)
        assert result["e123"] == pytest.approx(2.0)

    def test_gp_max_vector_bivector(self, alg):
        e1 = alg.multivector({"e1": 2.0})
        e23 = alg.multivector({"e23": 3.0})
        result = e1.gp_max(e23)
        assert result["e123"] == pytest.approx(6.0)

    def test_gp_max_raises_on_multigrade(self, alg):
        a = alg.multivector({"e1": 1.0, "e12": 3.0})
        b = alg.multivector({"e1": 1.0})
        with pytest.raises(ValueError, match="pure blade"):
            a.gp_max(b)