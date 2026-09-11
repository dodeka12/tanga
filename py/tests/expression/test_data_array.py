# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the DataArray data container."""

import numpy as np
import pytest

from pytanga import DataArray
from pytanga.basis import BasisE3
from pytanga.blade_mask import BladeMask


class TestDataArray:
    def setup_method(self):
        self.alg = BasisE3()
        self.vec_mask = BladeMask(self.alg, [self.alg.E1, self.alg.E2, self.alg.E3])

    def test_numpy_scalar_1d(self):
        d = DataArray(np.array([1.0, 2.0, 3.0]), masks=("n",))
        assert d.ndim == 1
        assert d.shape == (3,)
        assert d.masks == ("n",)

    def test_numpy_scalar_2d(self):
        d = DataArray(np.zeros((3, 4)), masks=("n", "m"))
        assert d.ndim == 2
        assert d.masks == ("n", "m")

    def test_numpy_point_data(self):
        d = DataArray(np.zeros((100, 3)), masks=("pnt_idx", self.vec_mask))
        assert d.ndim == 2
        assert d.masks == ("pnt_idx", self.vec_mask)

    def test_list_of_scalars(self):
        d = DataArray([1.0, 2.0, 3.0], masks=("n",))
        assert d.ndim == 1
        np.testing.assert_allclose(d.array, [1.0, 2.0, 3.0])

    def test_list_of_mvs_counting_first(self):
        mvs = [self.alg.multivector({"e1": i + 1.0}) for i in range(4)]
        d = DataArray(mvs, masks=("n", self.vec_mask))
        assert d.ndim == 2
        assert d.shape == (4, 3)
        assert d.masks == ("n", self.vec_mask)
        np.testing.assert_allclose(d.array[:, 0], [1.0, 2.0, 3.0, 4.0])

    def test_list_of_mvs_blade_first(self):
        mvs = [self.alg.multivector({"e1": i + 1.0}) for i in range(4)]
        d = DataArray(mvs, masks=(self.vec_mask, "n"))
        assert d.shape == (3, 4)
        assert d.masks == (self.vec_mask, "n")
        np.testing.assert_allclose(d.array[0, :], [1.0, 2.0, 3.0, 4.0])

    def test_rename_axis(self):
        d = DataArray(np.zeros((3, 4)), masks=("n", "m"))
        d2 = d.rename_axis("n", "pnt_idx")
        assert d.masks == ("n", "m")  # old unchanged
        assert d2.masks == ("pnt_idx", "m")

    def test_call_rename(self):
        d = DataArray(np.zeros((3, 4)), masks=("n", "m"))
        out = d(n="pnt_idx")
        assert out is d
        assert d.masks == ("pnt_idx", "m")

    def test_errors(self):
        with pytest.raises(TypeError):
            DataArray(np.zeros((2, 2)), masks=("n", 3))

        with pytest.raises(ValueError):
            DataArray(np.zeros((2, 2)), masks=("n",))

        with pytest.raises(ValueError):
            DataArray(np.zeros((2, 2)), masks=("n", "n"))

        with pytest.raises(ValueError):
            DataArray(np.zeros((2, 2)), masks=("_", "*"))

        with pytest.raises(ValueError):
            mvs = [self.alg.multivector({"e1": 1.0}), self.alg.multivector({"e2": 1.0})]
            DataArray(mvs, masks=(self.vec_mask,))
