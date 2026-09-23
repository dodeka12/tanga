# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the ``linear_map`` factory and single-variable positional apply."""

import numpy as np
import pytest

from pytanga.algebra import Algebra
from pytanga.blade_mask import BladeMask
from pytanga.expression import Variable, linear_map


def test_linear_map_applies_matrix() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])  # e1, e2, e3
    # cyclic permutation of the three blades
    M = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
    expr = linear_map(M, mask, "c", mask)
    mv = alg.multivector({1: 2.0, 2: 3.0, 4: 5.0})
    out = expr(c=mv)
    assert out[1] == pytest.approx(3.0)
    assert out[2] == pytest.approx(5.0)
    assert out[4] == pytest.approx(2.0)


def test_linear_map_positional_apply() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])
    expr = linear_map(np.eye(3), mask, "c", mask)
    mv = alg.multivector({1: 2.0, 4: 5.0})
    out = expr(mv)  # positional apply on a single-variable expression
    assert out[1] == pytest.approx(2.0)
    assert out[4] == pytest.approx(5.0)


def test_linear_map_evaluate_positional() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])
    expr = linear_map(np.eye(3), mask, "c", mask)
    mv = alg.multivector({2: 7.0})
    out = expr.evaluate(mv)
    assert out[2] == pytest.approx(7.0)


def test_linear_map_rejects_bad_shape() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])
    with pytest.raises(ValueError):
        linear_map(np.eye(2), mask, "c", mask)


def test_positional_requires_single_variable() -> None:
    alg = Algebra(3, 0)
    full = BladeMask.full(alg)
    v = Variable("V1", full)
    w = Variable("V2", full)
    expr = v * w  # two variables
    with pytest.raises(TypeError):
        expr(alg.multivector({0: 1.0}))


def test_positional_conflicts_with_keyword() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])
    expr = linear_map(np.eye(3), mask, "c", mask)
    mv = alg.multivector({1: 2.0})
    with pytest.raises(TypeError):
        expr(mv, c=mv)


def test_matmul_applies_single_variable_expression() -> None:
    alg = Algebra(3, 0)
    mask = BladeMask(alg, [1, 2, 4])
    expr = linear_map(np.eye(3), mask, "c", mask)
    mv = alg.multivector({1: 2.0, 4: 5.0})
    out = expr @ mv  # matmul == evaluate
    assert out[1] == pytest.approx(2.0)
    assert out[4] == pytest.approx(5.0)


def test_matmul_requires_single_variable() -> None:
    alg = Algebra(3, 0)
    full = BladeMask.full(alg)
    expr = Variable("V1", full) * Variable("V2", full)  # two variables
    with pytest.raises(TypeError):
        expr @ alg.multivector({0: 1.0})
