# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for product tensor correctness (GP, IP, OP) using MVTensor."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask, MVTensor
from pytanga.algebra import EInv, EProduct
from pytanga.tensor.convert import to_tensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


class TestProductTensorShape:
    """Shape correctness of the product tensor."""

    def test_shape_full_mask_gp(self, alg_float):
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.GP)
        assert isinstance(T, MVTensor)
        expected_c = len(full)  # 8 for E3
        assert T.shape == (expected_c, expected_c, expected_c)
        assert T.masks[1] == full  # a_mask
        assert T.masks[2] == full  # b_mask
        assert T.masks[0] == full  # c_mask

    def test_shape_subspace_masks(self, alg_float):
        a_mask = BladeMask(alg_float, [1, 2])  # e1, e2
        b_mask = BladeMask(alg_float, [1, 4])  # e1, e3
        c_mask = BladeMask(alg_float, [0, 3, 6])  # scalar, e12, e23
        T = product_tensor(a_mask, b_mask, c_mask, product=EProduct.GP)
        assert T.shape == (3, 2, 2)

    def test_shape_ip(self, alg_float):
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.IP)
        assert T.shape[1] == len(full)  # a_mask
        assert T.shape[2] == len(full)  # b_mask
        assert T.shape[0] == len(T.masks[0])
        assert T.shape[0] < len(full)  # fewer outputs than full algebra

    def test_shape_op(self, alg_float):
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.OP)
        assert T.shape == (len(full), len(full), len(full))

    def test_auto_c_mask(self, alg_float):
        a_mask = BladeMask(alg_float, [1])  # e1 only
        b_mask = BladeMask(alg_float, [2])  # e2 only
        T = product_tensor(a_mask, b_mask)
        assert set(T.masks[0].ids) == {3}
        assert T.shape == (1, 1, 1)


class TestGPTensorEntries:
    """Verify specific known entries in the GP tensor for E3."""

    @staticmethod
    def _blade_index(mask, blade_id):
        return mask.ids.index(blade_id)

    def test_scalar_from_same_blade(self, alg_float):
        """e1 * e1 = scalar (positive)."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.GP)
        e1_idx = self._blade_index(full, 1)
        s_idx = self._blade_index(full, 0)
        assert T.data[s_idx, e1_idx, e1_idx] == 1.0

    def test_bivector_from_orthogonal(self, alg_float):
        """e1 * e2 = e12 (positive)."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.GP)
        e1_idx = self._blade_index(full, 1)
        e2_idx = self._blade_index(full, 2)
        e12_idx = self._blade_index(full, 3)
        assert T.data[e12_idx, e1_idx, e2_idx] == 1.0

    def test_entries_are_pm1_or_zero(self, alg_float):
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.GP)
        unique = set(np.unique(T.data))
        assert unique <= {-1.0, 0.0, 1.0}


class TestIPTensor:
    """Inner product tensor properties."""

    def test_ip_zero_when_disjoint(self, alg_float):
        """IP is zero when blades are not in containment relationship."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.IP)
        e1_idx = full.ids.index(1)
        e2_idx = full.ids.index(2)
        col = T.data[:, e1_idx, e2_idx]
        assert np.all(col == 0.0)

    def test_ip_nonzero_for_scalar_left(self, alg_float):
        """IP with scalar gives zero (scalar contains nothing)."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.IP)
        s_idx = full.ids.index(0)
        e1_idx = full.ids.index(1)
        col = T.data[:, s_idx, e1_idx]
        assert np.all(col == 0.0)


class TestOPTensor:
    """Outer product tensor properties."""

    def test_op_zero_when_overlapping(self, alg_float):
        """OP is zero when blades share basis vectors."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.OP)
        e1_idx = full.ids.index(1)
        col = T.data[:, e1_idx, e1_idx]
        assert np.all(col == 0.0)

    def test_op_nonzero_for_disjoint(self, alg_float):
        """e1 ^ e2 = e12 (positive)."""
        full = BladeMask.full(alg_float)
        T = product_tensor(full, full, product=EProduct.OP)
        e1_idx = full.ids.index(1)
        e2_idx = full.ids.index(2)
        e12_idx = full.ids.index(3)
        assert T.data[e12_idx, e1_idx, e2_idx] == 1.0


class TestEinsumContraction:
    """Verify contraction via contract() produces the same result as algebra."""

    def test_gp_contraction(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.GP)

        rng = np.random.default_rng(123)
        A_coeffs = rng.uniform(-1, 1, len(full))
        B_coeffs = rng.uniform(-1, 1, len(full))

        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))

        C = contract("kij,i,j->k", O, tA, tB)
        assert C.masks == (full,)

        A = alg_float({int(bid): float(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg_float({int(bid): float(v) for bid, v in zip(full.ids, B_coeffs)})
        AB = A * B
        AB.prune()

        for i, bid in enumerate(full.ids):
            name = alg_float.blade_name(bid)
            expected = AB.to_dict().get(name, 0.0)
            assert C.data[i] == pytest.approx(expected, abs=1e-10)

    def test_ip_contraction(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.IP)

        rng = np.random.default_rng(456)
        A_coeffs = rng.uniform(-1, 1, len(full))
        B_coeffs = rng.uniform(-1, 1, len(full))

        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))

        C = contract("kij,i,j->k", O, tA, tB)

        A = alg_float({int(bid): float(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg_float({int(bid): float(v) for bid, v in zip(full.ids, B_coeffs)})
        AB = A | B
        AB.prune()

        for i, bid in enumerate(C.masks[0].ids):
            name = alg_float.blade_name(bid)
            expected = AB.to_dict().get(name, 0.0)
            assert C.data[i] == pytest.approx(expected, abs=1e-10)

    def test_op_contraction(self, alg_float):
        full = BladeMask.full(alg_float)
        O = product_tensor(full, full, product=EProduct.OP)

        rng = np.random.default_rng(789)
        A_coeffs = rng.uniform(-1, 1, len(full))
        B_coeffs = rng.uniform(-1, 1, len(full))

        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))

        C = contract("kij,i,j->k", O, tA, tB)

        A = alg_float({int(bid): float(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg_float({int(bid): float(v) for bid, v in zip(full.ids, B_coeffs)})
        AB = A ^ B
        AB.prune()

        for i, bid in enumerate(C.masks[0].ids):
            name = alg_float.blade_name(bid)
            expected = AB.to_dict().get(name, 0.0)
            assert C.data[i] == pytest.approx(expected, abs=1e-10)

    def test_subspace_contraction(self, alg_float):
        """Contraction with restricted masks should match the full-tensor result."""
        a_mask = BladeMask(alg_float, [1, 2])  # e1, e2
        b_mask = BladeMask(alg_float, [1, 2])
        O = product_tensor(a_mask, b_mask, product=EProduct.GP)

        tA = to_tensor(alg_float("3 e1 - 5 e2"), mask=a_mask)
        tB = to_tensor(alg_float("2 e1 + 7 e2"), mask=b_mask)

        C = contract("kij,i,j->k", O, tA, tB)

        A = alg_float("3 e1 - 5 e2")
        B = alg_float("2 e1 + 7 e2")
        AB = A * B
        AB.prune()

        for i, bid in enumerate(C.masks[0].ids):
            name = alg_float.blade_name(bid)
            expected = AB.to_dict().get(name, 0.0)
            assert C.data[i] == pytest.approx(expected, abs=1e-10)
