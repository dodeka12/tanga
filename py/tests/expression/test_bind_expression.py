# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for binding a variable to a sub-expression (composition)."""

import pytest

from pytanga import BladeMask, DataArray, Variable
from pytanga.basis import BasisE3
from pytanga.expression._expression import AffineExpression, Expression
from pytanga.expression._labels import _reset_allocator
from pytanga.geometry import Direction
from pytanga.geometry.create_e3 import create_rotor


def _close(a, b) -> bool:  # noqa: ANN001
    return (a - b).mag < 1e-12


class TestBindExpression:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.vec = BladeMask(self.alg, grades=[1])
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_bind_expression_composes_single_occurrence(self):  # noqa: ANN201
        a = Variable("a", self.full)
        b = Variable("b", self.full)
        e = a * b

        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        B = Variable("B", self.full)
        inner = R * B * ~R  # full-mask sandwich (matches b's full mask)

        result = e.bind(b=inner)
        assert isinstance(result, Expression)
        assert set(result.names) == {"a", "B"}
        assert len(result.names["B"]) == 1

        a_val = self._mv({"e1": 1.0, "e2": 2.0})
        b_val = self._mv({"e1": -1.0, "e3": 0.5})
        expected = a_val * (R * b_val * ~R)
        assert _close(result(a=a_val, B=b_val), expected)

    def test_bind_expression_mask_mismatch(self):  # noqa: ANN201
        v = Variable("v", self.vec)
        a = self._mv({"e1": 1.0})
        e = v * a

        inner = Expression(self._mv({"e12": 1.0}))  # bivector output, not vec
        with pytest.raises(ValueError):
            e.bind(v=inner)

    def test_bind_expression_constant_equals_mv_binding(self):  # noqa: ANN201
        v = Variable("v", self.vec)
        w = Variable("w", self.vec)
        e = v * w
        x = self._mv({"e1": 2.0})

        partial_mv = e.bind(w=x)
        partial_expr = e.bind(w=Expression(x, self.vec))
        assert isinstance(partial_expr, Expression)
        assert set(partial_expr.names) == {"v"}

        v_val = self._mv({"e2": 3.0})
        assert _close(partial_mv(v=v_val), partial_expr(v=v_val))

    def test_bind_expression_nested(self):  # noqa: ANN201
        a = Variable("a", self.full)
        b = Variable("b", self.full)
        e = a * b

        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        S = create_rotor(self.alg, 0.3, Direction(0, 1, 0))

        B1 = Variable("B1", self.full)
        r1 = e.bind(b=R * B1 * ~R)
        assert set(r1.names) == {"a", "B1"}

        B2 = Variable("B2", self.full)
        r2 = r1.bind(B1=S * B2 * ~S)
        assert set(r2.names) == {"a", "B2"}

        a_val = self._mv({"e1": 1.0, "e2": 2.0})
        b2_val = self._mv({"e1": -1.0, "e3": 0.5})
        expected = a_val * (R * (S * b2_val * ~S) * ~R)
        assert _close(r2(a=a_val, B2=b2_val), expected)

    def test_bind_expression_repeated_host_variable(self):  # noqa: ANN201
        v = Variable("v", self.full)
        e = v * v

        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        w = Variable("w", self.full)
        g = w * R

        result = e.bind(v=g)
        assert set(result.names) == {"w"}
        assert len(result.names["w"]) == 2

        x = self._mv({"e1": 1.0, "e2": 2.0})
        assert _close(result(w=x), (x * R) * (x * R))

    def test_bind_expression_repeated_inner_free_variable(self):  # noqa: ANN201
        v = Variable("v", self.full)
        e = v * 1.0

        w = Variable("w", self.full)
        g = w * w

        result = e.bind(v=g)
        assert set(result.names) == {"w"}
        assert len(result.names["w"]) == 2

        x = self._mv({"e1": 1.0, "e2": 2.0})
        assert _close(result(w=x), x * x)

    def test_bind_expression_both_repeated(self):  # noqa: ANN201
        v = Variable("v", self.full)
        e = v * v

        w = Variable("w", self.full)
        g = w * w

        result = e.bind(v=g)
        assert set(result.names) == {"w"}
        assert len(result.names["w"]) == 4

        x = self._mv({"e1": 1.0, "e2": 2.0})
        assert _close(result(w=x), (x * x) * (x * x))

    def test_bind_expression_shared_free_variable_dataarray(self):  # noqa: ANN201
        v = Variable("v", self.full)
        e = v * v

        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        w = Variable("w", self.full)
        result = e.bind(v=w * R)

        xs = [
            self._mv({"e1": 1.0, "e2": 2.0}),
            self._mv({"e2": 3.0, "e3": -1.0}),
        ]
        data = DataArray(xs, masks=("n", self.full))
        vals = result(w=data)
        assert isinstance(vals, list) and len(vals) == 2
        for x, val in zip(xs, vals):
            assert _close(val, (x * R) * (x * R))

    def test_bind_expression_affine(self):  # noqa: ANN201
        o1 = Variable("Omega_b", self.full)
        o2 = Variable("Omega_b", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        aff = o1 * a + o2 * b
        assert isinstance(aff, AffineExpression)

        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        Omega = Variable("Omega", self.full)
        inner = R * Omega * ~R

        result = aff.bind(Omega_b=inner)
        assert isinstance(result, AffineExpression)
        assert set(result.names) == {"Omega"}

        w = self._mv({"e1": 1.0, "e2": 4.0, "e3": 0.5})
        omega_val = R * w * ~R
        assert _close(result(Omega=w), omega_val * a + omega_val * b)

    def test_bind_expression_collision_with_remaining(self):  # noqa: ANN201
        x = Variable("x", self.full)
        y = Variable("y", self.full)
        e = x * y

        inner = x * self._mv({"e1": 1.0})  # free "x" collides with the kept x
        with pytest.raises(ValueError):
            e.bind(y=inner)

    def test_bind_expression_self_reference(self):  # noqa: ANN201
        y = Variable("y", self.full)
        e = y * 1.0

        inner = y * self._mv({"e1": 1.0})  # free "y" == the bound name
        with pytest.raises(ValueError):
            e.bind(y=inner)

    def test_bind_expression_duplicate_free_name(self):  # noqa: ANN201
        y = Variable("y", self.full)
        z = Variable("z", self.full)
        e = y * z

        inner_y = Variable("Omega", self.full) * self._mv({"e1": 1.0})
        inner_z = Variable("Omega", self.full) * self._mv({"e2": 2.0})
        with pytest.raises(ValueError):
            e.bind(y=inner_y, z=inner_z)

    def test_bind_expression_counting_axes_rejected(self):  # noqa: ANN201
        w = Variable("w", self.full)
        t = Variable("t", self.full)
        inner_base = w * t
        xs = [self._mv({"e1": 1.0}), self._mv({"e2": 2.0})]
        inner = inner_base(w=DataArray(xs, masks=("n", self.full)))
        assert inner._has_counting_axes()

        v = Variable("v", self.full)
        e = v * 1.0
        with pytest.raises(ValueError):
            e.bind(v=inner)

