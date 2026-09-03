# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for AffineExpression (sums of non-mergeable expressions)."""

import pytest

from pytanga import AffineExpression, BladeMask, DataArray, Expression, Variable
from pytanga.basis import BasisE3
from pytanga.expression._labels import _reset_allocator


def _close(a, b) -> bool:
    return (a - b).mag < 1e-12


class TestAffineExpression:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_sum_of_different_degree(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        assert isinstance(a, AffineExpression)
        assert len(a.terms) == 2
        x = self._mv({"e1": 2.0})
        y = self._mv({"e2": 3.0})
        assert _close(a(V1=x, V2=y), (x * x) + y)

    def test_sum_with_constant(self):
        v = Variable("V1", self.full)
        c = self._mv({"e1": 2.0})
        a = v + c
        assert isinstance(a, AffineExpression)
        x = self._mv({"e1": 1.0, "e2": 1.0})
        assert _close(a(V1=x), x + c)

    def test_difference_with_constant(self):
        v = Variable("V1", self.full)
        c = self._mv({"e1": 2.0})
        a = v - c
        x = self._mv({"e1": 1.0})
        assert _close(a(V1=x), x - c)

    def test_merge_still_happens(self):
        v = Variable("V1", self.full)
        a = v * self._mv({"e1": 2.0})
        b = v * self._mv({"e2": 3.0})
        s = a + b  # same variable -> merges into a single Expression
        assert isinstance(s, Expression)
        assert not isinstance(s, AffineExpression)
        x = self._mv({"e1": 1.0})
        assert _close(
            s(V1=x),
            (x * self._mv({"e1": 2.0})) + (x * self._mv({"e2": 3.0})),
        )

    def test_partial_single(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        x = self._mv({"e1": 2.0})
        partial = a(V1=x)
        assert isinstance(partial, AffineExpression)
        y = self._mv({"e2": 3.0})
        assert _close(partial(V2=y), (x * x) + y)

    def test_partial_batch(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        result = a(V1=DataArray(xs, masks=("n", self.full)))
        assert isinstance(result, list) and len(result) == 2
        assert all(isinstance(t, AffineExpression) for t in result)
        y = self._mv({"e2": 3.0})
        for t, x in zip(result, xs):
            assert _close(t(V2=y), (x * x) + y)

    def test_full_batch(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        y = self._mv({"e2": 3.0})
        result = a(V1=DataArray(xs, masks=("n", self.full)), V2=y)
        assert isinstance(result, list) and len(result) == 2
        for r, x in zip(result, xs):
            assert _close(r, (x * x) + y)

    def test_distribute_product(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        b = a * self._mv({"e1": 2.0})
        assert isinstance(b, AffineExpression)
        x = self._mv({"e1": 1.0})
        y = self._mv({"e2": 1.0})
        assert _close(b(V1=x, V2=y), ((x * x) + y) * self._mv({"e1": 2.0}))

    def test_affine_times_affine(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        b = v + w
        prod = a * b  # 2 x 2 -> 4 terms
        assert isinstance(prod, AffineExpression)
        assert len(prod.terms) == 4
        x = self._mv({"e1": 1.0})
        y = self._mv({"e2": 1.0})
        assert _close(prod(V1=x, V2=y), ((x * x) + y) * (x + y))

    def test_involutions_and_scale(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        assert isinstance(~a, AffineExpression)
        assert isinstance(2.0 * a, AffineExpression)
        assert isinstance(-a, AffineExpression)
        x = self._mv({"e1": 1.0})
        y = self._mv({"e2": 1.0})
        assert _close((-a)(V1=x, V2=y), -((x * x) + y))

    def test_inv_raises(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        with pytest.raises(ValueError):
            a.inv("V3")

    def test_unknown_variable(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = (v * v) + w
        with pytest.raises(ValueError):
            a(V3=self._mv({"e1": 1.0}))

    def test_out_mask_is_union(self):
        v = Variable("V1", self.full)
        w = Variable("V2", BladeMask(self.alg, [1]))  # only e1
        a = (v * v) + w
        assert len(a.out_mask) == 8  # full E3 mask

    def test_mixed_mask_union_check(self):
        # The same variable name bound with different masks in two terms: a
        # binding is valid iff its blades lie within the union of those masks.
        v1 = Variable("V1", BladeMask(self.alg, [1]))  # e1 only
        v2 = Variable("V1", BladeMask(self.alg, [2]))  # e2 only
        e1 = self._mv({"e1": 1.0})
        e2 = self._mv({"e2": 1.0})
        a = (v1 * e1) + (v2 * e2)
        # e1 + e2 is within the union [e1, e2]; each term uses its own mask.
        assert _close(a(V1=e1 + e2), (e1 * e1) + (e2 * e2))
        # a blade outside the union raises
        with pytest.raises(ValueError):
            a(V1=e1 + e2 + self._mv({"e3": 1.0}))
