# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Algebra.random_mv()."""

from __future__ import annotations

import numpy as np
import pytest
from pytanga import Algebra, BladeMask
from pytanga.algebra import random_mv


@pytest.fixture(scope="module")
def alg_float():
    return Algebra(3, 0, "float64")


@pytest.fixture(scope="module")
def alg_int():
    return Algebra(3, 0, "int64")


class TestRandomMV:
    def test_all_blades_float(self, alg_float):
        mv = random_mv(alg_float, rng=0)
        assert len(mv.to_dict()) == 8

    def test_mask_restriction(self, alg_float):
        mask = BladeMask(alg_float, grades=[1])
        mv = random_mv(alg_float, mask=mask, rng=0)
        for name in mv.to_dict():
            bid = alg_float.blade_id(name)
            assert bin(bid).count("1") == 1, f"non-grade-1 blade {name}"

    def test_range_float(self, alg_float):
        mv = random_mv(alg_float, low=5.0, high=6.0, rng=0)
        for v in mv.to_dict().values():
            assert 5.0 <= v < 6.0

    def test_reproducibility(self, alg_float):
        mv_a = random_mv(alg_float, rng=42)
        mv_b = random_mv(alg_float, rng=42)
        assert mv_a.to_dict() == mv_b.to_dict()

    def test_different_seeds_differ(self, alg_float):
        mv_a = random_mv(alg_float, rng=0)
        mv_b = random_mv(alg_float, rng=1)
        assert mv_a.to_dict() != mv_b.to_dict()

    def test_integer_dtype(self, alg_int):
        mv = random_mv(alg_int, low=-10, high=11, rng=0)
        for v in mv.to_dict().values():
            assert isinstance(v, int)
            assert -10 <= v <= 10

    def test_numpy_rng_accepted(self, alg_float):
        rng = np.random.default_rng(99)
        mv = random_mv(alg_float, rng=rng)
        assert mv is not None
