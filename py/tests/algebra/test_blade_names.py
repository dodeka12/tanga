# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for pytanga._blade_names — pure Python, no C++ compilation needed."""

import pytest
from pytanga.algebra._blade_names import (
    all_blades,
    blade_id,
    blade_id_signed,
    blade_name,
    grade,
)


# ---------------------------------------------------------------------------
# grade
# ---------------------------------------------------------------------------
class TestGrade:
    def test_scalar(self):
        assert grade(0) == 0

    def test_vector(self):
        assert grade(0b001) == 1
        assert grade(0b010) == 1
        assert grade(0b100) == 1

    def test_bivector(self):
        assert grade(0b011) == 2
        assert grade(0b101) == 2
        assert grade(0b110) == 2

    def test_pseudoscalar_3d(self):
        assert grade(0b111) == 3


# ---------------------------------------------------------------------------
# blade_name
# ---------------------------------------------------------------------------
class TestBladeName:
    def test_scalar(self):
        assert blade_name(0, 3) == "s"

    def test_pseudoscalar(self):
        assert blade_name(7, 3) == "I"

    def test_vectors(self):
        assert blade_name(1, 3) == "e1"
        assert blade_name(2, 3) == "e2"
        assert blade_name(4, 3) == "e3"

    def test_bivectors(self):
        assert blade_name(3, 3) == "e12"
        assert blade_name(5, 3) == "e13"
        assert blade_name(6, 3) == "e23"

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            blade_name(8, 3)  # 8 >= 2^3


# ---------------------------------------------------------------------------
# blade_id
# ---------------------------------------------------------------------------
class TestBladeId:
    def test_scalar(self):
        assert blade_id("s", 3) == 0
        assert blade_id("0", 3) == 0

    def test_pseudoscalar(self):
        assert blade_id("I", 3) == 7

    def test_vectors(self):
        assert blade_id("e1", 3) == 1
        assert blade_id("e2", 3) == 2
        assert blade_id("e3", 3) == 4

    def test_bivectors(self):
        assert blade_id("e12", 3) == 3
        assert blade_id("e13", 3) == 5
        assert blade_id("e23", 3) == 6

    def test_order_independent(self):
        # e21 should give the same bitmask as e12
        assert blade_id("e21", 3) == blade_id("e12", 3)

    def test_index_out_of_range(self):
        with pytest.raises(ValueError):
            blade_id("e4", 3)  # dim=3, max index is 3

    def test_repeated_index(self):
        with pytest.raises(ValueError):
            blade_id("e11", 3)

    def test_roundtrip(self):
        for dim in (3, 4, 5):
            for b in range(1 << dim):
                name = blade_name(b, dim)
                assert blade_id(name, dim) == b


# ---------------------------------------------------------------------------
# blade_id_signed
# ---------------------------------------------------------------------------
class TestBladeIdSigned:
    def test_scalar(self):
        assert blade_id_signed("s", 3) == (0, 1)
        assert blade_id_signed("0", 3) == (0, 1)

    def test_pseudoscalar(self):
        assert blade_id_signed("I", 3) == (7, 1)

    def test_canonical_order_is_positive(self):
        assert blade_id_signed("e12", 3) == (3, 1)
        assert blade_id_signed("e13", 3) == (5, 1)
        assert blade_id_signed("e23", 3) == (6, 1)

    def test_reversed_bivector_is_negative(self):
        assert blade_id_signed("e21", 3) == (3, -1)
        assert blade_id_signed("e31", 3) == (5, -1)
        assert blade_id_signed("e32", 3) == (6, -1)

    def test_reversed_trivector_is_negative(self):
        assert blade_id_signed("e123", 3) == (7, 1)
        assert blade_id_signed("e321", 3) == (7, -1)

    def test_two_transpositions_are_positive(self):
        # e312 → indices [3, 1, 2]; two inversions → even → +1
        assert blade_id_signed("e312", 3) == (7, 1)

    def test_matches_blade_id_bitmask(self):
        for name in ("e12", "e21", "e13", "e31", "e123", "e321"):
            bitmask, _sign = blade_id_signed(name, 3)
            assert bitmask == blade_id(name, 3)

    def test_roundtrip_is_positive(self):
        for dim in (3, 4, 5):
            for b in range(1 << dim):
                name = blade_name(b, dim)
                assert blade_id_signed(name, dim) == (b, 1)


# ---------------------------------------------------------------------------
# all_blades
# ---------------------------------------------------------------------------
class TestAllBlades:
    def test_count(self):
        assert len(all_blades(3)) == 8
        assert len(all_blades(4)) == 16

    def test_sorted_by_grade(self):
        blades = all_blades(3)
        grades = [grade(b) for b in blades]
        assert grades == sorted(grades)

    def test_contains_all(self):
        assert set(all_blades(3)) == set(range(8))
