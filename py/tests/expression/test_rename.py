# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for variable substitution, rename_var, and unify."""

import pytest

from pytanga import BladeMask, Variable
from pytanga.basis import BasisE3
from pytanga.expression import unify
from pytanga.expression._expression import AffineExpression, Expression
from pytanga.expression._labels import _reset_allocator


def _close(a, b) -> bool:  # noqa: ANN001
    return (a - b).mag < 1e-12


class TestSubstituteRename:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_substitute_unifies_same_name(self):  # noqa: ANN201
        x1 = Variable("X", self.full)
        x2 = Variable("X", self.full)
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        s = (x1 * a)._substitute({"X": x}) + (x2 * b)._substitute({"X": x})
        assert isinstance(s, Expression)  # merged, not affine
        v = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(s(X=v), v * a + v * b)

    def test_substitute_renames(self):  # noqa: ANN201
        x = Variable("X", self.full)
        y = Variable("Y", self.full)
        a = self._mv({"e1": 2.0})
        r = (x * a)._substitute({"X": y})
        assert r.names == {"Y": (y.labels[0],)}

    def test_substitute_merges_two_names(self):  # noqa: ANN201
        va = Variable("a", self.full)
        vb = Variable("b", self.full)
        x = Variable("X", self.full)
        e = va * vb
        r = e._substitute({"a": x, "b": x})
        assert set(r.names) == {"X"}
        assert len(r.names["X"]) == 2
        v = self._mv({"e1": 2.0})
        assert _close(r(X=v), v * v)

    def test_substitute_skips_absent(self):  # noqa: ANN201
        x = Variable("X", self.full)
        y = Variable("Y", self.full)
        a = self._mv({"e1": 2.0})
        r = (x * a)._substitute({"X": y, "Z": y})
        assert r.names == {"Y": (y.labels[0],)}

    def test_substitute_mask_mismatch(self):  # noqa: ANN201
        x = Variable("X", self.full)
        vec_mask = BladeMask(self.alg, grades=[1])
        y = Variable("Y", vec_mask)
        a = self._mv({"e1": 2.0})
        with pytest.raises(ValueError):
            (x * a)._substitute({"X": y})

    def test_substitute_collision_with_kept(self):  # noqa: ANN201
        x = Variable("X", self.full)
        y = Variable("Y", self.full)
        e = x * y
        # Substituting Y -> X collides with the kept variable "X".
        with pytest.raises(ValueError):
            e._substitute({"Y": x})

    def test_rename_var_name_only(self):  # noqa: ANN201
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        e = x * a
        r = e.rename_var("X", "Y")
        assert r.names == {"Y": e.names["X"]}  # same label block
        v = self._mv({"e1": 3.0})
        assert _close(r(Y=v), v * a)

    def test_rename_var_unknown(self):  # noqa: ANN201
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        with pytest.raises(ValueError):
            (x * a).rename_var("Z", "Y")

    def test_rename_var_collision(self):  # noqa: ANN201
        x = Variable("X", self.full)
        y = Variable("Y", self.full)
        e = x * y
        with pytest.raises(ValueError):
            e.rename_var("X", "Y")


class TestBindSubstitution:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_bind_substitute_merges(self):  # noqa: ANN201
        x1 = Variable("X", self.full)
        x2 = Variable("X", self.full)
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        s = (x1 * a).bind(X=x) + (x2 * b).bind(X=x)
        assert isinstance(s, Expression)
        v = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(s(X=v), v * a + v * b)

    def test_bind_rename(self):  # noqa: ANN201
        x = Variable("X", self.full)
        y = Variable("Y", self.full)
        a = self._mv({"e1": 2.0})
        r = (x * a).bind(X=y)
        assert r.names == {"Y": (y.labels[0],)}

    def test_bind_unknown_substitution(self):  # noqa: ANN201
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        with pytest.raises(ValueError):
            (x * a).bind(Z=Variable("Y", self.full))

    def test_bind_value_regression(self):  # noqa: ANN201
        x = Variable("X", self.full)
        w = Variable("W", self.full)
        e = x * w
        v = self._mv({"e1": 3.0})
        partial = e.bind(X=v)
        assert isinstance(partial, Expression)
        assert set(partial.names) == {"W"}

    def test_bind_mixed_substitute_then_value(self):  # noqa: ANN201
        x1 = Variable("X", self.full)
        w = Variable("W", self.full)
        x = Variable("X", self.full)
        e = x1 * w
        wv = self._mv({"e2": 3.0})
        r = e.bind(X=x, W=wv)
        assert set(r.names) == {"X"}
        xv = self._mv({"e1": 2.0})
        assert _close(r(X=xv), xv * wv)


