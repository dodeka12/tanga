# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for MVTensor, to_tensor, from_tensor, and contract."""

import numpy as np
import pytest
from pytanga import BladeMask, MVTensor
from pytanga.algebra import EProduct
from pytanga.tensor.ops import contract
from pytanga.tensor.convert import from_tensor, to_tensor
from pytanga.tensor.product import product_tensor


class TestToTensor:
    def test_single_mv_rank1(self, alg_float):
        mv = alg_float({"e1": 3.0, "e2": -5.0})
        mask = BladeMask(mv)
        t = to_tensor(mv, mask=mask)
        assert isinstance(t, MVTensor)
        assert t.data.ndim == 1
        assert t.masks == (mask,)
        assert t.shape == (len(mask),)
        assert t.data[mask.index(1)] == 3.0
        assert t.data[mask.index(2)] == -5.0

    def test_list_of_mvs_rank2(self, alg_float):
        mvs = [alg_float("e1"), alg_float("e2"), alg_float("e1 + e2")]
        mask = BladeMask(alg_float, [1, 2])
        t = to_tensor(mvs, mask=mask)
        assert isinstance(t, MVTensor)
        assert t.shape == (2, 3)
        assert t.masks == (mask, None)
        # column 0: e1
        assert t.data[mask.index(1), 0] == 1.0
        assert t.data[mask.index(2), 0] == 0.0
        # column 2: e1+e2
        assert t.data[mask.index(1), 2] == 1.0
        assert t.data[mask.index(2), 2] == 1.0


class TestFromTensor:
    def test_single_mv_roundtrip(self, alg_float):
        mv = alg_float({"e1": 3.0, "e2": -5.0})
        t = to_tensor(mv)
        recovered = from_tensor(t)
        diff = mv - recovered
        diff.prune()
        assert not diff.to_dict()

    def test_list_roundtrip(self, alg_float):
        mvs = [alg_float("e1"), alg_float("2 e1 - 3 e2 + e12")]
        t = to_tensor(mvs)
        recovered = from_tensor(t)
        assert isinstance(recovered, list)
        assert len(recovered) == 2
        for orig, rec in zip(mvs, recovered):
            d = orig - rec
            d.prune()
            assert not d.to_dict()

    def test_nested_rank3(self, alg_float):
        mvs = [[alg_float("e1"), alg_float("e2")], [alg_float("e3"), alg_float("e12")]]
        # manually build rank-3 tensor
        mask = BladeMask(alg_float, [1, 2, 3, 4])
        arr = np.zeros((len(mask), 2, 2))
        for i, row in enumerate(mvs):
            for j, mv in enumerate(row):
                for bid in mask.ids:
                    name = alg_float.blade_name(bid)
                    val = mv.to_dict().get(name, 0.0)
                    arr[mask.index(bid), i, j] = val
        t = MVTensor(data=arr, masks=(mask, None, None))
        recovered = from_tensor(t)
        assert isinstance(recovered, list)
        assert len(recovered) == 2
        for i, row in enumerate(recovered):
            assert isinstance(row, list)
            assert len(row) == 2
            for j, mv in enumerate(row):
                d = mvs[i][j] - mv
                d.prune()
                assert not d.to_dict()

    def test_zero_masks_error(self, alg_float):
        t = MVTensor(data=np.array([[1.0, 2.0]]), masks=(None, None))
        with pytest.raises(ValueError, match="exactly one BladeMask"):
            from_tensor(t)

    def test_two_masks_error(self, alg_float):
        mask = BladeMask(alg_float, [1])
        t = MVTensor(data=np.array([[1.0]]), masks=(mask, mask))
        with pytest.raises(ValueError, match="exactly one BladeMask"):
            from_tensor(t)


class TestContract:
    def test_gp_single(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.GP)
        tA = to_tensor(alg_float("e1"), mask=full)
        tB = to_tensor(alg_float("e2"), mask=full)
        C = contract("kij,i,j->k", O, tA, tB)
        assert C.masks == (full,)
        # e1 * e2 = e12 (blade id 3)
        assert C.data[full.index(3)] == pytest.approx(1.0)

    def test_batch_gp(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.GP)

        mvs_a = [alg_float("e1"), alg_float("e2"), alg_float("e3")]
        mvs_b = [alg_float("e2"), alg_float("e3"), alg_float("e1")]
        tA = to_tensor(mvs_a, mask=full)  # (8, 3)
        tB = to_tensor(mvs_b, mask=full)  # (8, 3)

        C = contract("kij,in,jn->kn", O, tA, tB)
        assert C.masks == (full, None)
        assert C.shape == (len(full), 3)

        for n, (a, b) in enumerate(zip(mvs_a, mvs_b)):
            expected = a * b
            expected.prune()
            for bid in full.ids:
                name = alg_float.blade_name(bid)
                exp = expected.to_dict().get(name, 0.0)
                assert C.data[full.index(bid), n] == pytest.approx(exp, abs=1e-10)

    def test_mask_incompatibility(self, alg_float):
        mask_a = BladeMask(alg_float, [1])  # e1 only
        mask_b = BladeMask(alg_float, [1, 2])  # e1, e2
        O = product_tensor(mask_a, mask_a, product=EProduct.GP)
        tA = MVTensor(data=np.array([1.0]), masks=(mask_a,))
        tB = MVTensor(data=np.array([1.0, 0.0]), masks=(mask_b,))
        with pytest.raises(ValueError, match="incompatible masks"):
            contract("kij,i,j->k", O, tA, tB)

    def test_subscript_axis_count_mismatch(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.GP)
        tA = MVTensor(data=np.ones(len(full)), masks=(full,))
        with pytest.raises(ValueError, match="subscript"):
            contract("kij,ij->k", O, tA)  # tA has 1 axis, subscript says 2
