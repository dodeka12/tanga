# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the branch-free ``MV`` operator dispatch (private ``_*_impl``)."""

from pytanga.basis import BasisE3


def test_add_sub_scale() -> None:
    alg = BasisE3()
    e1 = alg.multivector({1: 1.0})
    e2 = alg.multivector({2: 1.0})
    assert (e1 + e2)["e1"] == 1.0
    assert (e1 + e2)["e2"] == 1.0
    assert (e1 - e2)["e1"] == 1.0
    assert (e1 - e2)["e2"] == -1.0
    assert (3.0 * e1)["e1"] == 3.0


def test_products() -> None:
    alg = BasisE3()
    e1 = alg.multivector({1: 1.0})
    e2 = alg.multivector({2: 1.0})
    assert (e1 * e2)["e12"] == 1.0
    assert (e1 ^ e2)["e12"] == 1.0
    assert (e1 | e2)["s"] == 0.0
    assert (e1 | e1)["s"] == 1.0


def test_named_gp_op_ip() -> None:
    alg = BasisE3()
    e1 = alg.multivector({1: 1.0})
    e2 = alg.multivector({2: 1.0})
    assert e1.gp(e2)["e12"] == 1.0
    assert e1.op(e2)["e12"] == 1.0
    assert e1.ip(e1)["s"] == 1.0


def test_scalar_add_and_div() -> None:
    alg = BasisE3()
    e1 = alg.multivector({1: 1.0})
    assert (e1 + 2.0)["s"] == 2.0
    assert (e1 + 2.0)["e1"] == 1.0
    assert (e1 / 2.0)["e1"] == 0.5
