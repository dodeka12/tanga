# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for product tensor involution flags (a_inv, b_inv, c_inv, left)."""

import numpy as np
import pytest
from pytanga import Algebra, BladeMask, MVTensor
from pytanga.algebra import EInv, EProduct
from pytanga.tensor.convert import to_tensor
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor


class TestProductTensorEInv:
    """Involution flags for product_tensor (a_inv, b_inv, c_inv, left)."""

    @staticmethod
    def _random_mvs_and_tensors(alg, rng_seed=42):
        """Return (full_mask, tA, tB, A, B) for a Euclidean 3D algebra."""
        full = BladeMask.full(alg)
        rng = np.random.default_rng(rng_seed)
        A_coeffs = rng.uniform(-1, 1, len(full))
        B_coeffs = rng.uniform(-1, 1, len(full))
        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))
        A = alg({int(bid): float(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg({int(bid): float(v) for bid, v in zip(full.ids, B_coeffs)})
        return full, tA, tB, A, B

    # ------------------------------------------------------------------
    # left_inv
    # ------------------------------------------------------------------
    def test_default_is_identity(self, alg_float):
        full, tA, tB, _, _ = self._random_mvs_and_tensors(alg_float)
        T_def = product_tensor(full, full, product=EProduct.GP)
        T_id = product_tensor(
            full,
            full,
            product=EProduct.GP,
            a_inv=EInv.ID,
            b_inv=EInv.ID,
            c_inv=EInv.ID,
        )
        assert np.array_equal(T_def.data, T_id.data)

    def test_left_rev_matches_gp_with_rev_a(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_std = product_tensor(full, full, product=EProduct.GP)
        T_rev_left = product_tensor(full, full, product=EProduct.GP, a_inv=EInv.REV)

        A_rev = alg_float.rev(A)
        A_rev.prune()
        tA_rev = to_tensor(A_rev, mask=full)

        C_via_rev_a = contract("kij,i,j->k", T_std, tA_rev, tB)
        C_via_inv = contract("kij,i,j->k", T_rev_left, tA, tB)
        assert np.allclose(C_via_rev_a.data, C_via_inv.data)

    def test_left_conj_matches_gp_with_conj_a(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_std = product_tensor(full, full, product=EProduct.GP)
        T_conj_left = product_tensor(full, full, product=EProduct.GP, a_inv=EInv.CONJ)

        A_conj = alg_float.conj(A)
        A_conj.prune()
        tA_conj = to_tensor(A_conj, mask=full)

        C_via_conj_a = contract("kij,i,j->k", T_std, tA_conj, tB)
        C_via_inv = contract("kij,i,j->k", T_conj_left, tA, tB)
        assert np.allclose(C_via_conj_a.data, C_via_inv.data)

    # ------------------------------------------------------------------
    # right_inv
    # ------------------------------------------------------------------
    def test_right_rev_matches_gp_with_rev_b(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_std = product_tensor(full, full, product=EProduct.GP)
        T_rev_right = product_tensor(full, full, product=EProduct.GP, b_inv=EInv.REV)

        B_rev = alg_float.rev(B)
        B_rev.prune()
        tB_rev = to_tensor(B_rev, mask=full)

        C_via_rev_b = contract("kij,i,j->k", T_std, tA, tB_rev)
        C_via_inv = contract("kij,i,j->k", T_rev_right, tA, tB)
        assert np.allclose(C_via_rev_b.data, C_via_inv.data)

    def test_right_conj_matches_gp_with_conj_b(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_std = product_tensor(full, full, product=EProduct.GP)
        T_conj_right = product_tensor(full, full, product=EProduct.GP, b_inv=EInv.CONJ)

        B_conj = alg_float.conj(B)
        B_conj.prune()
        tB_conj = to_tensor(B_conj, mask=full)

        C_via_conj_b = contract("kij,i,j->k", T_std, tA, tB_conj)
        C_via_inv = contract("kij,i,j->k", T_conj_right, tA, tB)
        assert np.allclose(C_via_conj_b.data, C_via_inv.data)

    # ------------------------------------------------------------------
    # c_inv (result involution)
    # ------------------------------------------------------------------
    def test_c_rev_matches_rev_of_gp_result(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_c_rev = product_tensor(full, full, product=EProduct.GP, c_inv=EInv.REV)

        AB = A * B
        AB.prune()
        AB_rev = alg_float.rev(AB)
        AB_rev.prune()

        C_via_inv = contract("kij,i,j->k", T_c_rev, tA, tB)
        C_expected = to_tensor(AB_rev, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    def test_c_conj_matches_conj_of_gp_result(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_c_conj = product_tensor(full, full, product=EProduct.GP, c_inv=EInv.CONJ)

        AB = A * B
        AB.prune()
        AB_conj = alg_float.conj(AB)
        AB_conj.prune()

        C_via_inv = contract("kij,i,j->k", T_c_conj, tA, tB)
        C_expected = to_tensor(AB_conj, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    # ------------------------------------------------------------------
    # left=False (operand order swap)
    # ------------------------------------------------------------------
    def test_left_false_is_b_times_a(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T_right = product_tensor(full, full, product=EProduct.GP, left=False)

        BA = B * A
        BA.prune()

        C_via_inv = contract("kij,i,j->k", T_right, tA, tB)
        C_expected = to_tensor(BA, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    def test_left_false_with_rev(self, alg_float):
        """left=False with a_inv=REV: rev is applied to the a-mask blades (axis 1).

        When left=False, the product order is B ∘ A.  a_inv applies to
        tensor axis 1 (a_mask), so the a-mask blades (which become the right
        operand in the product) are reversed: B * rev(A).
        """
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(
            full,
            full,
            product=EProduct.GP,
            left=False,
            a_inv=EInv.REV,
        )

        # left=False means B ∘ A.  a_inv on a_mask → rev(A) as right operand
        A_rev = alg_float.rev(A)
        A_rev.prune()
        BA_rev = B * A_rev
        BA_rev.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        C_expected = to_tensor(BA_rev, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    # ------------------------------------------------------------------
    # combined involutions
    # ------------------------------------------------------------------
    def test_both_rev(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(
            full, full, product=EProduct.GP, a_inv=EInv.REV, b_inv=EInv.REV
        )

        A_rev = alg_float.rev(A)
        A_rev.prune()
        B_rev = alg_float.rev(B)
        B_rev.prune()
        expected = A_rev * B_rev
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        C_expected = to_tensor(expected, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    def test_all_three_conj(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(
            full,
            full,
            product=EProduct.GP,
            a_inv=EInv.CONJ,
            b_inv=EInv.CONJ,
            c_inv=EInv.CONJ,
        )

        A_conj = alg_float.conj(A)
        A_conj.prune()
        B_conj = alg_float.conj(B)
        B_conj.prune()
        AB_conj = A_conj * B_conj
        AB_conj.prune()
        expected = alg_float.conj(AB_conj)
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        C_expected = to_tensor(expected, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    def test_mixed_rev_and_conj(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(
            full,
            full,
            product=EProduct.GP,
            a_inv=EInv.REV,
            b_inv=EInv.CONJ,
            c_inv=EInv.REV,
        )

        A_rev = alg_float.rev(A)
        A_rev.prune()
        B_conj = alg_float.conj(B)
        B_conj.prune()
        AB = A_rev * B_conj
        AB.prune()
        expected = alg_float.rev(AB)
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        C_expected = to_tensor(expected, mask=full)
        assert np.allclose(C_via_inv.data, C_expected.data)

    # ------------------------------------------------------------------
    # shape and entry integrity
    # ------------------------------------------------------------------
    def test_shape_unchanged_by_involution(self, alg_float):
        full = BladeMask.full(alg_float)
        T_std = product_tensor(full, full, product=EProduct.GP)
        for kw in [
            {"a_inv": EInv.REV},
            {"b_inv": EInv.CONJ},
            {"c_inv": EInv.REV},
            {"a_inv": EInv.REV, "b_inv": EInv.CONJ, "c_inv": EInv.CONJ},
            {"left": False},
            {"left": False, "b_inv": EInv.REV},
        ]:
            T = product_tensor(full, full, product=EProduct.GP, **kw)
            assert T.shape == T_std.shape, f"shape mismatch for {kw}"
            assert T.masks == T_std.masks, f"mask mismatch for {kw}"

    def test_entries_are_pm1_or_zero_with_involution(self, alg_float):
        full = BladeMask.full(alg_float)
        for kw in [
            {"a_inv": EInv.REV},
            {"b_inv": EInv.CONJ},
            {"c_inv": EInv.REV},
            {"a_inv": EInv.REV, "b_inv": EInv.CONJ, "c_inv": EInv.CONJ},
        ]:
            T = product_tensor(full, full, product=EProduct.GP, **kw)
            unique = set(np.unique(T.data))
            assert unique <= {-1.0, 0.0, 1.0}, f"bad entries for {kw}"

    # ------------------------------------------------------------------
    # IP and OP with involution
    # ------------------------------------------------------------------
    def test_ip_with_left_rev(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(full, full, product=EProduct.IP, a_inv=EInv.REV)

        A_rev = alg_float.rev(A)
        A_rev.prune()
        expected = A_rev | B
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        for i, bid in enumerate(C_via_inv.masks[0].ids):
            name = alg_float.blade_name(bid)
            exp_val = expected.to_dict().get(name, 0.0)
            assert C_via_inv.data[i] == pytest.approx(exp_val, abs=1e-10)

    def test_op_with_right_rev(self, alg_float):
        full, tA, tB, A, B = self._random_mvs_and_tensors(alg_float)
        T = product_tensor(full, full, product=EProduct.OP, b_inv=EInv.REV)

        B_rev = alg_float.rev(B)
        B_rev.prune()
        expected = A ^ B_rev
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        for i, bid in enumerate(C_via_inv.masks[0].ids):
            name = alg_float.blade_name(bid)
            exp_val = expected.to_dict().get(name, 0.0)
            assert C_via_inv.data[i] == pytest.approx(exp_val, abs=1e-10)

    # ------------------------------------------------------------------
    # integer dtype
    # ------------------------------------------------------------------
    def test_integer_left_rev(self, alg_int):
        full = BladeMask.full(alg_int)
        rng = np.random.default_rng(17)
        A_coeffs = rng.integers(-3, 4, len(full)).astype(np.int64)
        B_coeffs = rng.integers(-3, 4, len(full)).astype(np.int64)
        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))
        A = alg_int({int(bid): int(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg_int({int(bid): int(v) for bid, v in zip(full.ids, B_coeffs)})

        T = product_tensor(full, full, product=EProduct.GP, a_inv=EInv.REV)
        assert T.data.dtype == np.int64

        A_rev = alg_int.rev(A)
        A_rev.prune()
        expected = A_rev * B
        expected.prune()

        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        for i, bid in enumerate(full.ids):
            name = alg_int.blade_name(bid)
            exp_val = expected.to_dict().get(name, 0)
            assert int(C_via_inv.data[i]) == int(exp_val)

    # ------------------------------------------------------------------
    # subspace masks with involution
    # ------------------------------------------------------------------
    def test_subspace_with_c_inv(self, alg_float):
        a_mask = BladeMask(alg_float, [1, 2, 3])  # e1, e2, e12
        b_mask = BladeMask(alg_float, [1, 2, 3])
        T = product_tensor(a_mask, b_mask, product=EProduct.GP, c_inv=EInv.REV)

        A = alg_float("2 e1 - 3 e2 + e12")
        B = alg_float("e1 + 2 e2 - e12")
        AB = A * B
        AB.prune()
        expected = alg_float.rev(AB)
        expected.prune()

        tA = to_tensor(A, mask=a_mask)
        tB = to_tensor(B, mask=b_mask)
        C_via_inv = contract("kij,i,j->k", T, tA, tB)
        for i, bid in enumerate(C_via_inv.masks[0].ids):
            name = alg_float.blade_name(bid)
            exp_val = expected.to_dict().get(name, 0.0)
            assert C_via_inv.data[i] == pytest.approx(exp_val, abs=1e-10)

    # ------------------------------------------------------------------
    # CONJ vs REV distinguished in non-Euclidean algebra
    # ------------------------------------------------------------------
    def test_conj_differs_from_rev_in_p3(self):
        """In P3 (signature mask=0b1000), the e4 basis vector has negative metric,
        so conj ≠ rev for blades containing e4."""
        alg = Algebra(4, 0b1000, "float64")
        full = BladeMask.full(alg)

        T_rev = product_tensor(full, full, product=EProduct.GP, a_inv=EInv.REV)
        T_conj = product_tensor(full, full, product=EProduct.GP, a_inv=EInv.CONJ)
        assert not np.allclose(T_rev.data, T_conj.data), (
            "REV and CONJ tensors should differ in a non-Euclidean algebra"
        )

        # Verify by contracting: rev(A)*B should match tensor, conj(A)*B should match tensor
        rng = np.random.default_rng(99)
        A_coeffs = rng.uniform(-1, 1, len(full))
        B_coeffs = rng.uniform(-1, 1, len(full))
        tA = MVTensor(data=A_coeffs, masks=(full,))
        tB = MVTensor(data=B_coeffs, masks=(full,))
        A = alg({int(bid): float(v) for bid, v in zip(full.ids, A_coeffs)})
        B = alg({int(bid): float(v) for bid, v in zip(full.ids, B_coeffs)})

        A_rev = alg.rev(A)
        A_rev.prune()
        expected_rev = A_rev * B
        expected_rev.prune()
        C_rev = contract("kij,i,j->k", T_rev, tA, tB)
        C_rev_expected = to_tensor(expected_rev, mask=full)
        assert np.allclose(C_rev.data, C_rev_expected.data)

        A_conj = alg.conj(A)
        A_conj.prune()
        expected_conj = A_conj * B
        expected_conj.prune()
        C_conj = contract("kij,i,j->k", T_conj, tA, tB)
        C_conj_expected = to_tensor(expected_conj, mask=full)
        assert np.allclose(C_conj.data, C_conj_expected.data)


class TestModularTensor:
    """Modular integer tensor."""

    def test_int_dtype(self, alg_int):
        full = BladeMask.full(alg_int)
        T = product_tensor(full, full, product=EProduct.GP)
        assert T.data.dtype == np.int64
        unique = set(np.unique(T.data))
        assert unique <= {-1, 0, 1}
