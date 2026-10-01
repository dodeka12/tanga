# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cross-instance compatibility for tensor/solver/matrix (equal-parameter algebras)."""

import numpy as np
import pytest

from pytanga import Algebra, BladeMask, MVProductMatrix, MVTensor
from pytanga.algebra import EProduct
from pytanga.basis import BasisE3, BasisN3
from pytanga.solver.solve import solve_mod
from pytanga.tensor.ops import contract
from pytanga.tensor.product import product_tensor, product_tensor_rc


def test_product_tensor_across_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    a_mask = BladeMask(a, grades=[1])
    b_mask = BladeMask(b, grades=[1])
    T = product_tensor(a_mask, b_mask, product=EProduct.GP)
    assert isinstance(T, MVTensor)


def test_product_tensor_rc_across_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    a_mask = BladeMask(a, grades=[1])
    b_mask = BladeMask(b, grades=[1])
    T = product_tensor_rc(a_mask, b_mask)
    assert isinstance(T, MVTensor)


def test_contract_across_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    mask_a = BladeMask(a, grades=[1])
    mask_b = BladeMask(b, grades=[1])
    A = MVTensor(data=np.arange(len(mask_a), dtype=float), masks=(mask_a,))
    B = MVTensor(data=np.arange(len(mask_b), dtype=float), masks=(mask_b,))
    C = contract("i,i->i", A, B)
    assert isinstance(C, MVTensor)


def test_mv_product_matrix_across_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    a_mask = BladeMask(a, [1, 2])
    b_mask = BladeMask(b, [1, 2])
    c_mask = BladeMask(a, [0, 3])
    M = MVProductMatrix(
        data=np.zeros((2, 2, 2)),
        a_mask=a_mask,
        b_mask=b_mask,
        c_mask=c_mask,
        product=EProduct.GP,
        left=True,
    )
    assert M.algebra == a


def test_solve_mod_across_instances() -> None:
    a_alg = Algebra(3, 0, "int64")
    b_alg = Algebra(3, 0, "int64")
    a = a_alg("e12")
    c = b_alg.multivector({0: 1})
    x = solve_mod(a, c, 97)
    assert x.to_dict() == a_alg.inv(a, 97).to_dict()


def test_different_algebra_still_raises() -> None:
    n3 = BasisN3()
    e3 = BasisE3()
    n3_mask = BladeMask(n3, grades=[1])
    e3_mask = BladeMask(e3, grades=[1])
    with pytest.raises(AssertionError):
        product_tensor(n3_mask, e3_mask, product=EProduct.GP)
