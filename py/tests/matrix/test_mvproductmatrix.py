# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for MVProductMatrix validation."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask, MVProductMatrix
from pytanga.algebra import EProduct


class TestMVProductMatrix:
    def test_validation_2d_raises(self, alg_float):
        a_mask = BladeMask(alg_float, [1, 2])
        b_mask = BladeMask.full(alg_float)
        c_mask = BladeMask.full(alg_float)
        with pytest.raises(ValueError):
            MVProductMatrix(
                data=np.zeros((2, 8)),
                a_mask=a_mask,
                b_mask=b_mask,
                c_mask=c_mask,
                product=EProduct.GP,
                left=True,
            )

    def test_validation_wrong_shape_raises(self, alg_float):
        a_mask = BladeMask(alg_float, [1, 2])
        b_mask = BladeMask.full(alg_float)
        c_mask = BladeMask.full(alg_float)
        with pytest.raises(ValueError):
            MVProductMatrix(
                data=np.zeros((3, 8, 7)),
                a_mask=a_mask,
                b_mask=b_mask,
                c_mask=c_mask,
                product=EProduct.GP,
                left=True,
            )

    def test_validation_cross_algebra_raises(self, alg_float):
        a_mask = BladeMask(alg_float, [1, 2])
        b_mask = BladeMask.full(alg_float)
        alg2 = Algebra(4, 0, "float64")
        c_mask2 = BladeMask.full(alg2)
        with pytest.raises(ValueError):
            MVProductMatrix(
                data=np.zeros((2, 8, 8)),
                a_mask=a_mask,
                b_mask=b_mask,
                c_mask=c_mask2,
                product=EProduct.GP,
                left=True,
            )
