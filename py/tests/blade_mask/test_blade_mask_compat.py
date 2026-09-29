# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cross-instance compatibility for ``BladeMask`` (equal-parameter algebras)."""

import pytest

from pytanga import BladeMask
from pytanga.basis import BasisE3, BasisN3


def test_union_across_equal_parameter_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    mask_a = BladeMask(a, [1, 2])
    mask_b = BladeMask(b, [2, 4])
    assert mask_a.union(mask_b).ids == [1, 2, 4]


def test_intersection_across_equal_parameter_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    mask_a = BladeMask(a, [1, 2])
    mask_b = BladeMask(b, [2, 4])
    assert mask_a.intersection(mask_b).ids == [2]


def test_from_array_across_equal_parameter_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    mask = BladeMask.from_array(
        [a.multivector({1: 1.0}), b.multivector({2: 2.0})]
    )
    assert mask.ids == [1, 2]


def test_eq_across_equal_parameter_instances() -> None:
    a = BasisN3()
    b = BasisN3()
    assert a is not b
    mask_a = BladeMask(a, [1, 2])
    mask_b = BladeMask(b, [1, 2])
    assert mask_a == mask_b


def test_different_algebra_still_raises() -> None:
    mask_n3 = BladeMask(BasisN3(), [1])
    mask_e3 = BladeMask(BasisE3(), [1])
    with pytest.raises(AssertionError):
        mask_n3.union(mask_e3)
    with pytest.raises(AssertionError):
        mask_n3.intersection(mask_e3)
