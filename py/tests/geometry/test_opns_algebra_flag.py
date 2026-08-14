# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 1 tests — mutable ``opns`` flag on Algebra, MV, and Basis classes."""

from __future__ import annotations

import pytest

from pytanga.algebra._algebra import Algebra
from pytanga.basis import (
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
)

ALL_BASES = [
    BasisE2,
    BasisE3,
    BasisP2,
    BasisP3,
    BasisN2,
    BasisN3,
    BasisPGA2,
    BasisPGA3,
]


def test_algebra_default_opns_is_true():
    assert Algebra(2, 0).opns is True


def test_algebra_opns_false():
    assert Algebra(2, 0, opns=False).opns is False


@pytest.mark.parametrize("basis_cls", ALL_BASES)
def test_basis_default_opns_is_true(basis_cls):
    assert basis_cls().opns is True


@pytest.mark.parametrize("basis_cls", ALL_BASES)
def test_basis_opns_false(basis_cls):
    alg = basis_cls(opns=False)
    assert alg.opns is False


@pytest.mark.parametrize("basis_cls", ALL_BASES)
def test_basis_opns_mutation(basis_cls):
    alg = basis_cls()
    alg.opns = False
    assert alg.opns is False
    alg.opns = True
    assert alg.opns is True


def test_mv_observes_algebra_opns():
    alg = BasisE3()
    mv = alg.multivector({1: 1})
    assert mv.opns is True

    alg.opns = False
    assert mv.opns is False
    assert mv.algebra.opns is False


def test_flag_is_per_algebra_not_global():
    a = BasisE3(opns=True)
    b = BasisE3(opns=False)
    assert a.opns is True
    assert b.opns is False

    # mutating one does not affect the other
    a.opns = False
    assert a.opns is False
    assert b.opns is False
    b.opns = True
    assert b.opns is True
    assert a.opns is False