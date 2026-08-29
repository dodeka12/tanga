# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for creation (entities → quadric-space MV)."""

import numpy as np
import pytest

from pytanga.basis.e3 import BasisE3
from pytanga.geometry import (
    Circle,
    Conic,
    Ellipsoid,
    Point,
    Quadric3D,
    analyze,
    create,
    refine,
)
from pytanga.quadric import BasisQ2, BasisQ3, to_coeffs


def _coeff_mv(basis, coeffs):
    return basis.multivector({1 << i: c for i, c in enumerate(coeffs)})


def _circle_matrix():
    return np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])


class TestConicCreate:
    def test_conic_round_trip_ipns(self):
        b = BasisQ2(opns=False)
        mv = _coeff_mv(b, to_coeffs(_circle_matrix()))
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        assert (mv - create(b, raw)).is_zero

    def test_conic_round_trip_opns(self):
        b = BasisQ2(opns=True)
        coeffs = to_coeffs(_circle_matrix())
        mv = _coeff_mv(b, coeffs).undual()  # grade-5 OPNS conic
        raw = analyze(mv)
        assert isinstance(raw, Conic)
        # round-trip is exact up to a global scale/sign
        created = create(b, raw)
        assert (mv + created).is_zero or (mv - created).is_zero

    def test_circle_round_trip(self):
        b = BasisQ2(opns=False)
        circle = Circle(Point(1.0, 2.0, 0.0), 2.0)
        mv = create(b, circle)
        assert isinstance(refine(analyze(mv)), Circle)


class TestQuadricCreate:
    def test_quadric_round_trip_ipns(self):
        b = BasisQ3(opns=False)
        coeffs = tuple(float(i) for i in range(1, 11))
        mv = _coeff_mv(b, coeffs)
        raw = analyze(mv)
        assert isinstance(raw, Quadric3D)
        assert (mv - create(b, raw)).is_zero

    def test_ellipsoid_round_trip(self):
        b = BasisQ3(opns=False)
        ellipsoid = Ellipsoid(Point(1.0, 2.0, 3.0), (2.0, 3.0, 4.0))
        mv = create(b, ellipsoid)
        raw = analyze(mv)
        assert isinstance(raw, Quadric3D)
        refined = refine(raw)
        assert isinstance(refined, Ellipsoid)
        assert refined.center.x == pytest.approx(1.0)
        assert refined.center.y == pytest.approx(2.0)
        assert refined.center.z == pytest.approx(3.0)
        assert sorted(refined.radii, reverse=True) == pytest.approx([4.0, 3.0, 2.0])


class TestRejectUnsupported:
    def test_conic_not_supported_in_e3(self):
        with pytest.raises(TypeError):
            create(BasisE3(), Conic((1.0, 2.0, 3.0, 4.0, 5.0, 6.0)))

    def test_quadric_not_supported_in_q2(self):
        with pytest.raises(TypeError):
            create(BasisQ2(), Quadric3D(tuple(float(i) for i in range(1, 11))))
