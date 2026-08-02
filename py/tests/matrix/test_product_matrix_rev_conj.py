# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for reverse/conjugate product matrix (from blade mask only)."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask, MVProductMatrix
from pytanga.algebra import EProduct
from pytanga.matrix.convert import to_matrix
from pytanga.matrix.product import product_matrix_conj, product_matrix_rev


class TestProductMatrixRevConj:
    def test_rev_shape_and_masks(self, alg_float):
        mask = BladeMask(alg_float, [0, 1, 2, 4])
        M = product_matrix_rev(mask)
        assert isinstance(M, MVProductMatrix)
        n = len(mask)
        assert M.data.shape == (1, n, n)
        assert M.a_mask == mask
        assert M.b_mask == mask
        assert M.c_mask == mask
        assert M.product == EProduct.GP
        assert M.left is True

    def test_rev_diagonal_e3(self, alg_float):
        mask = BladeMask.full(alg_float)
        M = product_matrix_rev(mask)
        M2d = M.data[0]
        assert np.allclose(M2d - np.diag(np.diag(M2d)), 0.0, atol=1e-12)
        for i, bid in enumerate(mask.ids):
            g = bin(bid).count("1")
            expected = -1 if (g % 4) in (2, 3) else 1
            assert M2d[i, i] == expected, (
                f"blade={alg_float.blade_name(bid)} grade={g}: expected {expected}, got {M2d[i, i]}"
            )

    def test_rev_subset_mask(self, alg_float):
        mask = BladeMask(alg_float, grades=[2])
        M = product_matrix_rev(mask)
        assert M.data.shape == (1, 3, 3)
        M2d = M.data[0]
        for i in range(3):
            assert M2d[i, i] == -1, f"bivector at pos {i} should have sign -1"

    def test_rev_scalar_only(self, alg_float):
        mask = BladeMask(alg_float, grades=[0])
        M = product_matrix_rev(mask)
        assert M.data.shape == (1, 1, 1)
        assert M.data[0, 0, 0] == 1

    def test_conj_shape_and_masks(self, alg_float):
        mask = BladeMask(alg_float, [0, 1, 2, 4])
        M = product_matrix_conj(mask)
        assert isinstance(M, MVProductMatrix)
        n = len(mask)
        assert M.data.shape == (1, n, n)
        assert M.a_mask == mask
        assert M.b_mask == mask
        assert M.c_mask == mask

    def test_conj_equals_rev_in_euclidean(self, alg_float):
        mask = BladeMask.full(alg_float)
        M_rev = product_matrix_rev(mask)
        M_conj = product_matrix_conj(mask)
        assert np.allclose(M_rev.data, M_conj.data)

    def test_conj_differs_from_rev_in_p3(self):
        alg_p3 = Algebra(4, 0b1000, "float64")
        mask = BladeMask.full(alg_p3)
        M_rev = product_matrix_rev(mask)
        M_conj = product_matrix_conj(mask)
        n = len(mask)
        diff_found = False
        for i in range(n):
            if M_rev.data[0, i, i] != M_conj.data[0, i, i]:
                diff_found = True
                break
        assert diff_found, (
            "Expected conj != rev for at least one blade in non-Euclidean P3"
        )

    def test_rev_applied_matches_algebra_rev(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -3.0, "e12": 1.0})
        mask = BladeMask(a)
        M = product_matrix_rev(mask)
        vec_a = to_matrix(a, mask=mask).data
        vec_rev_pred = M.data[0] @ vec_a
        a_rev = alg_float.rev(a)
        for i, bid in enumerate(mask.ids):
            expected = a_rev.to_dict().get(alg_float.blade_name(bid), 0.0)
            assert vec_rev_pred[i, 0] == pytest.approx(expected, abs=1e-12)

    def test_conj_applied_matches_algebra_conj(self, alg_float):
        a = alg_float({"e1": 2.0, "e2": -3.0, "e12": 1.0})
        mask = BladeMask(a)
        M = product_matrix_conj(mask)
        vec_a = to_matrix(a, mask=mask).data
        vec_conj_pred = M.data[0] @ vec_a
        a_conj = alg_float.conj(a)
        for i, bid in enumerate(mask.ids):
            expected = a_conj.to_dict().get(alg_float.blade_name(bid), 0.0)
            assert vec_conj_pred[i, 0] == pytest.approx(expected, abs=1e-12)

    def test_rev_involution(self, alg_float):
        mask = BladeMask.full(alg_float)
        M = product_matrix_rev(mask)
        M2d = M.data[0]
        id_approx = M2d @ M2d
        assert np.allclose(id_approx, np.eye(len(mask)), atol=1e-12)

    def test_conj_involution(self, alg_float):
        mask = BladeMask.full(alg_float)
        M = product_matrix_conj(mask)
        M2d = M.data[0]
        id_approx = M2d @ M2d
        assert np.allclose(id_approx, np.eye(len(mask)), atol=1e-12)

    def test_rev_integer_algebra(self, alg_int):
        mask = BladeMask(alg_int, grades=[0, 1, 2, 3])
        M = product_matrix_rev(mask)
        assert M.data.dtype == np.int64
        M2d = M.data[0]
        for i, bid in enumerate(mask.ids):
            g = bin(bid).count("1")
            expected = -1 if (g % 4) in (2, 3) else 1
            assert int(M2d[i, i]) == expected

    def test_conj_integer_algebra(self, alg_int):
        mask = BladeMask(alg_int, grades=[0, 1, 2, 3])
        M = product_matrix_conj(mask)
        assert M.data.dtype == np.int64
