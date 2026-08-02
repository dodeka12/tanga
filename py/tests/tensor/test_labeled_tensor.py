# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for MVLabeledTensor label-aware tensor operations."""

import numpy as np
import pytest

from pytanga import Algebra, BladeMask, MVTensor
from pytanga.tensor._labeled import (
    MVLabeledTensor,
    _canonicalise,
    _raw_names,
    _mode_at,
    _is_elemwise,
    iter_labels,
)
from pytanga.tensor.convert import to_tensor
from pytanga.tensor.ops import _build_subscript, contract_labeled
from pytanga.tensor.product import product_tensor
from pytanga.algebra import _as_mv


@pytest.fixture(scope="module")
def alg():
    return Algebra.from_name("E3", dtype="float64")


@pytest.fixture(scope="module")
def full(alg):
    return BladeMask.full(alg)


# ---------------------------------------------------------------------------
# 7.1 – Label canonicalisation
# ---------------------------------------------------------------------------


class TestLabelCanonicalisation:
    def test_basic(self):
        assert _canonicalise("kij") == "k*i*j*"
        assert _canonicalise("k*i*j*") == "k*i*j*"
        assert _canonicalise("in_") == "i*n_"
        assert _canonicalise("i*n_") == "i*n_"
        assert _canonicalise("i_") == "i_"
        assert _canonicalise("ij_n") == "i*j_n*"
        assert _canonicalise("i*n_j*") == "i*n_j*"

    def test_errors(self):
        with pytest.raises(ValueError):
            _canonicalise("_i")
        with pytest.raises(ValueError):
            _canonicalise("i__")
        with pytest.raises(ValueError):
            _canonicalise("_")
        with pytest.raises(ValueError):
            _canonicalise("1ab")

    def test_raw_names(self):
        assert _raw_names("k*i*j*") == "kij"
        assert _raw_names("i*n_") == "in"
        assert _raw_names("i_") == "i"

    def test_mode_at(self):
        assert _mode_at("i*n_", 0) == "*"
        assert _mode_at("i*n_", 1) == "_"
        assert not _is_elemwise("i*n_", 0)
        assert _is_elemwise("i*n_", 1)


# ---------------------------------------------------------------------------
# 7.2 – __getitem__ on MVTensor
# ---------------------------------------------------------------------------


class TestMVTensorGetItem:
    def test_string_creates_labeled(self, alg, full):
        G = product_tensor(full, full)
        G_labeled = G["kij"]
        assert isinstance(G_labeled, MVLabeledTensor)
        assert G_labeled.labels == "k*i*j*"

    def test_product_tensor_labeled(self, alg, full):
        G = product_tensor(full, full)
        G_labeled = G["kij"]
        assert G_labeled.tensor is G  # same underlying tensor

    def test_single_mv_labeled(self, alg, full):
        mv = _as_mv(alg, "1 + 2e1 + 3e2")
        A = to_tensor(mv, mask=full)
        A_labeled = A["i"]
        assert isinstance(A_labeled, MVLabeledTensor)
        assert A_labeled.labels == "i*"


# ---------------------------------------------------------------------------
# 7.3 – __getitem__ slicing on MVTensor
# ---------------------------------------------------------------------------


class TestMVTensorSlicing:
    def test_slice_rank1(self, alg, full):
        mv = _as_mv(alg, "1 + 2e1 + 3e2")
        A = to_tensor(mv, mask=full)
        sliced = A[0:3]
        assert isinstance(sliced, MVTensor)
        assert sliced.shape == (3,)
        # Mask is filtered to match the slice: first 3 blade ids
        expected_mask = BladeMask(full.algebra, full.ids[:3])
        assert sliced.masks == (expected_mask,)

    def test_integer_index_collapses(self, alg, full):
        mv = _as_mv(alg, "1 + 2e1 + 3e2")
        A = to_tensor(mv, mask=full)
        scalar = A[2]
        # Integer index on rank-1 returns 0-d data; MVTensor.__getitem__
        # forwards scalar results directly
        assert isinstance(scalar, (np.ndarray, np.number, float, int))

    def test_fancy_indexing_fallback(self, alg, full):
        mv = _as_mv(alg, "1 + 2e1 + 3e2")
        A = to_tensor(mv, mask=full)
        result = A[[0, 1, 3]]
        assert isinstance(result, np.ndarray)


# ---------------------------------------------------------------------------
# 7.4 – __getitem__ transpose/reorder on MVLabeledTensor
# ---------------------------------------------------------------------------