class TestAffineSubstitution:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_bind_substitutes_all_terms(self):  # noqa: ANN201
        x1 = Variable("X", self.full)
        x2 = Variable("X", self.full)
        x = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        aff = x1 * a + x2 * b
        assert isinstance(aff, AffineExpression)
        s = aff.bind(X=x)
        assert isinstance(s, AffineExpression)
        v = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(s(X=v), v * a + v * b)

    def test_rename_var_distributes(self):  # noqa: ANN201
        x1 = Variable("X", self.full)
        x2 = Variable("X", self.full)
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        aff = x1 * a + x2 * b
        r = aff.rename_var("X", "Y")
        assert r.names == {"Y"}
        v = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(r(Y=v), v * a + v * b)

    def test_rename_var_skips_terms_missing_var(self):  # noqa: ANN201
        a = Variable("A", self.full)
        b = Variable("B", self.full)
        e1 = self._mv({"e1": 2.0})
        e2 = self._mv({"e2": 3.0})
        aff = a * e1 + b * e2
        r = aff.rename_var("A", "A2")
        assert r.names == {"A2", "B"}
        va = self._mv({"e1": 1.0})
        vb = self._mv({"e2": 4.0})
        assert _close(r(A2=va, B=vb), va * e1 + vb * e2)

    def test_rename_var_unknown_across_all_terms(self):  # noqa: ANN201
        a = Variable("A", self.full)
        b = Variable("B", self.full)
        aff = a * self._mv({"e1": 2.0}) + b * self._mv({"e2": 3.0})
        with pytest.raises(ValueError):
            aff.rename_var("Z", "Y")

    def test_rename_var_collision_across_terms(self):  # noqa: ANN201
        a = Variable("A", self.full)
        b = Variable("B", self.full)
        aff = a * self._mv({"e1": 2.0}) + b * self._mv({"e2": 3.0})
        with pytest.raises(ValueError):
            aff.rename_var("A", "B")


class TestUnify:
    def setup_method(self):  # noqa: ANN201
        _reset_allocator()
        self.alg = BasisE3()
        self.full = BladeMask.full(self.alg)

    def _mv(self, coeffs):  # noqa: ANN001, ANN202
        return self.alg.multivector(coeffs)

    def test_unify_remaps_different_names_to_same(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0})
        b = self._mv({"e2": 3.0})
        e1 = Variable("X", self.full) * a
        e2 = Variable("Y", self.full) * b
        x = Variable("X", self.full)
        r = unify([e1, e2], X=x, Y=x)
        s = r[0] + r[1]
        assert isinstance(s, Expression)  # merged into a single term
        v = self._mv({"e1": 1.0, "e2": 4.0})
        assert _close(s(X=v), v * a + v * b)

    def test_unify_skips_absent(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0})
        e = Variable("X", self.full) * a
        x = Variable("X", self.full)
        r = unify([e], X=x, Z=x)
        assert r[0].names == {"X": (x.labels[0],)}

    def test_unify_mask_mismatch(self):  # noqa: ANN201
        a = self._mv({"e1": 2.0})
        e = Variable("X", self.full) * a
        vec_mask = BladeMask(self.alg, grades=[1])
        y = Variable("Y", vec_mask)
        with pytest.raises(ValueError):
            unify([e], X=y)
