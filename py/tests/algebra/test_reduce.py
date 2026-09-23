# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the sequence GA products (``op`` / ``join`` / ``meet`` / ``gp``)."""

import pytest

from pytanga.algebra import Algebra, gp, join, meet, op


def _basis() -> Algebra:
    return Algebra(3, 0)


def test_empty_raises() -> None:
    for fn in (op, join, meet, gp):
        with pytest.raises(ValueError):
            fn([])


def test_single_passthrough() -> None:
    alg = _basis()
    e1 = alg.multivector({1: 2.0})
    for fn in (op, join, meet, gp):
        assert fn([e1])[1] == pytest.approx(2.0)


def test_matches_binary_chain() -> None:
    alg = _basis()
    e1 = alg.multivector({1: 1.0})
    e2 = alg.multivector({2: 1.0})
    e3 = alg.multivector({4: 1.0})

    # e1 ^ e2 ^ e3 == e1 * e2 * e3 == the pseudoscalar e123 (blade id 7).
    assert op([e1, e2, e3])[7] == pytest.approx(1.0)
    assert gp([e1, e2, e3])[7] == pytest.approx(1.0)

    assert (join([e1, e2, e3]) - e1.join(e2).join(e3)).is_zero
    assert (meet([e1, e2]) - e1.meet(e2)).is_zero
