# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for EInv — involution enum in product_matrix()."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask
from pytanga.algebra import EInv
from pytanga.blade_mask.predict import product_blade_mask
from pytanga.matrix.convert import to_matrix
from pytanga.matrix.product import product_matrix


class TestProductMatrixEInv:
    def test_default_is_identity(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -1.0})
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M_def = product_matrix(a, b_mask=b_mask, c_mask=c_mask)
        M_id = product_matrix(
            a,
            b_mask=b_mask,
            c_mask=c_mask,
            left_inv=EInv.ID,
            right_inv=EInv.ID,
        )
        assert np.allclose(M_def.data, M_id.data)

    def test_left_rev_matches_gp_rev(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -3.0, "e12": 1.0})
        a_rev = alg_float.rev(a)
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M_revA = product_matrix(a, b_mask=b_mask, c_mask=c_mask, left_inv=EInv.REV)
        M_aRev = product_matrix(a_rev, b_mask=b_mask, c_mask=c_mask)
        assert np.allclose(M_revA.data, M_aRev.data)

    def test_right_rev_integrated(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -3.0, 0: 0.5})
        x = alg_float({"e1": 0.5, "e2": 1.0, "e12": -1.0})
        x_rev = alg_float.rev(x)
        b_mask = BladeMask(x)
        c_mask = product_blade_mask(BladeMask(a), b_mask, complete=True)
        M = product_matrix(a, b_mask=b_mask, c_mask=c_mask, right_inv=EInv.REV)
        vec_x = to_matrix(x, mask=b_mask).data
        pred = M.data[0] @ vec_x
        expected = a * x_rev
        expected.prune()
        for i, bid in enumerate(c_mask.ids):
            exp_val = expected.to_dict().get(alg_float.blade_name(bid), 0.0)
            assert pred[i, 0] == pytest.approx(exp_val, abs=1e-10)

    def test_left_conj_p3(self):
        alg = Algebra(4, 0b1000, "float64")
        a = alg({"e1": 1.0, "e2": 2.0, "e4": 3.0, "e12": 1.0})
        a_conj = alg.conj(a)
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M_conjA = product_matrix(a, b_mask=b_mask, c_mask=c_mask, left_inv=EInv.CONJ)
        M_aConj = product_matrix(a_conj, b_mask=b_mask, c_mask=c_mask)
        assert np.allclose(M_conjA.data, M_aConj.data)

    def test_both_rev(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -3.0, 0: 0.5})
        x = alg_float({"e1": 0.5, "e2": 1.0, "e12": -1.0})
        b_mask = BladeMask(x)
        c_mask = product_blade_mask(BladeMask(a), b_mask, complete=True)
        M = product_matrix(
            a,
            b_mask=b_mask,
            c_mask=c_mask,
            left_inv=EInv.REV,
            right_inv=EInv.REV,
        )
        vec_x = to_matrix(x, mask=b_mask).data
        pred = M.data[0] @ vec_x
        a_rev = alg_float.rev(a)
        x_rev = alg_float.rev(x)
        expected = a_rev * x_rev
        expected.prune()
        for i, bid in enumerate(c_mask.ids):
            exp_val = expected.to_dict().get(alg_float.blade_name(bid), 0.0)
            assert pred[i, 0] == pytest.approx(exp_val, abs=1e-10)

    def test_left_inv_preserved_in_mvproductmatrix(self, alg_float):
        a = alg_float("e1 + e2")
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M = product_matrix(a, b_mask=b_mask, c_mask=c_mask, left_inv=EInv.REV)
        assert M.left_inv == EInv.REV
        assert M.right_inv == EInv.ID

    def test_integer_left_rev(self, alg_int):
        a = alg_int({"e1": 3, "e2": 5, 0: 1})
        a_rev = alg_int.rev(a)
        b_mask = BladeMask(a)
        c_mask = product_blade_mask(b_mask, b_mask, complete=True)
        M_revA = product_matrix(a, b_mask=b_mask, c_mask=c_mask, left_inv=EInv.REV)
        M_aRev = product_matrix(a_rev, b_mask=b_mask, c_mask=c_mask)
        assert np.allclose(M_revA.data, M_aRev.data)
