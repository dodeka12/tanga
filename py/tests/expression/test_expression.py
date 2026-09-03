# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Expression class and the tensor product builder."""

import pytest

from pytanga import BladeMask, DataArray
from pytanga.basis import BasisE3, BasisN3
from pytanga.geometry import Direction, Geometry, Motor, Point, Rotor, Translator
from pytanga.geometry.create_e3 import create_rotor
from pytanga.expression._expression import AffineExpression, Expression
from pytanga.expression._labels import _reset_allocator
from pytanga.expression._variable import Variable
from pytanga.tensor._labeled import _axis_modes, _axis_names


def _close(a, b) -> bool:
    return (a - b).mag < 1e-12


class TestExpression:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_gp_variable_times_const(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e2": 3.0})
        e = v * a
        x = self._mv({"e1": 1.0, "e3": -1.0})
        assert isinstance(e, Expression)
        assert _close(e(V1=x), x * a)

    def test_gp_const_times_variable(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = a * v
        x = self._mv({"e1": 1.0, "e2": 5.0})
        assert _close(e(V1=x), a * x)

    def test_ip_and_op(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e12": 3.0})
        x = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close((v | a)(V1=x), x | a)
        assert _close((v ^ a)(V1=x), x ^ a)

    def test_two_variables(self):
        v1 = Variable("V1", self.full)
        v2 = Variable("V2", self.full)
        e = v1 * v2
        x = self._mv({"e1": 2.0})
        y = self._mv({"e2": 3.0})
        assert _close(e(V1=x, V2=y), x * y)

    def test_constant_folding(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e1 = v * a * b
        e2 = v * (a * b)
        x = self._mv({"e3": 1.0, "e1": -2.0})
        assert _close(e1(V1=x), e2(V1=x))

    def test_scalar_scale(self):
        v = Variable("V1", self.full)
        e = 2.0 * (v * self._mv({"e1": 3.0}))
        x = self._mv({"e1": 1.0})
        assert _close(e(V1=x), 2.0 * (x * self._mv({"e1": 3.0})))

    def test_tensor_property(self):
        v = Variable("V1", self.full)
        e = v * self._mv({"e1": 2.0})
        t = e.tensor
        assert t.ndim == 2
        assert t.labels[0].name == "k"
        assert t.labels[1].name == v.label
        assert e.names == {"V1": (v.label,)}
        assert e.masks["V1"] is v.mask

    def test_unknown_binding_and_empty_call(self):
        v = Variable("V1", self.full)
        e = v * self._mv({"e1": 2.0})
        x = self._mv({"e1": 1.0})
        with pytest.raises(ValueError):
            e(V2=x)
        assert e() is e  # no bindings -> self (partial, no-op)

    def test_value_outside_mask(self):
        mask = BladeMask(self.alg, [1])  # only e1
        v = Variable("V1", mask)
        e = v * self._mv({"e1": 2.0})
        x = self._mv({"e1": 1.0, "e2": 3.0})
        with pytest.raises(ValueError):
            e(V1=x)

    def test_quadratic(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e2": 3.0})
        e = v * v
        assert _close(e(V1=x), x * x)

    def test_no_aliasing(self):
        v = Variable("V1", self.full)
        e = v * self._mv({"e1": 2.0})
        x = self._mv({"e1": 1.0})
        r1 = e(V1=x)
        r2 = e(V1=x)
        assert r1 is not r2
        assert r1.to_dict() == r2.to_dict()

    def test_mismatched_algebra(self):
        v = Variable("V1", self.full)
        other = BasisN3().multivector({1: 1.0})
        with pytest.raises(ValueError):
            v * other


class TestAddition:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_distributive_add(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e1 = v * a + v * b
        e2 = v * (a + b)
        x = self._mv({"e1": 1.0, "e3": -1.0})
        assert _close(e1(V1=x), e2(V1=x))

    def test_add_constant_is_affine(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        c = self._mv({"e2": 5.0})
        e = v * a + c
        assert isinstance(e, AffineExpression)
        x = self._mv({"e1": 1.0})
        assert _close(e(V1=x), (x * a) + c)

    def test_zero_add(self):
        v = Variable("V1", self.full)
        e = v * self._mv({"e1": 2.0})
        assert e + 0 is e
        assert 0 + e is e
        x = self._mv({"e1": 1.0})
        assert _close((0 - e)(V1=x), (-e)(V1=x))

    def test_sub(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e = v * a - v * b
        x = self._mv({"e1": 1.0})
        assert _close(e(V1=x), x * a - x * b)

    def test_different_variables_is_affine(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e = v * a + w * b
        assert isinstance(e, AffineExpression)
        x = self._mv({"e1": 1.0})
        y = self._mv({"e3": 1.0})
        assert _close(e(V1=x, V2=y), (x * a) + (y * b))

    def test_mask_unification(self):
        mask = BladeMask(self.alg, [1])  # variable holds only e1
        v = Variable("V1", mask)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e = v * a + v * b
        x = self._mv({"e1": 1.0})
        assert _close(e(V1=x), x * a + x * b)


class TestInvolutions:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_reverse_variable(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e12": 3.0})
        assert _close((~v)(V1=x), x.rev())

    def test_conj_variable(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e12": 3.0})
        assert _close(v.conj()(V1=x), x.conj())

    def test_reverse_expression(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e2": 3.0})
        e = v * a
        x = self._mv({"e1": 1.0, "e3": -1.0})
        assert _close((~e)(V1=x), (x * a).rev())

    def test_conj_expression(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = v * a
        x = self._mv({"e2": 1.0})
        assert _close(e.conj()(V1=x), (x * a).conj())

    def test_constant_build_time_involution(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0, "e2": 3.0})
        e = v * ~a
        x = self._mv({"e1": 1.0, "e3": 2.0})
        assert _close(e(V1=x), x * a.rev())

    def test_constant_times_reverse_variable(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = a * ~v
        x = self._mv({"e2": 3.0, "e12": 1.0})
        assert _close(e(V1=x), a * x.rev())


class TestBatched:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_single_list(self):
        v = Variable("V1", self.full)
        a = self._mv({"e1": 2.0})
        e = v * a
        xs = [
            self._mv({"e1": 1.0}),
            self._mv({"e2": 3.0}),
            self._mv({"e3": -1.0}),
        ]
        result = e(V1=DataArray(xs, masks=("n", self.full)))
        assert isinstance(result, list)
        assert len(result) == 3
        for r, x in zip(result, xs):
            assert _close(r, x * a)

    def test_two_lists_cross_product(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        xs = [self._mv({"e1": 1.0}), self._mv({"e2": 2.0})]
        ys = [self._mv({"e3": 3.0}), self._mv({"e1": 4.0})]
        result = e(
            V1=DataArray(xs, masks=("n", self.full)),
            V2=DataArray(ys, masks=("m", self.full)),
        )
        assert isinstance(result, list) and len(result) == 2
        assert all(isinstance(row, list) and len(row) == 2 for row in result)
        for i, x in enumerate(xs):
            for j, y in enumerate(ys):
                assert _close(result[i][j], x * y)


class TestExpressionN3:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisN3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_gp_ip_op_roundtrip(self):
        v = Variable("V1", self.full)
        a = self._mv({1: 2.0, 2: 3.0})
        x = self._mv({1: 1.0, 4: -1.0})
        assert _close((v * a)(V1=x), x * a)
        assert _close((v | a)(V1=x), x | a)
        assert _close((v ^ a)(V1=x), x ^ a)

    def test_involutions_mixed_grade(self):
        # includes em (id 16), whose negative metric distinguishes conj from rev
        v = Variable("V1", self.full)
        a = self._mv({1: 2.0, 16: 1.0})
        e = v * a
        x = self._mv({2: 1.0, 8: 2.0})
        assert _close((~e)(V1=x), (x * a).rev())
        assert _close(e.conj()(V1=x), (x * a).conj())


class TestInverse:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_inv_roundtrip(self):
        v = Variable("V1", self.full)
        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        e = v * R  # square 8x8: x -> x * R
        e_inv = e.inv("V2")
        x = self._mv({"e1": 1.0, "e2": 2.0, "e3": 3.0})
        y = e(V1=x)
        assert _close(e_inv(V2=y), x)

    def test_inv_multivariable_rejected(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        with pytest.raises(ValueError):
            e.inv("V3")

    def test_inv_nonsquare_rejected(self):
        v = Variable("V1", BladeMask(self.alg, [1, 2]))
        a = self._mv({0: 1.0, 1: 1.0})  # 1 + e1
        e = v * a  # output mask has 4 blades, variable mask has 2
        with pytest.raises(ValueError):
            e.inv("V2")

    def test_inv_singular_rejected(self):
        v = Variable("V1", self.full)
        a = self._mv({0: 1.0, 1: 1.0})  # 1 + e1 is a zero divisor -> singular map
        e = v * a
        with pytest.raises(ValueError):
            e.inv("V2")


class TestLeastSquares:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_lstsq_rhs_recovers_solution(self):
        v = Variable("V1", self.full)
        R = create_rotor(self.alg, 0.5, Direction(1, 0, 0))
        e = v * R
        x = self._mv({"e1": 1.0, "e2": 2.0, "e3": 3.0})
        y = e(V1=x)
        assert _close(e.lstsq(rhs=y), x)

    def test_lstsq_homogeneous_recovers_line_direction(self):
        from pytanga.basis import BasisP3
        from pytanga.geometry import Geometry, Line, Point

        alg = BasisP3()
        geo = Geometry(alg)
        P = geo.create_var("P", Point)
        L = geo.create_var("L", Line)

        pts = [geo.create(Point(t, 0.0, 0.0)) for t in (1.0, 2.0, 3.0, 4.0)]
        constraints = (P ^ L)(P=DataArray(pts, masks=("n", P.mask)))
        L_est = constraints.lstsq()

        # A point on the fitted line should satisfy incidence ~ 0.
        p = geo.create(Point(2.0, 0.0, 0.0))
        assert (p ^ L_est).mag < 1e-8

    def test_lstsq_rejects_multivariable(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        with pytest.raises(ValueError):
            (v * w).lstsq()

    def test_lstsq_rejects_repeated_variable(self):
        v = Variable("V1", self.full)
        with pytest.raises(ValueError):
            (v * v).lstsq()

    def test_svd_returns_sorted_values_and_mvs(self):
        v = Variable("V1", BladeMask(self.alg, [1, 2, 4]))
        a = self._mv({0: 2.0, 1: 1.0})  # 2-scalar + e1 -> diagonal-ish map
        e = v * a

        values, mvs = e.svd()
        assert isinstance(values, list)
        assert len(values) == len(mvs)
        assert values == sorted(values, reverse=True)
        assert all(_is_mv(mv) for mv in mvs)

    def test_svd_smallest_singular_mv_matches_lstsq(self):
        from pytanga.basis import BasisP3
        from pytanga.geometry import Geometry, Line, Point

        alg = BasisP3()
        geo = Geometry(alg)
        P = geo.create_var("P", Point)
        L = geo.create_var("L", Line)
        pts = [geo.create(Point(t, 0.0, 0.0)) for t in (1.0, 2.0, 3.0, 4.0)]
        constraints = (P ^ L)(P=DataArray(pts, masks=("n", P.mask)))

        values, mvs = constraints.svd()
        L_svd = mvs[-1]  # smallest singular vector
        L_lstsq = constraints.lstsq()
        # Same homogeneous solution up to sign/scale.
        assert abs(L_svd.sp(L_lstsq)) > 0.99 * L_svd.mag * L_lstsq.mag

    def test_svd_rejects_multivariable(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        with pytest.raises(ValueError):
            (v * w).svd()


def _is_mv(obj) -> bool:
    from pytanga.algebra import MV

    return isinstance(obj, MV)


class TestPartial:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_partial_single(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        x = self._mv({"e1": 2.0})
        y = self._mv({"e2": 3.0})
        partial = e(V1=x)
        assert isinstance(partial, Expression)
        assert set(partial.names) == {"V2"}
        assert not partial._has_counting_axes()
        assert _close(partial(V2=y), e(V1=x, V2=y))

    def test_jacobian(self):
        # Jacobian of (v * w) w.r.t. w, holding v fixed, is the linear map z -> x*z.
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        x = self._mv({"e1": 1.0})
        jac = e(V1=x)
        assert isinstance(jac, Expression)
        assert jac.tensor.ndim == 2
        z = self._mv({"e3": 1.0, "e2": 2.0})
        assert _close(jac(V2=z), x * z)

    def test_partial_batch(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        y = self._mv({"e2": 3.0})
        partial = e(V1=DataArray(xs, masks=("n", self.full)))
        assert isinstance(partial, Expression)
        assert partial._has_counting_axes()
        result = partial(V2=y)
        assert isinstance(result, list) and len(result) == 2
        for r, x in zip(result, xs):
            assert _close(r, x * y)

    def test_partial_batch_named_label(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        e = v * w
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        partial = e(V1=DataArray(xs, masks=("n", self.full)))
        assert "n" in _axis_names(partial.tensor.labels)
        y = self._mv({"e2": 3.0})
        result = partial(V2=y)
        for r, x in zip(result, xs):
            assert _close(r, x * y)

    def test_stacked_guards(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        z = Variable("V3", self.full)
        e = v * w
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        partial = e(V1=DataArray(xs, masks=("n", self.full)))
        c = self._mv({"e1": 1.0})

        # A single stacked operand may now be composed with a constant/variable.
        for comp in (partial * c, c * partial, partial * z, z * partial):
            assert isinstance(comp, Expression)
            assert comp._has_counting_axes()
        assert "n" in _axis_names((partial * c).tensor.labels)
        names = _axis_names((partial * c).tensor.labels)
        assert _axis_modes((partial * c).tensor.labels)[names.index("n")] == "_"

        # Structurally identical stacked operands merge under addition.
        merged = partial + partial
        assert isinstance(merged, Expression)
        assert merged._has_counting_axes()
        y = self._mv({"e2": 3.0})
        result = merged(V2=y)
        assert isinstance(result, list) and len(result) == 2
        for r, x in zip(result, xs):
            assert _close(r, 2.0 * (x * y))

        # Two stacked operands still cannot be composed.
        with pytest.raises(ValueError):
            partial * partial
        with pytest.raises(ValueError):
            partial.inv("V3")
        assert (~partial)._has_counting_axes()
        assert (2.0 * partial)._has_counting_axes()


class TestRepeatedVariables:
    def setup_method(self):
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):
        return self.alg.multivector(coeffs)

    def test_cubic(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0, "e2": 3.0})
        e = v * v * v
        assert _close(e(V1=x), x * x * x)

    def test_square_merges(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0})
        e = (v * v) + (v * v)
        assert e.tensor.ndim == 3  # out + two occurrences, merged into one tensor
        assert _close(e(V1=x), (x * x) + (x * x))

    def test_square_cancels(self):
        v = Variable("V1", self.full)
        x = self._mv({"e1": 2.0})
        e = (v * v) - (v * v)
        assert _close(e(V1=x), self.alg.multivector({}))

    def test_interleaved_order_not_merged(self):
        v = Variable("V1", self.full)
        w = Variable("V2", self.full)
        a = v * w * v  # v0, w0, v1
        b = v * v * w  # v0, v1, w0
        s = a + b  # different axis order -> affine (not merged)
        assert isinstance(s, AffineExpression)
        assert len(s.terms) == 2
        x = self._mv({"e1": 1.0})
        y = self._mv({"e2": 1.0})
        assert _close(s(V1=x, V2=y), a(V1=x, V2=y) + b(V1=x, V2=y))

    def test_inv_rejects_quadratic(self):
        v = Variable("V1", self.full)
        with pytest.raises(ValueError):
            (v * v).inv("V2")

    def test_degree_exceeded(self):
        v = Variable("V1", self.full)
        with pytest.raises(ValueError):
            v * v * v * v * v  # 5 occurrences > MAX_DEGREE

    def test_batch_quadratic(self):
        v = Variable("V1", self.full)
        xs = [self._mv({"e1": 1.0}), self._mv({"e1": 2.0})]
        e = v * v
        result = e(V1=DataArray(xs, masks=("n", self.full)))
        assert isinstance(result, list) and len(result) == 2
        for r, x in zip(result, xs):
            assert _close(r, x * x)


def test_batched_sandwich_merge():
    """The note's repro: (motor * X)(X=batch) - (Y * motor)(Y=batch) merges."""
    _reset_allocator()
    N3 = BasisN3()
    geo = Geometry(N3)
    motor = geo.create_var("motor", Motor)
    X = geo.create_var("X", Point)
    Y = geo.create_var("Y", Point)

    local_points = [geo(Point(0, 0, 0)), geo(Point(1, 0, 0)), geo(Point(0, 1, 0))]
    world_points = [geo(Point(1, 2, 3)), geo(Point(2, 2, 3)), geo(Point(1, 3, 3))]

    lm = (motor * X)(X=DataArray(local_points, masks=("n", X.mask)))
    rm = (Y * motor)(Y=DataArray(world_points, masks=("n", Y.mask)))

    eqn = lm - rm
    assert isinstance(eqn, Expression)
    assert eqn._has_counting_axes()
    assert set(eqn.names) == {"motor"}

    m = geo(
        Motor(
            rotor=Rotor(0.0, Direction(1, 0, 0)),
            translator=Translator(Direction(0, 0, 0)),
        )
    )
    result = eqn(motor=m)
    assert isinstance(result, list) and len(result) == 3
    for r, x, y in zip(result, local_points, world_points):
        assert _close(r, m * x - y * m)


def test_stacked_add_different_labels_raises():
    _reset_allocator()
    alg = BasisE3()
    full = BladeMask.full(alg)
    v = Variable("V1", full)
    w = Variable("V2", full)
    e = v * w
    xs = [alg.multivector({"e1": 1.0}), alg.multivector({"e1": 2.0})]
    p1 = e(V1=DataArray(xs, masks=("n", full)))
    p2 = e(V1=DataArray(xs, masks=("m", full)))
    with pytest.raises(ValueError):
        p1 + p2


def test_constant_expression():
    _reset_allocator()
    alg = BasisE3()
    A = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0})
    E = Expression(A)
    assert E.names == {}
    assert E.masks == {}
    assert E.out_mask == BladeMask(A)
    assert E.ndim == 1
    assert _close(E(), A)


def test_constant_expression_with_mask():
    from pytanga.tensor.convert import from_tensor

    _reset_allocator()
    alg = BasisE3()
    A = alg.multivector({"s": 1.0, "e1": 2.0, "e2": 3.0, "e12": 4.0})
    mask = BladeMask(alg, [1, 3])  # e1, e12
    E = Expression(A, mask)
    assert E.out_mask == mask
    result = from_tensor(E.tensor.tensor)
    assert _close(result, A.project_onto(mask))
