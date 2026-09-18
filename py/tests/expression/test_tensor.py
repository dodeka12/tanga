# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``Expression.get_tensor`` / ``AffineExpression.get_tensor`` / ``MVTensor.get_array``."""

from __future__ import annotations

import numpy as np
import pytest

from pytanga import AffineExpression, BladeMask, DataArray, Variable
from pytanga.basis import BasisN3
from pytanga.matrix.convert import to_matrix
from pytanga.tensor import MVTensor


def _twist(alg: BasisN3) -> BladeMask:
    return BladeMask(alg, [3, 5, 6, 9, 10, 12, 17, 18, 20]).with_basis(
        [
            ("e12", alg.e12),
            ("e13", alg.e13),
            ("e23", alg.e23),
            ("e1∧einf", alg.e1.op(alg.einf)),
            ("e2∧einf", alg.e2.op(alg.einf)),
            ("e3∧einf", alg.e3.op(alg.einf)),
        ]
    )


def test_expression_get_tensor_returns_mvtensor() -> None:
    alg = BasisN3()
    x = Variable("X", _twist(alg))
    expr = x * 1.0
    tensor = expr.get_tensor()
    assert isinstance(tensor, MVTensor)
    assert tensor.shape == (9, 9)  # raw output (9) × raw variable (9)


def test_get_array_default() -> None:
    alg = BasisN3()
    x = Variable("X", _twist(alg))
    expr = x * 1.0
    arr = expr.get_tensor().get_array()
    # output uses the auto display basis (9), variable uses the twist basis (6)
    assert arr.shape == (9, 6)


def test_get_array_out_basis_identity() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    expr = x * 1.0
    arr = expr.get_tensor().get_array(out_basis=twist.basis_vectors)
    assert arr.shape == (6, 6)
    assert np.allclose(arr, np.eye(6))


def test_affine_get_tensor_raw_and_array() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    aff = AffineExpression([x * alg.e12, x * alg.e13])

    tensor = aff.get_tensor()
    assert isinstance(tensor, MVTensor)
    assert tensor.shape == (len(aff.out_mask), len(twist))

    _name, var_mask, raw = aff._variable_matrix()
    assert np.allclose(tensor.data, raw)

    out_mask = aff.out_mask
    c_out = np.linalg.pinv(to_matrix(out_mask.basis_vectors, mask=out_mask).data)
    b_var = to_matrix(var_mask.basis_vectors, mask=var_mask).data
    expected = c_out @ raw @ b_var
    assert np.allclose(tensor.get_array(), expected)


def test_affine_multilinear_get_tensor_shape() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    aff = AffineExpression([x * x, (x * alg.e1) * x])

    tensor = aff.get_tensor()
    assert isinstance(tensor, MVTensor)
    assert tensor.shape == (len(aff.out_mask), len(twist), len(twist))


def test_affine_multilinear_einsum_equivalence() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    aff = AffineExpression([x * x, (x * alg.e1) * x])

    raw = aff.get_tensor().data
    omega = 0.3 * alg.e12 + 0.1 * alg.e13 - 0.2 * alg.e23 + 0.05 * (alg.e1 ^ alg.einf)
    c = np.asarray(to_matrix(omega, mask=twist).data, dtype=np.float64).ravel()
    predicted = np.einsum("ijk,j,k->i", raw, c, c)

    actual = aff(X=omega)
    actual_raw = np.asarray(
        to_matrix(actual, mask=aff.out_mask).data, dtype=np.float64
    ).ravel()
    assert np.allclose(predicted, actual_raw)


def test_expression_get_tensor_repeated_occurrence_rank() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    expr = x * x
    tensor = expr.get_tensor()
    assert tensor.shape == (len(expr.out_mask), len(twist), len(twist))


def test_affine_multilinear_inconsistent_occurrences_raises() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    aff = AffineExpression([x * x, x * 1.0])
    with pytest.raises(ValueError, match="same number of times"):
        aff.get_tensor()


def test_affine_get_tensor_rejects_counting_axes() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)
    w = Variable("W", twist)
    xs = [alg.e12, alg.e13]
    partial = (x * w)(X=DataArray(xs, masks=("n", twist)))
    aff = AffineExpression([partial])
    with pytest.raises(ValueError, match="counting axes"):
        aff.get_tensor()

