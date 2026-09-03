# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for DataArray bindings in ``Expression.__call__``."""

import numpy as np
import pytest

from pytanga import DataArray
from pytanga.basis import BasisN3
from pytanga.blade_mask import BladeMask
from pytanga.expression import Expression, Variable
from pytanga.expression._labels import _reset_allocator


def _close(a, b) -> bool:
    return (a - b).mag < 1e-12


class TestDataArrayBinding:
    def setup_method(self):
        _reset_allocator()
        self.N3 = BasisN3()
        self.bi_mask = BladeMask(self.N3, [self.N3.E12, self.N3.E13, self.N3.E23])
        self.point_mask = BladeMask(self.N3, [self.N3.E1, self.N3.E2, self.N3.E3])
        self.bi_var = Variable("bi_var", self.bi_mask)
        self.x_pnt = Variable("x_pnt", self.point_mask)
        self.expr = self.x_pnt ^ (self.bi_var | self.x_pnt)
        self.points = np.random.default_rng(0).random((100, 3))
        self.bi = self.N3({self.N3.E12: 1.0, self.N3.E13: 2.0, self.N3.E23: 3.0})

    def _point_mv(self, coeffs):
        return self.N3(
            {
                self.N3.E1: float(coeffs[0]),
                self.N3.E2: float(coeffs[1]),
                self.N3.E3: float(coeffs[2]),
            }
        )

    def _expected(self, points):
        return [self._point_mv(p) ^ (self.bi | self._point_mv(p)) for p in points]

    def _sum_expected(self, points, scalars):
        total = self.N3({})
        for p, s in zip(points, scalars):
            total = total + self._expected([p])[0] * s
        return total

    def test_dataarray_variable_binding(self):
        partial = self.expr(
            x_pnt=DataArray(self.points, masks=("pnt_idx", self.point_mask))
        )
        assert isinstance(partial, Expression)
        assert set(partial.names) == {"bi_var"}
        assert partial._has_counting_axes()

        pnt_axes = [ax for ax in partial.tensor.labels if ax.name == "pnt_idx"]
        assert len(pnt_axes) == 1 and pnt_axes[0].mode == "_"

        result = partial(bi_var=self.bi)
        assert isinstance(result, list) and len(result) == len(self.points)
        for r, e in zip(result, self._expected(self.points)):
            assert _close(r, e)

    def test_dataarray_from_mvs(self):
        mvs = [self._point_mv(p) for p in self.points]
        partial = self.expr(x_pnt=DataArray(mvs, masks=("pnt_idx", self.point_mask)))
        result = partial(bi_var=self.bi)
        for r, e in zip(result, self._expected(self.points)):
            assert _close(r, e)

    def test_two_counting_axes(self):
        points = np.random.default_rng(1).random((100, 2, 3))
        partial = self.expr(
            x_pnt=DataArray(points, masks=("pnt_idx", "group_idx", self.point_mask))
        )
        assert partial._has_counting_axes()
        names = {ax.name for ax in partial.tensor.labels}
        assert {"pnt_idx", "group_idx"} <= names

        result = partial(bi_var=self.bi)
        assert isinstance(result, list) and len(result) == 100
        for i, row in enumerate(result):
            assert isinstance(row, list) and len(row) == 2
            for g, r in enumerate(row):
                assert _close(r, self._expected(points[i, g][None, :])[0])

    def test_counting_axis_sum(self):
        partial = self.expr(
            x_pnt=DataArray(self.points, masks=("pnt_idx", self.point_mask))
        )
        scalars = np.random.default_rng(1).random(100)
        reduced = partial(pnt_idx=scalars)
        assert isinstance(reduced, Expression)
        assert set(reduced.names) == {"bi_var"}
        assert not reduced._has_counting_axes()

        result = reduced(bi_var=self.bi)
        assert _close(result, self._sum_expected(self.points, scalars))

    def test_counting_axis_multiply(self):
        partial = self.expr(
            x_pnt=DataArray(self.points, masks=("pnt_idx", self.point_mask))
        )
        scalars = np.random.default_rng(1).random(100)
        expected = [self._expected([p])[0] * s for p, s in zip(self.points, scalars)]

        datas = (
            DataArray(scalars, masks=("_",)),
            DataArray(scalars, masks=("pnt_idx_",)),
            DataArray(scalars, masks=("n",)).rename_axis("n", "_"),
            DataArray(scalars, masks=("n",))(n="_"),
        )
        for data in datas:
            reduced = partial(pnt_idx=data)
            assert isinstance(reduced, Expression)
            assert reduced._has_counting_axes()
            pnt_axes = [ax for ax in reduced.tensor.labels if ax.name == "pnt_idx"]
            assert len(pnt_axes) == 1 and pnt_axes[0].mode == "_"
            result = reduced(bi_var=self.bi)
            for r, e in zip(result, expected):
                assert _close(r, e)

    def test_counting_axis_1d_implicit_sum(self):
        partial = self.expr(
            x_pnt=DataArray(self.points, masks=("pnt_idx", self.point_mask))
        )
        scalars = np.random.default_rng(1).random(100)
        a = partial(pnt_idx=scalars)
        b = partial(pnt_idx=DataArray(scalars, masks=("n",)))
        c = partial(pnt_idx=DataArray(scalars, masks=("*",)))
        assert _close(a(bi_var=self.bi), b(bi_var=self.bi))
        assert _close(a(bi_var=self.bi), c(bi_var=self.bi))

    def test_contract_one_keep_one(self):
        points = np.random.default_rng(1).random((100, 2, 3))
        scalars2d = np.random.default_rng(2).random((100, 2))
        partial = self.expr(
            x_pnt=DataArray(points, masks=("pnt_idx", "group_idx", self.point_mask))
        )

        datas = (
            DataArray(scalars2d, masks=("pnt_idx", "group_idx_")),
            DataArray(scalars2d, masks=("pnt_idx", "group_idx")),
            DataArray(scalars2d, masks=("*", "group_idx")),
        )
        for data in datas:
            reduced = partial(pnt_idx=data)
            names = {ax.name for ax in reduced.tensor.labels}
            assert "group_idx" in names and "pnt_idx" not in names
            gax = [ax for ax in reduced.tensor.labels if ax.name == "group_idx"][0]
            assert gax.mode == "_"

            result = reduced(bi_var=self.bi)
            assert isinstance(result, list) and len(result) == 2
            for g in range(2):
                expected = self.N3({})
                for i in range(100):
                    expected = (
                        expected + self._expected([points[i, g]])[0] * scalars2d[i, g]
                    )
                assert _close(result[g], expected)

    def test_contract_multiply_keep_one(self):
        points = np.random.default_rng(1).random((100, 2, 3))
        scalars2d = np.random.default_rng(2).random((100, 2))
        partial = self.expr(
            x_pnt=DataArray(points, masks=("pnt_idx", "group_idx", self.point_mask))
        )

        reduced = partial(pnt_idx=DataArray(scalars2d, masks=("_", "group_idx")))
        names = {ax.name for ax in reduced.tensor.labels}
        assert {"pnt_idx", "group_idx"} <= names

        result = reduced(bi_var=self.bi)
        assert isinstance(result, list) and len(result) == 100
        for i, row in enumerate(result):
            assert isinstance(row, list) and len(row) == 2
            for g in range(2):
                expected = self._expected([points[i, g]])[0] * scalars2d[i, g]
                assert _close(row[g], expected)

    def test_variable_binding_errors(self):
        with pytest.raises(ValueError):
            self.expr(x_pnt=DataArray(self.points, masks=("pnt_idx", "group_idx")))

        with pytest.raises(ValueError):
            self.expr(x_pnt=DataArray(self.points, masks=("pnt_idx", self.bi_mask)))

        with pytest.raises(ValueError):
            self.expr(x_pnt=DataArray(self.points, masks=("k", self.point_mask)))

    def test_reduction_errors(self):
        partial = self.expr(
            x_pnt=DataArray(self.points, masks=("pnt_idx", self.point_mask))
        )
        scalars = np.random.default_rng(1).random(100)

        with pytest.raises(ValueError):
            partial(unknown=scalars)

        with pytest.raises(ValueError):
            partial(pnt_idx=np.random.default_rng(0).random(7))

        with pytest.raises(ValueError):
            # multi-axis DataArray that does not name the key
            partial(pnt_idx=DataArray(np.zeros((100, 2)), masks=("n", "m")))

        with pytest.raises(ValueError):
            # duplicate key markers
            partial(pnt_idx=DataArray(np.zeros((100, 2)), masks=("_", "pnt_idx")))