class TestTranspose:
    def test_ij_ji(self, full):
        t = MVLabeledTensor.zeros("ij", [full, full])
        t_t = t["ij->ji"]
        assert t_t.labels == "j*i*"
        assert t_t.shape == (len(full), len(full))
        assert np.may_share_memory(t.tensor.data, t_t.tensor.data)

    def test_kij_jki(self, full):
        t = MVLabeledTensor.zeros("kij", [full, full, full])
        t_t = t["kij->jki"]
        assert t_t.labels == "j*k*i*"
        assert t_t.shape == (len(full),) * 3

    def test_ijk_kji_reverse(self, full):
        t = MVLabeledTensor.zeros("ijk", [full, full, full])
        t_t = t["ijk->kji"]
        assert t_t.labels == "k*j*i*"
        assert t_t.shape == (len(full),) * 3

    def test_invalid_permutation(self, full):
        t = MVLabeledTensor.zeros("ij", [full, full])
        with pytest.raises(ValueError):
            _ = t["ij->jk"]  # different label sets

    def test_arrow_target_only_infer_source(self, full):
        """t["->ji"] infers source from tensor labels."""
        t = MVLabeledTensor.zeros("ij", [full, full])
        result = t["->ji"]
        assert result.labels == "j*i*"
        assert result.shape == (len(full), len(full))

    def test_arrow_target_only_rank3(self, full):
        """t["->jki"] on a rank-3 labeled tensor."""
        t = MVLabeledTensor.zeros("kij", [full, full, full])
        result = t["->jki"]
        assert result.labels == "j*k*i*"
        assert result.shape == (len(full),) * 3

    def test_arrow_target_only_with_modes(self, full):
        """t["->nij"] preserves element-wise modes from source."""
        t = MVLabeledTensor.zeros("i*n_", [full, 5])
        result = t["->ni"]
        assert result.labels == "n_i*"
        assert result.shape == (5, len(full))

    def test_arrow_source_only_reverse(self, full):
        """t["ij->"] infers destination from tensor labels (identity)."""
        t = MVLabeledTensor.zeros("ij", [full, full])
        result = t["ij->"]
        assert result.labels == "i*j*"
        assert result.shape == (len(full), len(full))

    def test_arrow_target_only_equivalent_to_explicit(self, full):
        """t["->ji"] produces same result as t["ij->ji"]."""
        t = MVLabeledTensor.zeros("ij", [full, full])
        result1 = t["->ji"]
        result2 = t["ij->ji"]
        assert result1.labels == result2.labels
        assert np.array_equal(result1.tensor.data, result2.tensor.data)


# ---------------------------------------------------------------------------
# 7.5 – Contraction __mul__
# ---------------------------------------------------------------------------


class TestMulContraction:
    def test_basic_gp(self, alg, full):
        O = product_tensor(full, full)
        mvs = [_as_mv(alg, "e1"), _as_mv(alg, "e2")]
        A = to_tensor(mvs[0], mask=full)
        B = to_tensor(mvs[1], mask=full)

        result = O["kij"] * A["i"] * B["j"]
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "k*"
        # e1 * e2 = e12 (blade id 3 in E3)
        expected_id = 3
        assert result.tensor.data[expected_id] != 0

    def test_outer_product(self, full):
        A = MVLabeledTensor.zeros("i", [full])
        B = MVLabeledTensor.zeros("j", [full])
        result = A["i"] * B["j"]
        assert result.labels == "i*j*"
        assert result.shape == (len(full), len(full))

    def test_scalar_mul(self, full):
        A = MVLabeledTensor.zeros("i", [full])
        result = A["i"] * 2.0
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"

    def test_scalar_rmul(self, full):
        A = MVLabeledTensor.zeros("i", [full])
        result = 3.0 * A["i"]
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"

    def test_no_shared_labels(self, full):
        A = MVLabeledTensor.zeros("ij", [full, 3])
        B = MVLabeledTensor.zeros("kl", [4, 5])
        result = A["ij"] * B["kl"]
        assert result.labels == "i*j*k*l*"
        assert result.shape == (len(full), 3, 4, 5)


# ---------------------------------------------------------------------------
# 7.6 – Element-wise _ suffix
# ---------------------------------------------------------------------------


class TestElementWise:
    def test_both_elemwise(self, full):
        A = MVLabeledTensor.zeros("in_", [full, 5])
        B = MVLabeledTensor.zeros("jn_", [full, 5])
        result = A["in_"] * B["jn_"]
        assert result.labels == "i*j*n_"
        assert result.shape == (len(full), len(full), 5)

    def test_one_elemwise(self, full):
        A = MVLabeledTensor.zeros("in_", [full, 5])
        B = MVLabeledTensor.zeros("jn", [full, 5])
        result = A["in_"] * B["jn"]
        assert result.labels == "i*j*n_"
        assert result.shape == (len(full), len(full), 5)

    def test_explicit_star_format(self, full):
        A = MVLabeledTensor.zeros("i*n_", [full, 5])
        B = MVLabeledTensor.zeros("j*n_", [full, 5])
        result = A["i*n_"] * B["j*n_"]
        assert result.labels == "i*j*n_"


