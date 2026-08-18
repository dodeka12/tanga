# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for BladeMask construction."""

import pytest
from pytanga import BladeMask
from pytanga.algebra import EProduct
from pytanga.blade_mask.predict import inverse_blade_mask, product_blade_mask


class TestBladeMask:
    def test_int_ids_sorted_deduped(self, alg_float):
        m = BladeMask(alg_float, [4, 1, 1, 2])
        assert m.ids == [1, 2, 4]

    def test_index_lookup(self, alg_float):
        m = BladeMask(alg_float, [4, 1, 1, 2])
        assert m.index(2) == 1

    def test_contains(self, alg_float):
        m = BladeMask(alg_float, [4, 1, 1, 2])
        assert 4 in m
        assert 7 not in m

    def test_from_mv(self, alg_float, vec_A_float, mask_A_float):
        assert mask_A_float.algebra is alg_float
        expected_ids = {alg_float.blade_id(name) for name in vec_A_float.to_dict()}
        assert set(mask_A_float.ids) == expected_ids

    def test_from_array(self, alg_float):
        e1 = alg_float("e1")
        e2 = alg_float("e2")
        e12 = alg_float("e12")
        mask = BladeMask.from_array([e1, e2])
        assert mask.ids == [1, 2]
        a = alg_float("e1 + e12")
        b = alg_float("e2 + e12")
        mask2 = BladeMask.from_array([a, b])
        assert mask2.ids == [1, 2, 3]
        mask4 = BladeMask.from_array([e12])
        assert mask4.ids == [3]
        with pytest.raises(ValueError):
            BladeMask.from_array([])

    def test_from_str_expression(self, alg_float):
        m = BladeMask(alg_float, "1 + 2 e3 - e13")
        assert m.ids == [0, 4, 5]

    def test_from_str_simple(self, alg_float):
        m = BladeMask(alg_float, "e1 - e2")
        assert m.ids == [1, 2]

    def test_from_list_of_strings(self, alg_float):
        m = BladeMask(alg_float, ["e12", "1 + e13"])
        assert m.ids == [0, 3, 5]

    def test_grades_scalar(self, alg_float):
        assert BladeMask(alg_float, grades=[0]).ids == [0]

    def test_grades_bivectors(self, alg_float):
        assert BladeMask(alg_float, grades=[2]).ids == [3, 5, 6]

    def test_grades_even_subalgebra(self, alg_float):
        assert BladeMask(alg_float, grades=[0, 2]).ids == [0, 3, 5, 6]

    def test_combined_ids_and_grades(self, alg_float):
        assert BladeMask(alg_float, ["e1"], grades=[2]).ids == [1, 3, 5, 6]

    def test_full(self, alg_float):
        assert BladeMask.full(alg_float).ids == list(range(8))

    def test_union(self, alg_float):
        a = BladeMask(alg_float, [1, 2, 4])
        b = BladeMask(alg_float, grades=[0])
        u = a.union(b)
        assert 0 in u and 1 in u

    def test_intersection(self, alg_float):
        a = BladeMask(alg_float, [0, 1, 2])
        b = BladeMask(alg_float, [0, 3])
        assert a.intersection(b).ids == [0]

    def test_union_cross_algebra_raises(self, alg_float, alg_int):
        a = BladeMask(alg_float, [1])
        b = BladeMask(alg_int, [1])
        with pytest.raises(AssertionError):
            a.union(b)

    def test_product_blade_mask_gp(self, alg_float, mask_A_float):
        out = product_blade_mask( mask_A_float, mask_A_float, complete=True)
        assert isinstance(out, BladeMask)
        assert len(out) >= 1

    def test_product_blade_mask_cross_algebra_raises(self, alg_float, alg_int):
        float_mask = BladeMask(alg_float, [1])
        wrong_mask = BladeMask(alg_int, [1])
        with pytest.raises(AssertionError):
            product_blade_mask( float_mask, wrong_mask)

    def test_unknown_product_raises(self, alg_float, mask_A_float):
        with pytest.raises(ValueError):
            product_blade_mask( mask_A_float, mask_A_float, product="xy")

    def test_inverse_blade_mask_ip_both_directions(self, alg_float):
        # A = e12, C = {e1, e2, e3}.  The symmetric inner product is non-zero
        # when either blade contains the other, so X can be a sub-blade of A
        # (e1, e2 from k ⊆ i) or a super-blade of A (e123 from i ⊆ k).
        a = BladeMask(alg_float, "e12")
        c = BladeMask(alg_float, "e1 + e2 + e3")
        out = inverse_blade_mask(a, c, product=EProduct.IP)
        assert out.ids == [1, 2, 7]  # e1, e2, e123

    def test_inverse_blade_mask_ip_independent_of_left(self, alg_float):
        a = BladeMask(alg_float, "e12")
        c = BladeMask(alg_float, "e1 + e2 + e3")
        left = inverse_blade_mask(a, c, product=EProduct.IP, left=True).ids
        right = inverse_blade_mask(a, c, product=EProduct.IP, left=False).ids
        assert left == right == [1, 2, 7]

    def test_inverse_blade_mask_op_independent_of_left(self, alg_float):
        # X ∧ e1 = e12  →  X = e2, same support as e1 ∧ X = e12
        a = BladeMask(alg_float, "e1")
        c = BladeMask(alg_float, "e12")
        left = inverse_blade_mask(a, c, product=EProduct.OP, left=True).ids
        right = inverse_blade_mask(a, c, product=EProduct.OP, left=False).ids
        assert left == right == [2]  # e2
