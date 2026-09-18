# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``Expression.compile`` / ``AffineExpression.compile``."""

from __future__ import annotations

import pytest

from pytanga import AffineExpression, BladeMask, DataArray, Expression, Variable
from pytanga.basis import BasisE3, BasisN3
from pytanga.expression._labels import _reset_allocator
from pytanga.geometry import Direction, Geometry, Motor, Rotor


def _close(a, b) -> bool:  # noqa: ANN001
    return (a - b).mag < 1e-12


class TestExpressionCompile:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_single_variable_matches_call(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        expr = v * self._mv({"e1": 2.0, "e2": 3.0})
        compiled = expr.compile()
        x = self._mv({"e1": 1.0, "e3": -1.0})
        assert _close(compiled(V1=x), expr(V1=x))

    def test_scalar_binding(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        expr = v * self._mv({"e1": 2.0})
        compiled = expr.compile()
        assert _close(compiled(V1=3), expr(V1=3))

    def test_constant_expression_zero_arg(self):  # noqa: ANN201
        expr = Expression(self._mv({"e12": 2.0}))
        compiled = expr.compile()
        assert _close(compiled(), expr())

    def test_missing_binding_raises(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        compiled = (v * w).compile()
        with pytest.raises(ValueError, match="missing"):
            compiled(V1=self._mv({"e1": 1.0}))

    def test_extra_binding_raises(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        compiled = (v * 1.0).compile()
        with pytest.raises(ValueError, match="extra"):
            compiled(V1=self._mv({"e1": 1.0}), V2=self._mv({"e2": 1.0}))

    def test_dataarray_binding_raises(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        compiled = (v * 1.0).compile()
        xs = DataArray([self._mv({"e1": 1.0})], masks=("n", self.full))
        with pytest.raises(TypeError, match="single MV or scalar"):
            compiled(V1=xs)

    def test_out_of_mask_raises(self):  # noqa: ANN201
        v = Variable("V1", BladeMask(self.alg, [1]))
        compiled = (v * 1.0).compile()
        with pytest.raises(ValueError, match="blades outside its mask"):
            compiled(V1=self._mv({"e2": 1.0}))


class TestAffineCompile:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_affine_matches_call(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        aff = AffineExpression([v * v, v * self._mv({"e1": 2.0})])
        compiled = aff.compile()
        x = self._mv({"e1": 1.0, "e2": 2.0})
        assert _close(compiled(V1=x), aff(V1=x))

    def test_affine_scalar_binding(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        aff = AffineExpression([v * v, v * self._mv({"e1": 2.0})])
        compiled = aff.compile()
        assert _close(compiled(V1=2), aff(V1=2))

    def test_affine_missing_raises(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        aff = AffineExpression([v * w, v * 1.0])
        compiled = aff.compile()
        with pytest.raises(ValueError, match="missing"):
            compiled(V1=self._mv({"e1": 1.0}))


def test_repeated_occurrence_sandwich_compiles() -> None:
    _reset_allocator()
    alg = BasisN3()
    geo = Geometry(alg)
    R = geo.create_var("R", Motor)
    X = Variable("X", geo.mask_for(Motor))
    expr = ~R * X * R

    r = geo(Rotor(0.3, Direction(0, 0, 1)))
    x = 1.0 * alg.e12 + 0.5 * alg.e13 + 0.2 * (alg.e1 ^ alg.einf)

    compiled = expr.compile()
    assert _close(compiled(R=r, X=x), expr(R=r, X=x))
