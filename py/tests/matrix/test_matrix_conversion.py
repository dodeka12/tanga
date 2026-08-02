# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for to_matrix / from_matrix round-trip."""

import numpy as np
import pytest
from pytanga import BladeMask, MVMatrix
from pytanga.matrix.convert import from_matrix, to_matrix


class TestMatrixConversion:
    def test_to_matrix_shape(self, alg_float, vec_A_float, mask_A_float):
        m = to_matrix(vec_A_float, mask=mask_A_float)
        assert isinstance(m, MVMatrix)
        assert m.data.shape == (len(mask_A_float), 1)
        assert m.row_mask.ids == mask_A_float.ids
        assert m.is_single
        assert m.n_cols == 1

    def test_to_matrix_list(self, alg_float):
        mvs = [alg_float("e1"), alg_float("e2"), alg_float("3 e3")]
        mask = BladeMask(alg_float, [1, 2, 4])
        mat = to_matrix(mvs, mask=mask)
        assert isinstance(mat, MVMatrix)
        assert mat.n_cols == 3
        assert mat.data.shape == (3, 3)
        assert mat.data[0, 0] == 1.0
        assert mat.data[1, 1] == 1.0
        assert mat.data[2, 2] == 3.0

    def test_round_trip(self, alg_float, vec_A_float, mask_A_float):
        mat = to_matrix(vec_A_float, mask=mask_A_float)
        recovered = from_matrix(mat)
        assert recovered.to_dict() == vec_A_float.to_dict()

    def test_from_matrix_multi_column(self, alg_float):
        mask = BladeMask(alg_float, [1, 2, 4])
        data = np.array([[1, 0], [0, 1], [0, 0]], dtype=np.float64)
        m = MVMatrix(data=data, row_mask=mask)
        assert m.n_cols == 2
        assert not m.is_single
        result = from_matrix(m)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].to_dict() == {"e1": 1.0}
        assert result[1].to_dict() == {"e2": 1.0}

    def test_to_matrix_scalar_input(self, alg_float):
        scalar_mask = BladeMask(alg_float, grades=[0])
        mat = to_matrix(1.0, mask=scalar_mask)
        assert mat.data[0, 0] == pytest.approx(1.0)

    def test_to_matrix_string_input(self, alg_float):
        mask = BladeMask(alg_float, "e1")
        mat = to_matrix("e1", mask=mask)
        assert mat.data[0, 0] == pytest.approx(1.0)