# ---------------------------------------------------------------------------
# 7.7 – Division
# ---------------------------------------------------------------------------


class TestDivision:
    def test_division(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("jk", [full, full])
        # Fill B with ones to avoid division by zero
        B.tensor.data[:] = 2.0
        A.tensor.data[:] = 4.0
        result = A["ij"] / B["jk"]
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*k*"

    def test_division_by_ones(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("j", [full])
        A.tensor.data[:] = 6.0
        B.tensor.data[:] = 2.0
        result = A["ij"] / B["j"]
        # 6 / 2 = 3 for each element; contraction on j
        assert result.labels == "i*"

    def test_scalar_division(self, full):
        A = MVLabeledTensor.zeros("i", [full])
        result = A["i"] / 3.0
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"

    def test_scalar_rdivision(self, full):
        A = MVLabeledTensor.zeros("i", [full])
        A.tensor.data[:] = 2.0
        result = 6.0 / A["i"]
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"
        assert np.allclose(result.tensor.data, 3.0)


# ---------------------------------------------------------------------------
# 7.8 – Addition / subtraction
# ---------------------------------------------------------------------------


class TestAddSub:
    def test_add_broadcast(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("jk", [full, full])
        result = A["ij"] + B["jk"]
        assert result.labels == "i*j*k*"
        assert result.shape == (len(full), len(full), len(full))

    def test_add_same_labels(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("ij", [full, full])
        A.tensor.data[:] = 1.0
        B.tensor.data[:] = 2.0
        result = A["ij"] + B["ij"]
        assert result.labels == "i*j*"
        assert np.allclose(result.tensor.data, 3.0)

    def test_sub_same_labels(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("ij", [full, full])
        A.tensor.data[:] = 5.0
        B.tensor.data[:] = 2.0
        result = A["ij"] - B["ij"]
        assert result.labels == "i*j*"
        assert np.allclose(result.tensor.data, 3.0)

    def test_add_incompatible_masks(self, full):
        sub = BladeMask(full.algebra, [1, 2])
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("kj", [sub, full])
        with pytest.raises(ValueError):
            _ = A["ij"] + B["kj"]


# ---------------------------------------------------------------------------
# 7.9 – Scalar ops
# ---------------------------------------------------------------------------


class TestScalarOps:
    def test_mul_scalar(self, full):
        t = MVLabeledTensor.zeros("i", [full])
        result = t.mul_scalar(2.0)
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"

    def test_div_scalar(self, full):
        t = MVLabeledTensor.zeros("i", [full])
        result = t.div_scalar(2.0)
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"

    def test_rdiv_scalar(self, full):
        t = MVLabeledTensor.zeros("i", [full])
        t.tensor.data[:] = 2.0
        result = t.rdiv_scalar(10.0)
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "i*"
        assert np.allclose(result.tensor.data, 5.0)


# ---------------------------------------------------------------------------
# 7.10 – Chaining
# ---------------------------------------------------------------------------


class TestChaining:
    def test_three_tensor_contraction(self, alg, full):
        O = product_tensor(full, full)
        mvs = [_as_mv(alg, "e1"), _as_mv(alg, "e2")]
        A = to_tensor(mvs[0], mask=full)
        B = to_tensor(mvs[1], mask=full)

        result = O["kij"] * A["i"] * B["j"]
        assert isinstance(result, MVLabeledTensor)
        assert result.labels == "k*"

    def test_mul_then_div(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("jk", [full, full])
        A.tensor.data[:] = 6.0
        B.tensor.data[:] = 2.0
        result = A["ij"] * A["ij"] / B["jk"]
        assert isinstance(result, MVLabeledTensor)


# ---------------------------------------------------------------------------
# 7.11 – Factory constructors (zeros)
# ---------------------------------------------------------------------------


class TestFactoryConstructors:
    def test_mvtensor_zeros(self, full):
        Z = MVTensor.zeros([full, 5])
        assert Z.shape == (len(full), 5)
        assert Z.masks[0] == full
        assert Z.masks[1] is None
        assert np.all(Z.data == 0)

    def test_mvtensor_zeros_bare_int(self):
        Z = MVTensor.zeros([3])
        assert Z.shape == (3,)
        assert Z.masks == (None,)
        assert np.all(Z.data == 0)

    def test_mvtensor_zeros_like(self, full):
        Z1 = MVTensor.zeros([full, 5])
        Z2 = MVTensor.zeros_like(Z1)
        assert Z2.shape == Z1.shape
        assert Z2.masks == Z1.masks

    def test_mvtensor_zeros_invalid_spec(self):
        with pytest.raises(TypeError):
            MVTensor.zeros([3.5])  # type: ignore[arg-type]

    def test_labeled_zeros(self, full):
        LZ = MVLabeledTensor.zeros("kij", [full, full, full])
        assert LZ.labels == "k*i*j*"
        assert LZ.shape == (len(full),) * 3

    def test_zeros_from_dict(self, full):
        LZ = MVLabeledTensor.zeros_from_dict("in", {"i": full, "n": 5})
        assert LZ.labels == "i*n*"
        assert LZ.shape == (len(full), 5)

    def test_zeros_from_dict_missing(self, full):
        with pytest.raises(ValueError):
            MVLabeledTensor.zeros_from_dict("in", {"i": full})


# ---------------------------------------------------------------------------
# 7.12 – __setitem__ assignment
# ---------------------------------------------------------------------------


class TestSetItem:
    def test_broadcast_assign(self, full):
        A = MVLabeledTensor.zeros("kij", [full, full, full])
        B = MVLabeledTensor.zeros("ji", [full, full])
        B.tensor.data[:] = np.arange(len(full) * len(full), dtype=np.float64).reshape(
            len(full), len(full)
        )
        A["kij"] = B["ji"]
        # B was broadcast along k axis
        for k_idx in range(len(full)):
            assert np.allclose(
                A.tensor.data[k_idx, :, :],
                np.arange(len(full) * len(full), dtype=np.float64).reshape(
                    len(full), len(full)
                ),
            )

    def test_direct_assign(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("ij", [full, full])
        B.tensor.data[:] = 42.0
        A["ij"] = B["ij"]
        assert np.allclose(A.tensor.data, 42.0)

    def test_plain_mvtensor_assign(self, full):
        A = MVLabeledTensor.zeros("kij", [full, full, full])
        T = MVTensor.zeros([full, full, full])
        T.data[:] = 7.0
        A["kij"] = T
        assert np.allclose(A.tensor.data, 7.0)

    def test_extra_labels_error(self, full):
        A = MVLabeledTensor.zeros("ij", [full, full])
        B = MVLabeledTensor.zeros("jk", [full, full])
        with pytest.raises(ValueError):
            A["ij"] = B["jk"]


# ---------------------------------------------------------------------------
# 7.13 – iter_labels
# ---------------------------------------------------------------------------


class TestIterLabels:
    def test_single_tensor(self, full):
        A = MVLabeledTensor.zeros("na", [5, full])
        slices = list(iter_labels("n", A))
        assert len(slices) == 5
        for sl in slices:
            assert isinstance(sl, MVLabeledTensor)
            assert sl.labels == "a*"
            assert sl.shape == (len(full),)

    def test_multiple_tensors(self, full):
        A = MVLabeledTensor.zeros("na", [5, full])
        B = MVLabeledTensor.zeros("nb", [5, 3])
        for idx, (a_sl, b_sl) in enumerate(iter_labels("n", A, B)):
            assert a_sl.labels == "a*"
            assert b_sl.labels == "b*"
        assert idx == 4  # 5 iterations, last idx is 4

    def test_mismatched_lengths(self, full):
        A = MVLabeledTensor.zeros("na", [5, full])
        B = MVLabeledTensor.zeros("nb", [3, full])
        with pytest.raises(ValueError):
            list(iter_labels("n", A, B))

    def test_missing_label(self, full):
        A = MVLabeledTensor.zeros("ia", [full, 5])
        with pytest.raises(ValueError):
            list(iter_labels("n", A))


# ---------------------------------------------------------------------------
# _build_subscript
# ---------------------------------------------------------------------------


class TestBuildSubscript:
    def test_gp_contraction(self, full):
        O = MVLabeledTensor.zeros("kij", [full, full, full])
        A = MVLabeledTensor.zeros("i", [full])
        B = MVLabeledTensor.zeros("j", [full])
        sub, out_raw, modes = _build_subscript(O, A, B)
        assert sub == "kij,i,j->k"
        assert out_raw == ["k"]
        assert modes == {"k": "*"}

    def test_batch_gp(self, full):
        O = MVLabeledTensor.zeros("kij", [full, full, full])
        A = MVLabeledTensor.zeros("i*n_", [full, 5])
        B = MVLabeledTensor.zeros("j*n_", [full, 5])
        sub, out_raw, modes = _build_subscript(O, A, B)
        assert sub == "kij,in,jn->kn"
        assert set(out_raw) == {"k", "n"}

    def test_element_wise(self, full):
        A = MVLabeledTensor.zeros("in_", [full, 5])
        B = MVLabeledTensor.zeros("jn_", [full, 5])
        sub, out_raw, modes = _build_subscript(A, B)
        assert sub == "in,jn->ijn"
        assert modes == {"i": "*", "j": "*", "n": "_"}