#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

r"""quadratic_get_tensor.py — multilinear AffineExpression.get_tensor().

Builds a quadratic (bilinear) operator in a twist variable ``X`` — the sum
``X * X + (X * e1) * X`` — and extracts its fixed rank-3 tensor once with
``AffineExpression.get_tensor()``.  Contracting that tensor with a concrete
twist coefficient vector via ``np.einsum("ijk,j,k->i", Q, c, c)`` reproduces the
live ``aff(X=omega)`` evaluation, so the operator can be precomputed once and
evaluated cheaply many times.

Run with:  uv run python py/examples/ga/expression/quadratic_get_tensor.py

Keywords: expressions, get_tensor, get_array, multilinear, quadratic, einsum, N3
"""

import numpy as np

from pytanga import AffineExpression, BladeMask, Variable
from pytanga.basis import BasisN3
from pytanga.matrix.convert import to_matrix


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


def main() -> None:
    alg = BasisN3()
    twist = _twist(alg)
    x = Variable("X", twist)

    aff = AffineExpression([x * x, (x * alg.e1) * x])

    # Rank-3 tensor: output axis + one axis per occurrence of X.
    tensor = aff.get_tensor()
    print("raw tensor shape (out, X, X):", tensor.shape)

    # Same tensor recombined into the named twist basis on the variable axes.
    named = tensor.get_array(axis_bases={1: twist.basis_vectors, 2: twist.basis_vectors})
    print("named tensor shape (out display, 6 DOF, 6 DOF):", named.shape)

    # Contract the fixed tensor against a concrete twist and compare to the live
    # evaluation of the expression.
    omega = 0.3 * alg.e12 + 0.1 * alg.e13 - 0.2 * alg.e23 + 0.05 * (alg.e1 ^ alg.einf)
    c = np.asarray(to_matrix(omega, mask=twist).data, dtype=np.float64).ravel()
    predicted = np.einsum("ijk,j,k->i", tensor.data, c, c)
    actual = np.asarray(
        to_matrix(aff.evaluate(X=omega), mask=aff.out_mask).data, dtype=np.float64
    ).ravel()
    print("einsum(Q, c, c) == aff(X=omega):", np.allclose(predicted, actual))


if __name__ == "__main__":
    main()
