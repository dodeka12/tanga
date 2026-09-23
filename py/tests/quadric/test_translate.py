# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for quadric-space translation (as a linear-map expression)."""

import math

import numpy as np
import pytest

from pytanga.entity import Direction, Point
from pytanga.expression import Expression
from pytanga.geometry import Geometry, create
from pytanga.geometry.operators import Translator
from pytanga.quadric import BasisQ2, BasisQ3, Conic, Quadric3D


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


@_NEEDS_BUILD
def test_translator_returns_expression_and_moves_cone_apex() -> None:
    q2 = BasisQ2()
    geo2 = Geometry(q2)
    pts = [
        (2.0, 0.0),
        (0.0, 1.0),
        (-2.0, 0.0),
        (0.0, -1.0),
        (1.0, math.sqrt(3.0) / 2.0),
    ]
    emb = [geo2(Point(x, y, 0)) for x, y in pts]
    conic = (emb[0] ^ emb[1] ^ emb[2] ^ emb[3] ^ emb[4]).undual()

    q3 = BasisQ3(opns=False)
    geo3 = Geometry(q3)
    cone0 = q3(conic)  # grade-1 cone coefficient, apex at origin

    trans = geo3(Translator(Direction(1.0, -2.0, 3.0)))
    assert isinstance(trans, Expression)
    cone = trans(cone0)  # positional apply

    quad = Quadric3D(tuple(float(cone[1 << i]) for i in range(10)))
    assert quad.rank == 3
    assert quad.kind.value == "cone"
    apex = quad.refine().vertex
    assert apex.x == pytest.approx(1.0, abs=1e-6)
    assert apex.y == pytest.approx(-2.0, abs=1e-6)
    assert apex.z == pytest.approx(3.0, abs=1e-6)


@_NEEDS_BUILD
def test_translate_quadric_round_trip() -> None:
    q3 = BasisQ3(opns=False)
    geo3 = Geometry(q3)
    sphere = create(q3, Quadric3D(np.diag([1.0, 1.0, 1.0, -1.0])))
    out = geo3(Translator(Direction(2.0, -1.0, 3.0)))(sphere)
    back = geo3(Translator(Direction(-2.0, 1.0, -3.0)))(out)
    for i in range(10):
        assert float(back[1 << i]) == pytest.approx(float(sphere[1 << i]), abs=1e-8)


@_NEEDS_BUILD
def test_translate_conic_2d_round_trip() -> None:
    q2 = BasisQ2(opns=False)
    geo2 = Geometry(q2)
    circle = create(q2, Conic(np.diag([1.0, 1.0, -1.0])))
    out = geo2(Translator(Direction(1.0, 2.0, 0.0)))(circle)
    back = geo2(Translator(Direction(-1.0, -2.0, 0.0)))(out)
    for i in range(6):
        assert float(back[1 << i]) == pytest.approx(float(circle[1 << i]), abs=1e-8)
