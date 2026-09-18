# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for ``BladeMask`` named bases."""

from __future__ import annotations

import pytest

from pytanga import BladeMask
from pytanga.basis import BasisN3


class TestBladeMaskNamedBasis:
    def test_auto_display_basis_grade1(self) -> None:
        alg = BasisN3()
        mask = BladeMask(alg, grades=[1])
        assert mask.basis_names == ["e1", "e2", "e3", "einf", "eo"]

    def test_auto_display_basis_grade2(self) -> None:
        alg = BasisN3()
        mask = BladeMask(alg, grades=[2])
        assert len(mask.basis_vectors) == 10
        assert "e1∧einf" in mask.basis_names

    def test_raw_fallback_for_partial_subspace(self) -> None:
        alg = BasisN3()
        mask = BladeMask(alg, [8])  # ep alone — no display direction covers it
        assert mask.basis_names == ["e4"]
        assert mask.basis_vectors[0].to_dict() == alg.ep.to_dict()

    def test_composed_string_parse(self) -> None:
        alg = BasisN3()
        assert BladeMask(alg, "e1 + einf").ids == [1, 8, 16]
        assert BladeMask(alg, "eo").ids == [8, 16]

    def test_with_basis_reduced(self) -> None:
        alg = BasisN3()
        twist = BladeMask(alg, [3, 5, 6, 9, 10, 12, 17, 18, 20])
        d1 = alg.e1.op(alg.einf)
        d2 = alg.e2.op(alg.einf)
        d3 = alg.e3.op(alg.einf)
        mask = twist.with_basis(
            [
                ("e12", alg.e12),
                ("e13", alg.e13),
                ("e23", alg.e23),
                ("e1∧einf", d1),
                ("e2∧einf", d2),
                ("e3∧einf", d3),
            ]
        )
        assert mask.ids == twist.ids
        assert mask.basis_names == [
            "e12",
            "e13",
            "e23",
            "e1∧einf",
            "e2∧einf",
            "e3∧einf",
        ]
        assert len(mask.basis_vectors) == 6

    def test_with_basis_out_of_mask_raises(self) -> None:
        alg = BasisN3()
        mask = BladeMask(alg, [1, 2])
        with pytest.raises(ValueError):
            mask.with_basis([("einf", alg.einf)])

    def test_basis_matrix(self) -> None:
        alg = BasisN3()
        mask = BladeMask(alg, grades=[1])  # ids [1, 2, 4, 8, 16]
        bmat = mask.basis_matrix()
        assert bmat.shape == (5, 5)
        # einf column (basis index 3) = ep (id 8) + em (id 16)
        assert bmat[mask.ids.index(8), 3] == 1.0
        assert bmat[mask.ids.index(16), 3] == 1.0


class TestBladeMaskUnionIntersection:
    def test_union_merges_named_bases(self) -> None:
        alg = BasisN3()
        support = BladeMask(alg, [9, 10, 12, 17, 18, 20])
        a = support.with_basis(
            [
                ("e1∧einf", alg.e1.op(alg.einf)),
                ("e2∧einf", alg.e2.op(alg.einf)),
                ("e3∧einf", alg.e3.op(alg.einf)),
            ]
        )
        b = support.with_basis(
            [
                ("e1∧eo", alg.e1.op(alg.eo)),
                ("e2∧eo", alg.e2.op(alg.eo)),
                ("e3∧eo", alg.e3.op(alg.eo)),
            ]
        )
        merged = a.union(b)
        assert merged.ids == support.ids
        assert merged.basis_names == [
            "e1∧einf",
            "e2∧einf",
            "e3∧einf",
            "e1∧eo",
            "e2∧eo",
            "e3∧eo",
        ]

    def test_intersection_strict_raises_and_discard(self) -> None:
        alg = BasisN3()
        e4 = BladeMask(alg, [8])
        einf = BladeMask(alg, [8, 16]).with_basis([("einf", alg.einf)])
        with pytest.raises(ValueError):
            e4.intersection(einf)
        fallback = e4.intersection(einf, discard_basis=True)
        assert fallback.ids == [8]
        assert fallback.basis_names == ["e4"]

    def test_intersection_named_equal(self) -> None:
        alg = BasisN3()
        a = BladeMask(alg, [8, 16]).with_basis([("einf", alg.einf)])
        b = BladeMask(alg, [8, 16]).with_basis([("einf", alg.einf)])
        out = a.intersection(b)
        assert out.ids == [8, 16]
        assert out.basis_names == ["einf"]

    def test_intersection_named_disjoint(self) -> None:
        alg = BasisN3()
        a = BladeMask(alg, [8, 16]).with_basis([("einf", alg.einf)])
        b = BladeMask(alg, [8, 16]).with_basis([("eo", alg.eo)])
        out = a.intersection(b)
        assert out.ids == []
        assert out.basis_names == []
