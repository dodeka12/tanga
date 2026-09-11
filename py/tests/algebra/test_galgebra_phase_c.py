# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase C tests — extended grade_proj (list[int]) and project_to (int | list[int])."""

import pytest
import pytanga


@pytest.fixture(scope="module")
def alg():
    return pytanga.Algebra(dim=3, sig=0)


# ═══════════════════════════════════════════════════════════════════════════
# Extended grade_proj — list[int]
# ═══════════════════════════════════════════════════════════════════════════
class TestGradeProjList:
    def test_grade_int_still_works(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0})
        result = mv.grade(1)
        assert result["e1"] == pytest.approx(2.0)
        assert result["e2"] == pytest.approx(3.0)
        assert result["s"] == pytest.approx(0.0, abs=1e-14)

    def test_grade_list_multiple(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0, "e123": 5.0})
        result = mv.grade([0, 2])
        assert result["s"] == pytest.approx(1.0)
        assert result["e12"] == pytest.approx(4.0)
        assert result["e1"] == pytest.approx(0.0, abs=1e-14)

    def test_grade_list_empty(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0})
        result = mv.grade([])
        assert result.is_zero

    def test_algebra_grade_proj_list(self, alg):
        mv = alg.multivector({"e1": 3.0, "e2": 4.0, "e12": -1.0, "e123": 2.0})
        result = alg.grade_proj(mv, [1, 3])
        assert result["e1"] == pytest.approx(3.0)
        assert result["e2"] == pytest.approx(4.0)
        assert result["e123"] == pytest.approx(2.0)
        assert result["e12"] == pytest.approx(0.0, abs=1e-14)


# ═══════════════════════════════════════════════════════════════════════════
# project_onto — MV (restrict a to b's blades) and BladeMask (exact ids)
# ═══════════════════════════════════════════════════════════════════════════
class TestProjectOnto:
    def test_project_onto_mv(self, alg):
        a = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": 3.0})
        b = alg.multivector({"e1": 1.0, "e12": 4.0})
        result = a.project_onto(b)
        assert result["e1"] == pytest.approx(1.0)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)
        assert result["e12"] == pytest.approx(3.0)

    def test_project_onto_mv_direction(self, alg):
        # b has e12 which a lacks; proves we keep a's components, not b's.
        a = alg.multivector({"e1": 5.0, "e2": 7.0})
        b = alg.multivector({"e2": 1.0, "e12": 9.0})
        result = a.project_onto(b)
        assert result["e1"] == pytest.approx(0.0, abs=1e-14)
        assert result["e2"] == pytest.approx(7.0)
        assert result["e12"] == pytest.approx(0.0, abs=1e-14)

    def test_project_onto_blade_mask_exact(self, alg):
        a = alg.multivector({"s": 5.0, "e1": 1.0, "e2": 2.0, "e12": 3.0})
        result = a.project_onto(pytanga.BladeMask(alg, [1, 3]))  # e1, e12
        assert result["e1"] == pytest.approx(1.0)
        assert result["e12"] == pytest.approx(3.0)
        assert result["s"] == pytest.approx(0.0, abs=1e-14)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)

    def test_project_onto_invalid_type(self, alg):
        a = alg.multivector({"e1": 1.0})
        with pytest.raises(TypeError):
            a.project_onto(1)
