# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the GA-native (expression-system) conic/quadric from-points fit."""

import math

import pytest

from pytanga.blade_mask import BladeMask
from pytanga.expression import DataArray, Variable
from pytanga.geometry import Geometry, Point
from pytanga.quadric import BasisQ2, BasisQ3


def _build_ok() -> bool:
    try:
        BasisQ2()
        BasisQ3()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (Python.h missing)",
)


def _nullity(values: list[float], tol: float) -> int:
    scale = max(values)
    return sum(1 for v in values if abs(v) <= tol * scale)


@_NEEDS_BUILD
def test_conic_svd_recovers_ellipse() -> None:
    q2 = BasisQ2()
    geo = Geometry(q2)
    pts = [(2.0, 0.0), (0.0, 1.0), (-2.0, 0.0), (0.0, -1.0), (1.0, math.sqrt(3.0) / 2.0)]
    emb = [geo(Point(x, y, 0)) for x, y in pts]
    mask = BladeMask(q2, grades=[1])
    partial = Variable("c", mask).sp(Variable("p", mask))(
        p=DataArray(emb, masks=("pnt_idx", mask))
    )
    conic = partial.lstsq()
    for x, y in pts:
        assert float(geo(Point(x, y, 0)).sp(conic)) == pytest.approx(0.0, abs=1e-6)


@_NEEDS_BUILD
def test_quadric_svd_recovers_sphere() -> None:
    q3 = BasisQ3()
    geo = Geometry(q3)
    s = 1.0 / math.sqrt(2.0)
    t = 1.0 / math.sqrt(3.0)
    pts = [
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (-1.0, 0.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, -1.0),
        (t, t, t),
        (-t, t, -t),
        (s, -s, 0.0),
    ]
    emb = [geo(Point(x, y, z)) for x, y, z in pts]
    mask = BladeMask(q3, grades=[1])
    partial = Variable("c", mask).sp(Variable("p", mask))(
        p=DataArray(emb, masks=("pnt_idx", mask))
    )
    quadric = partial.lstsq()
    for x, y, z in pts:
        assert float(geo(Point(x, y, z)).sp(quadric)) == pytest.approx(0.0, abs=1e-6)


@_NEEDS_BUILD
def test_singular_values_pad_to_variable_count() -> None:
    q2 = BasisQ2()
    geo = Geometry(q2)
    pts = [(2.0, 0.0), (0.0, 1.0), (-2.0, 0.0), (0.0, -1.0), (1.0, math.sqrt(3.0) / 2.0)]
    emb = [geo(Point(x, y, 0)) for x, y in pts]
    mask = BladeMask(q2, grades=[1])
    partial = Variable("c", mask).sp(Variable("p", mask))(
        p=DataArray(emb, masks=("pnt_idx", mask))
    )
    values, _ = partial.svd()
    assert len(values) == 6
    assert values[-1] == pytest.approx(0.0, abs=1e-8)


@_NEEDS_BUILD
def test_nullity_detects_coplanar_degeneracy() -> None:
    q3 = BasisQ3()
    geo = Geometry(q3)
    pts = [(0.0, 0.0, 0.0)]
    pts += [
        (math.cos(theta), math.sin(theta), 1.0)
        for theta in (2.0 * math.pi * i / 20.0 for i in range(20))
    ]
    emb = [geo(Point(x, y, z)) for x, y, z in pts]
    mask = BladeMask(q3, grades=[1])
    partial = Variable("c", mask).sp(Variable("p", mask))(
        p=DataArray(emb, masks=("pnt_idx", mask))
    )
    values, _ = partial.svd()
    assert _nullity(values, q3.precision) >= 2
