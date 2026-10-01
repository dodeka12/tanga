# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``Algebra.compare`` / ``__eq__`` / ``__hash__`` (parameter equality)."""

from pytanga.algebra import Algebra
from pytanga.basis import BasisE3, BasisN3


def test_basis_equality() -> None:
    assert BasisN3() == BasisN3()
    assert BasisN3() != BasisE3()


def test_compare() -> None:
    assert BasisN3().compare(BasisN3())
    assert not BasisN3().compare(BasisE3())
    assert not BasisN3().compare("x")


def test_hash_matches_equality() -> None:
    a = BasisN3()
    b = BasisN3()
    assert a == b
    assert hash(a) == hash(b)


def test_modulus_included_in_equality() -> None:
    assert Algebra(3, 0, "int64") != Algebra(3, 0, "int64", modulus=7)
    assert Algebra(3, 0, "int64", modulus=7) == Algebra(3, 0, "int64", modulus=7)


def test_opns_excluded_from_equality() -> None:
    assert BasisN3(opns=True) == BasisN3(opns=False)


def test_mv_combine_across_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    result = a.multivector({1: 1.0}) + b.multivector({2: 2.0})
    expected = a.multivector({1: 1.0, 2: 2.0})
    assert result.to_dict() == expected.to_dict()
    assert result.algebra is a
