# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Cross-instance compatibility for ``Expression`` (equal-parameter algebras)."""

import pytest

from pytanga import BladeMask
from pytanga.basis import BasisE3, BasisN3
from pytanga.expression import Expression
from pytanga.expression._expression import AffineExpression
from pytanga.expression._labels import _reset_allocator
from pytanga.expression._variable import Variable


def test_product_across_instances() -> None:
    _reset_allocator()
    a = BasisN3()
    b = BasisN3()
    v1 = Variable("V1", BladeMask(a, grades=[1]))
    v2 = Variable("V2", BladeMask(b, grades=[1]))
    assert isinstance(v1 * v2, Expression)


def test_add_across_instances() -> None:
    _reset_allocator()
    a = BasisN3()
    b = BasisN3()
    v1 = Variable("V1", BladeMask(a, grades=[1]))
    v2 = Variable("V2", BladeMask(b, grades=[1]))
    assert isinstance(v1 + v2, (Expression, AffineExpression))


def test_project_onto_across_instances() -> None:
    _reset_allocator()
    a = BasisN3()
    b = BasisN3()
    expr = Variable("V1", BladeMask(a, grades=[1])) * 1.0
    target = BladeMask(b, grades=[1])
    assert isinstance(expr.project_onto(target), Expression)


def test_different_algebra_product_raises() -> None:
    _reset_allocator()
    a = BasisN3()
    e3 = BasisE3()
    v1 = Variable("V1", BladeMask(a, grades=[1]))
    v2 = Variable("V2", BladeMask(e3, grades=[1]))
    with pytest.raises(ValueError, match="different algebras"):
        v1 * v2


def test_different_algebra_project_onto_raises() -> None:
    _reset_allocator()
    a = BasisN3()
    e3 = BasisE3()
    expr = Variable("V1", BladeMask(a, grades=[1])) * 1.0
    target = BladeMask(e3, grades=[1])
    with pytest.raises(ValueError, match="different algebra"):
        expr.project_onto(target)
