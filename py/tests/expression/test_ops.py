# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the named GA product functions/methods on the expression system."""

import pytest

from pytanga import Algebra, BladeMask, DataArray, MV
from pytanga.basis import BasisE3
from pytanga.expression import (
    AffineExpression,
    ScalarExpression,
    acp,
    cp,
    gp,
    ip,
    nvp,
    op,
    rc,
    sp,
    vp,
)
from pytanga.expression._expression import Expression
from pytanga.expression._labels import _reset_allocator
from pytanga.expression._variable import Variable


def _close(a, b) -> bool:  # noqa: ANN001
    return (a - b).mag < 1e-12


class TestNamedProducts:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_gp_ip_op_named(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(v.gp(a)(V1=x), x * a)
        assert _close(v.ip(a)(V1=x), x | a)
        assert _close(v.op(a)(V1=x), x ^ a)
        assert _close(gp(v, a)(V1=x), x * a)
        assert _close(ip(v, a)(V1=x), x | a)
        assert _close(op(v, a)(V1=x), x ^ a)

    def test_gp_scalar_scale(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = (v * a).gp(2.0)
        x = self._mv({"e1": 3.0})
        assert _close(e(V1=x), 2.0 * (x * a))
        # AffineExpression.gp with a scalar scales the sum.
        w = Variable("V2", self.full)
        aff = v * a + w * a
        scaled = aff.gp(2.0)
        y = self._mv({"e2": 1.0})
        assert _close(scaled(V1=x, V2=y), 2.0 * (x * a + y * a))

    def test_const_const(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0, "e12": 3.0})
        b = self._mv({"e2": 1.0, "e3": -1.0})
        assert _close(gp(a, b), a * b)
        assert _close(ip(a, b), a | b)
        assert _close(op(a, b), a ^ b)
        assert _close(vp(a, b), a.vp(b))
        assert _close(nvp(a, b), a.nvp(b))
        assert _close(cp(a, b), a.cp(b))
        assert _close(acp(a, b), a.acp(b))
        assert _close(rc(a, b), a.rc(b))

    def test_vp_variable_versor(self):  # noqa: ANN201
        r = Variable("R", self.full)
        x = Variable("X", self.full)
        e = r.vp(x)
        assert set(e.names) == {"R", "X"}
        rr = self._mv({"e12": 1.0})
        xx = self._mv({"e1": 2.0, "e2": 3.0})
        assert _close(e(R=rr, X=xx), rr.vp(xx))

    def test_vp_constant_versor(self):  # noqa: ANN201
        a = self._mv({"e12": 1.0})
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e2": 3.0})
        assert _close(a.vp(v)(V1=x), a.vp(x))

    def test_nvp_constant_versor(self):  # noqa: ANN201
        a = self._mv({"e12": 1.0})
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e2": 3.0})
        assert _close(a.nvp(v)(V1=x), a.nvp(x))

    def test_nvp_symbolic_versor_raises(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        with pytest.raises(ValueError):
            v.nvp(a)

    def test_sp_const_returns_scalar(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0, "e12": 3.0})
        b = self._mv({"e1": 1.0, "e2": 4.0})
        result = sp(a, b)
        assert isinstance(result, float)
        assert result == pytest.approx(a.sp(b))

    def test_sp_symbolic_returns_float_when_bound(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        s = v.sp(a)
        assert isinstance(s, ScalarExpression)
        x = self._mv({"e1": 1.0, "e2": 4.0})
        result = s(V1=x)
        assert isinstance(result, float)
        assert result == pytest.approx(x.sp(a))

    def test_sp_mv_caller_variable_param(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0, "e12": 3.0})
        v = Variable("V1", self.full)
        x = self._mv({"e1": 1.0, "e2": 4.0})
        s = a.sp(v)
        assert isinstance(s, ScalarExpression)
        assert s(V1=x) == pytest.approx(a.sp(x))

    def test_sp_batched(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        s = v.sp(a)
        result = s(V1=DataArray(xs, masks=("n", self.full)))
        assert isinstance(result, list) and len(result) == 2
        for r, x in zip(result, xs):
            assert isinstance(r, float)
            assert r == pytest.approx(x.sp(a))

    def test_sp_int_dtype(self):  # noqa: ANN201
        alg = Algebra(3, 0, "int64")
        full = BladeMask.full(alg)
        a = alg.multivector({1: 2, 2: 3})
        b = alg.multivector({1: 4, 2: 5})
        assert sp(a, b) == a.sp(b)
        v = Variable("V1", full)
        s = v.sp(a)
        assert s(V1=b) == b.sp(a)

    def test_cp_acp_variable(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(v.cp(a)(V1=x), x.cp(a))
        assert _close(v.acp(a)(V1=x), x.acp(a))

    def test_cp_two_variables_is_affine(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = cp(v, w)
        assert isinstance(e, AffineExpression)
        x = self._mv({"e1": 1.0})
        y = self._mv({"e2": 3.0})
        assert _close(e(V1=x, V2=y), x.cp(y))

    def test_rc_variable(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(v.rc(a)(V1=x), x.rc(a))
        assert _close(a.rc(v)(V1=x), a.rc(x))

    def test_rc_grade_filter(self):  # noqa: ANN201
        # rc(vector, bivector) vanishes (grade(A) < grade(B)).
        v = Variable("V1", self.full)
        b = self._mv({"e12": 1.0})
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(v.rc(b)(V1=x), x.rc(b))
        assert _close(b.rc(v)(V1=x), b.rc(x))

    def test_mv_caller_all_products(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0, "e12": 3.0})
        v = Variable("V1", self.full)
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(a.gp(v)(V1=x), a * x)
        assert _close(a.ip(v)(V1=x), a | x)
        assert _close(a.op(v)(V1=x), a ^ x)
        assert _close(a.cp(v)(V1=x), a.cp(x))
        assert _close(a.acp(v)(V1=x), a.acp(x))
        assert _close(a.rc(v)(V1=x), a.rc(x))

    def test_expression_caller_methods(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = v * a  # Expression
        x = self._mv({"e1": 1.0, "e2": 4.0})
        b = self._mv({"e1": 3.0, "e12": 2.0})
        assert _close(e.gp(b)(V1=x), (x * a) * b)
        assert _close(e.ip(b)(V1=x), (x * a) | b)
        assert _close(e.op(b)(V1=x), (x * a) ^ b)
        assert _close(e.cp(b)(V1=x), (x * a).cp(b))
        assert _close(e.rc(b)(V1=x), (x * a).rc(b))

    def test_affine_distribution(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w + w * v  # AffineExpression
        assert isinstance(e, AffineExpression)
        b = self._mv({"e1": 1.0})
        x = self._mv({"e1": 2.0})
        y = self._mv({"e2": 3.0})
        prod = e.gp(b)
        assert isinstance(prod, AffineExpression)
        assert _close(prod(V1=x, V2=y), (x * y + y * x) * b)

    def test_sp_partial_bind_returns_scalar_expression(self):  # noqa: ANN201
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        s = v.sp(w)
        assert isinstance(s, ScalarExpression)
        x = self._mv({"e1": 2.0})
        partial = s.bind(V1=x)
        assert isinstance(partial, ScalarExpression)
        y = self._mv({"e2": 3.0})
        assert partial(V2=y) == pytest.approx(x.sp(y))
