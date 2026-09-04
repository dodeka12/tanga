# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Variable class."""

import pytest

from pytanga import BladeMask
from pytanga.basis import BasisE3
from pytanga.expression import Expression
from pytanga.expression._labels import MAX_DEGREE, _reset_allocator
from pytanga.expression._variable import Variable


class TestVariable:
    def test_construction_and_properties(self):
        _reset_allocator()
        alg = BasisE3()
        mask = BladeMask(alg, grades=[0, 2])
        v = Variable("V1", mask)
        assert v.name == "V1"
        assert v.mask is mask
        assert v.algebra is alg
        assert v.label == 0
        assert v.labels[0] == v.label
        assert len(v.labels) == MAX_DEGREE

    def test_label_blocks_are_distinct(self):
        _reset_allocator()
        alg = BasisE3()
        mask = BladeMask(alg, grades=[0, 2])
        v = Variable("V1", mask)
        w = Variable("V2", mask)
        assert v.labels != w.labels
        assert not (set(v.labels) & set(w.labels))

    def test_many_variables(self):
        _reset_allocator()
        alg = BasisE3()
        mask = BladeMask(alg, grades=[0, 2])
        for i in range(200):
            v = Variable(f"V{i}", mask)
            assert isinstance(v.label, int)
            assert v.label >= 0

    def test_repr(self):
        _reset_allocator()
        alg = BasisE3()
        v = Variable("V1", BladeMask(alg, grades=[0, 2]))
        assert "V1" in repr(v)

    def test_mask_type_error(self):
        with pytest.raises(TypeError):
            Variable("V1", "not a mask")

    def test_public_imports(self):
        from pytanga import Expression, Variable as TopVar
        from pytanga.expression import Expression as PkgExpr, Variable as PkgVar

        assert TopVar is Variable
        assert PkgVar is Variable
        assert PkgExpr is Expression

    def test_reflected_ops_constant_left(self):
        _reset_allocator()
        alg = BasisE3()
        omega = Variable("omega", BladeMask(alg, grades=[2]))
        x_cm = alg.multivector({"e12": 1.0, "e13": 2.0})
        for result in (x_cm ^ omega, x_cm | omega, x_cm * omega):
            assert isinstance(result, Expression)
            assert set(result.names) == {"omega"}
