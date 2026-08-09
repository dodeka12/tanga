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
# Extended project_to — int (blade mask) and list[int] (blade IDs)
# ═══════════════════════════════════════════════════════════════════════════
class TestProjectToExtended:
    def test_project_to_mv_unchanged(self, alg):
        a = alg.multivector({"e1": 1.0, "e2": 2.0, "e12": 3.0})
        b = alg.multivector({"e1": 1.0})
        result = a.project_to(b)
        assert result["e1"] == pytest.approx(1.0)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)
        assert result["e12"] == pytest.approx(0.0, abs=1e-14)

    def test_project_to_int_blade_mask_subset(self, alg):
        # e1 = blade_id 1 (0b001), e2 = blade_id 2 (0b010), e12 = blade_id 3 (0b011)
        # mask 1 (0b001) — retains only blades that are subsets of {e1}: i.e. s(0), e1(1)
        mv = alg.multivector({"s": 5.0, "e1": 2.0, "e2": 3.0, "e12": 4.0})
        result = mv.project_to(1)  # mask = e1
        assert result["s"] == pytest.approx(5.0)  # s is subset of anything
        assert result["e1"] == pytest.approx(2.0)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)
        assert result["e12"] == pytest.approx(0.0, abs=1e-14)

    def test_project_to_int_mask_bivector(self, alg):
        # mask 3 (0b011 = e12) — retains s, e1, e2, e12 (subsets of {e1,e2})
        mv = alg.multivector({"s": 5.0, "e1": 2.0, "e2": 3.0, "e3": 4.0, "e12": 6.0, "e13": 7.0})
        result = mv.project_to(3)  # mask = e12
        assert result["s"] == pytest.approx(5.0)
        assert result["e1"] == pytest.approx(2.0)
        assert result["e2"] == pytest.approx(3.0)
        assert result["e12"] == pytest.approx(6.0)
        assert result["e3"] == pytest.approx(0.0, abs=1e-14)  # e3 = blade 4 not subset of 3
        assert result["e13"] == pytest.approx(0.0, abs=1e-14)  # e13 = blade 5 not subset of 3

    def test_project_to_list_ids(self, alg):
        mv = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0, "e123": 5.0})
        result = mv.project_to([0, 1, 3])  # s, e1, e12
        assert result["s"] == pytest.approx(1.0)
        assert result["e1"] == pytest.approx(2.0)
        assert result["e12"] == pytest.approx(4.0)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)
        assert result["e123"] == pytest.approx(0.0, abs=1e-14)

    def test_project_to_list_missing_blade(self, alg):
        mv = alg.multivector({"e1": 1.0})
        result = mv.project_to([0, 2])  # keep scalar and e2 only
        assert result["e1"] == pytest.approx(0.0, abs=1e-14)
        assert result["e2"] == pytest.approx(0.0, abs=1e-14)

    def test_project_to_empty_list(self, alg):
        mv = alg.multivector({"e1": 1.0, "e2": 2.0})
        result = mv.project_to([])
        assert result.is_zero
