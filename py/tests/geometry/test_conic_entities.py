# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the conic/quadric entity dataclasses."""

import numpy as np
import pytest

from pytanga.geometry import (
    Conic,
    Direction,
    EConicKind,
    EQuadricKind,
    Hyperbola,
    Line,
    LinePair,
    ParallelLinePair,
    Parabola,
    Point,
    PointSet,
    Quadric2D,
    Quadric3D,
)
from pytanga.quadric import to_coeffs


def _circle_matrix():
    # (x - 1)^2 + (y - 2)^2 = 4
    return np.array([[1.0, 0.0, -1.0], [0.0, 1.0, -2.0], [-1.0, -2.0, 1.0]])


def _ellipsoid_matrix():
    # x^2/4 + y^2/9 + z^2/16 = 1
    return np.diag([0.25, 1.0 / 9.0, 1.0 / 16.0, -1.0])


def _sphere_matrix():
    # (x - 1)^2 + (y - 2)^2 + (z - 3)^2 = 4
    return np.array(
        [
            [1.0, 0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0, -2.0],
            [0.0, 0.0, 1.0, -3.0],
            [-1.0, -2.0, -3.0, 10.0],
        ]
    )


def _assert_point(p, x, y, z):
    assert p.x == pytest.approx(x)
    assert p.y == pytest.approx(y)
    assert p.z == pytest.approx(z)


class TestEnums:
    def test_conic_kind_values(self):
        assert EConicKind.circle.value == "circle"
        assert EConicKind.parallel_line_pair.value == "parallel_line_pair"

    def test_quadric_kind_values(self):
        assert EQuadricKind.ellipsoid.value == "ellipsoid"
        assert EQuadricKind.hyperboloid_1s.value == "hyperboloid_1s"


class TestConic:
    def test_constructor_coerces_to_tuple(self):
        c = Conic([1, 2, 3, 4, 5, 6])
        assert c.coeffs == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)

    def test_constructor_rejects_wrong_length(self):
        with pytest.raises(ValueError):
            Conic((1, 2, 3, 4, 5))

    def test_repr(self):
        assert "Conic" in repr(Conic((1, 2, 3, 4, 5, 6)))

    def test_circle_derived_properties(self):
        c = Conic(to_coeffs(_circle_matrix()))
        assert c.kind is EConicKind.circle
        assert c.rank == 3
        assert c.signature == (2, 1, 0)
        _assert_point(c.center, 1.0, 2.0, 0.0)
        assert c.eigenvalues == pytest.approx((1.0, 1.0))
        assert c.rho == pytest.approx(2.0)

    def test_circle_principal_directions_are_orthonormal(self):
        c = Conic(to_coeffs(_circle_matrix()))
        d1, d2 = c.principal_directions
        assert d1.mag() == pytest.approx(1.0)
        assert d2.mag() == pytest.approx(1.0)
        assert d1.dot(d2) == pytest.approx(0.0)

    def test_quadric2d_alias(self):
        assert Quadric2D is Conic


class TestQuadric3D:
    def test_constructor_rejects_wrong_length(self):
        with pytest.raises(ValueError):
            Quadric3D((1, 2, 3, 4, 5, 6, 7, 8, 9))

    def test_ellipsoid_derived_properties(self):
        q = Quadric3D(to_coeffs(_ellipsoid_matrix()))
        assert q.kind is EQuadricKind.ellipsoid
        assert q.rank == 4
        assert q.signature == (3, 1, 0)
        _assert_point(q.center, 0.0, 0.0, 0.0)
        assert q.eigenvalues == pytest.approx((1.0 / 16.0, 1.0 / 9.0, 1.0 / 4.0))
        assert q.rho is None

    def test_sphere_derived_properties(self):
        q = Quadric3D(to_coeffs(_sphere_matrix()))
        assert q.kind is EQuadricKind.sphere
        _assert_point(q.center, 1.0, 2.0, 3.0)
        assert q.rho == pytest.approx(2.0)


class TestConicEntities:
    def test_hyperbola(self):
        h = Hyperbola(
            Point(1.0, 2.0, 0.0),
            Direction(1.0, 0.0, 0.0),
            Direction(0.0, 1.0, 0.0),
            2.0,
            1.0,
        )
        assert h.a == 2.0
        assert h.b == 1.0
        assert h.center == Point(1.0, 2.0, 0.0)
        assert "Hyperbola" in repr(h)

    def test_parabola(self):
        p = Parabola(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0), 1.5)
        assert p.p == 1.5
        assert p.vertex == Point(0.0, 0.0, 0.0)
        assert "Parabola" in repr(p)

    def test_line_pair(self):
        l1 = Line(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0))
        l2 = Line(Point(0.0, 1.0, 0.0), Direction(0.0, 1.0, 0.0))
        lp = LinePair(l1, l2)
        assert lp.line1 is l1
        assert lp.line2 is l2
        assert "LinePair" in repr(lp)

    def test_parallel_line_pair_is_distinct(self):
        l1 = Line(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0))
        l2 = Line(Point(0.0, 1.0, 0.0), Direction(1.0, 0.0, 0.0))
        plp = ParallelLinePair(l1, l2)
        assert isinstance(plp, LinePair)
        assert type(plp) is ParallelLinePair
        assert "ParallelLinePair" in repr(plp)

    def test_point_set(self):
        pts = PointSet([Point(1.0, 2.0, 3.0), Point(4.0, 5.0, 6.0)], kind="pair")
        assert len(pts) == 2
        assert pts.kind == "pair"
        assert pts[0] == Point(1.0, 2.0, 3.0)
        assert list(pts) == [Point(1.0, 2.0, 3.0), Point(4.0, 5.0, 6.0)]
