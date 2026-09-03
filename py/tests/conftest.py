# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared fixtures for solver tests."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask
from pytanga.geometry import RndMV


@pytest.fixture(scope="module")
def alg_float():
    return Algebra(3, 0, "float64")


@pytest.fixture(scope="module")
def alg_int():
    return Algebra(3, 0, "int64")


@pytest.fixture(scope="module")
def vec_A_float(alg_float):
    """Reproducible general MV in float64."""
    mask = BladeMask.full(alg_float)
    return RndMV(mask, [(-1.0, 1.0)] * len(mask))(np.random.default_rng(42))


@pytest.fixture(scope="module")
def vec_A_int(alg_int):
    """Reproducible general MV in int64 with coefficients in [-48, 48]."""
    mask = BladeMask.full(alg_int)
    return RndMV(mask, [(-48, 49)] * len(mask))(np.random.default_rng(42))


@pytest.fixture(scope="module")
def mask_A_float(alg_float, vec_A_float):
    return BladeMask(vec_A_float)
