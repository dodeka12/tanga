# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for Hyperboloid / Paraboloid entity creation (Q3)."""

import pytest

from pytanga.geometry import Geometry, Hyperboloid, Paraboloid, Point
from pytanga.quadric import BasisQ3, Quadric3D


def _build_ok() -> bool:
    try:
        BasisQ3()
        return True
    except Exception:
        return False


_NEEDS_BUILD = pytest.mark.skipif(
    not _build_ok(),
    reason="C++ extension build unavailable (Python.h missing)",
)


@_NEEDS_BUILD
def test_hyperboloid_one_sheet_round_trip() -> None:
    geo = Geometry(BasisQ3(opns=False))
    mv = geo(Hyperboloid(Point(0, 0, 0), (1.0, 1.0, 1.0), sheets=1))
    quad = geo.analyze(mv)
    assert isinstance(quad, Quadric3D)
    assert quad.kind.value == "hyperboloid_1s"


@_NEEDS_BUILD
def test_hyperboloid_two_sheet_round_trip() -> None:
    geo = Geometry(BasisQ3(opns=False))
    mv = geo(Hyperboloid(Point(0, 0, 0), (1.0, 1.0, 1.0), sheets=2))
    assert geo.analyze(mv).kind.value == "hyperboloid_2s"


@_NEEDS_BUILD
def test_hyperboloid_rejects_bad_sheets() -> None:
    with pytest.raises(ValueError):
        Hyperboloid(Point(0, 0, 0), (1.0, 1.0, 1.0), sheets=3)


@_NEEDS_BUILD
def test_paraboloid_round_trip() -> None:
    geo = Geometry(BasisQ3(opns=False))
    mv = geo(Paraboloid(Point(0, 0, 0), (1.0, 1.0)))
    quad = geo.analyze(mv)
    assert isinstance(quad, Quadric3D)
    assert quad.kind.value == "elliptic_paraboloid"


@_NEEDS_BUILD
def test_hyperbolic_paraboloid_round_trip() -> None:
    geo = Geometry(BasisQ3(opns=False))
    mv = geo(Paraboloid(Point(0, 0, 0), (1.0, 1.0), is_hyperbolic=True))
    assert geo.analyze(mv).kind.value == "hyperbolic_paraboloid"
