# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared fixtures for solver tests."""

import pytest
from pytanga import Algebra, BladeMask, random_mv


@pytest.fixture(scope="module")
def alg_float():
    return Algebra(3, 0, "float64")


@pytest.fixture(scope="module")
def alg_int():
    return Algebra(3, 0, "int64")


@pytest.fixture(scope="module")
def vec_A_float(alg_float):
    """Reproducible general MV in float64."""
    return random_mv(alg_float, rng=42)


@pytest.fixture(scope="module")
def vec_A_int(alg_int):
    """Reproducible general MV in int64 with coefficients in [-48, 48]."""
    return random_mv(alg_int, low=-48, high=49, rng=42)


@pytest.fixture(scope="module")
def mask_A_float(alg_float, vec_A_float):
    return BladeMask(vec_A_float)
