# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for product_matrix correctness (GP, IP, OP)."""

import pytest
from pytanga import BladeMask, MVProductMatrix
from pytanga.algebra import EProduct
from pytanga.blade_mask.predict import product_blade_mask
from pytanga.matrix.convert import to_matrix
from pytanga.matrix.product import product_matrix


class TestProductMatrix:
    def test_shape(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0})
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M = product_matrix(a, b_mask=b_mask, c_mask=c_mask)
        assert isinstance(M, MVProductMatrix)
        assert M.data.shape == (1, len(c_mask), len(b_mask))
        assert M.b_mask.ids == b_mask.ids
        assert M.c_mask.ids == c_mask.ids

    def test_consistency_with_gp(self, alg_float):
        a = alg_float({"e1": 1.0, "e2": -2.0, 0: 0.5})
        x = alg_float({"e1": 0.3, "e2": -0.7, 0: 1.0})
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M = product_matrix(a, b_mask=b_mask, c_mask=c_mask, product=EProduct.GP)
        vec_x = to_matrix(x, mask=b_mask)
        M2d = M.data[0]
        mat_result = M2d @ vec_x.data
        ax = a * x
        ax.prune()
        for i, bid in enumerate(c_mask.ids):
            name = alg_float.blade_name(bid)
            expected = ax.to_dict().get(name, 0.0)
            assert mat_result[i, 0] == pytest.approx(expected, abs=1e-10)

    def test_product_matrix_list_with_a_mask(self, alg_float):
        mvs = [alg_float("e1"), alg_float("e2"), alg_float("e3")]
        b_mask = BladeMask.full(alg_float)
        c_mask = BladeMask.full(alg_float)
        a_mask = BladeMask(alg_float, [1, 2, 4])
        M = product_matrix(
            mvs, a_mask=a_mask, b_mask=b_mask, c_mask=c_mask, product="gp"
        )
        assert isinstance(M, MVProductMatrix)
        assert M.a_mask == a_mask
        assert M.b_mask == b_mask
        assert M.c_mask == c_mask
        assert M.shape == (3, len(c_mask), len(b_mask))

    def test_product_matrix_list_auto_a_mask(self, alg_float):
        mvs = [alg_float("e1"), alg_float("e2"), alg_float("e12")]
        b_mask = BladeMask.full(alg_float)
        c_mask = BladeMask.full(alg_float)
        M = product_matrix(mvs, b_mask=b_mask, c_mask=c_mask, product="gp")
        assert isinstance(M, MVProductMatrix)
        assert set(M.a_mask.ids) == {1, 2, 3}
        assert M.n_mvs == 3

    def test_product_blade_mask_renamed(self, alg_float):
        a_mask = BladeMask(alg_float("e1"))
        b_mask = BladeMask(alg_float, [1, 2])
        c_mask = product_blade_mask(a_mask, b_mask, product=EProduct.GP)
        assert 0 in c_mask.ids
        assert 3 in c_mask.ids
