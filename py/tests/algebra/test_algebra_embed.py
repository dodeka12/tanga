# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the general algebra blade-relabeling primitive (``embed`` / ``to_algebra``)."""

import pytest

from pytanga.algebra import Algebra


def test_embed_relabels_coefficients() -> None:
    src = Algebra(3, 0)
    dst = Algebra(4, 0)
    mv = src.multivector({1: 2.0, 4: -1.5})
    out = dst.embed(mv, {1: 1, 4: 4})
    assert out[1] == pytest.approx(2.0)
    assert out[4] == pytest.approx(-1.5)
    assert out[2] == pytest.approx(0.0)


def test_embed_rejects_unmapped_blade() -> None:
    src = Algebra(3, 0)
    dst = Algebra(4, 0)
    mv = src.multivector({1: 2.0, 4: -1.5})
    with pytest.raises(ValueError):
        dst.embed(mv, {1: 1})


def test_embed_rejects_same_algebra() -> None:
    src = Algebra(3, 0)
    mv = src.multivector({1: 2.0})
    with pytest.raises(ValueError):
        src.embed(mv, {1: 1})


def test_to_algebra_requires_blade_map() -> None:
    src = Algebra(3, 0)
    dst = Algebra(4, 0)
    mv = src.multivector({1: 2.0})
    with pytest.raises(ValueError):
        mv.to_algebra(dst)
    out = mv.to_algebra(dst, {1: 1})
    assert out[1] == pytest.approx(2.0)
