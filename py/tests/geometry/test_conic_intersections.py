# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for PointSet analysis and 2D two-conic intersection."""

import numpy as np
import pytest

from pytanga.geometry import (
    PointSet,
    analyze_entity,
    two_conic_intersection,
)
from pytanga.quadric import BasisQ2, BasisQ3, embed_point

_SQRT3_2 = np.sqrt(3.0) / 2.0


def _sorted_pts(ps):
    return sorted(ps, key=lambda p: (p.x, p.y, p.z))


class TestTwoConicIntersection:
    def test_two_circles(self):
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
        ps = two_conic_intersection(a, b)
        assert len(ps) == 2
        pts = _sorted_pts(ps)
        assert pts[0].x == pytest.approx(0.5)
        assert pts[0].y == pytest.approx(-_SQRT3_2)
        assert pts[1].x == pytest.approx(0.5)
        assert pts[1].y == pytest.approx(_SQRT3_2)

    def test_two_ellipses_four_points(self):
        a = np.diag([0.25, 1.0, -1.0])
        b = np.diag([1.0, 0.25, -1.0])
        ps = two_conic_intersection(a, b)
        assert len(ps) == 4

    def test_tangency_single_point(self):
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -2.0], [0.0, 1.0, 0.0], [-2.0, 0.0, 3.0]])
        ps = two_conic_intersection(a, b)
        assert len(ps) == 1
        assert ps[0].x == pytest.approx(1.0, abs=1e-3)
        assert abs(ps[0].y) < 1e-3

    def test_disjoint_empty(self):
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -10.0], [0.0, 1.0, 0.0], [-10.0, 0.0, 99.0]])
        ps = two_conic_intersection(a, b)
        assert len(ps) == 0


class TestPointSetJoin:
    def test_q2_join_of_two_points(self):
        b = BasisQ2()
        blade = embed_point(b, 1.0, 2.0) ^ embed_point(b, 3.0, 4.0)
        ps = analyze_entity(blade)
        assert isinstance(ps, PointSet)
        assert len(ps) == 2
        assert set((round(p.x, 6), round(p.y, 6)) for p in ps) == {
            (1.0, 2.0),
            (3.0, 4.0),
        }

    def test_q2_join_of_three_points(self):
        b = BasisQ2()
        p1 = embed_point(b, 0.0, 0.0)
        p2 = embed_point(b, 1.0, 0.0)
        p3 = embed_point(b, 0.0, 1.0)
        ps = analyze_entity(p1 ^ p2 ^ p3)
        assert len(ps) == 3

    def test_q2_join_of_four_points(self):
        b = BasisQ2()
        p1 = embed_point(b, 0.0, 0.0)
        p2 = embed_point(b, 1.0, 0.0)
        p3 = embed_point(b, 0.0, 1.0)
        p4 = embed_point(b, 1.0, 1.0)
        ps = analyze_entity(p1 ^ p2 ^ p3 ^ p4)
        assert len(ps) == 4

    def test_q3_join_of_two_points(self):
        b = BasisQ3()
        blade = embed_point(b, 1.0, 2.0, 3.0) ^ embed_point(b, 4.0, 5.0, 6.0)
        ps = analyze_entity(blade)
        assert isinstance(ps, PointSet)
        assert len(ps) == 2
        assert set((round(p.x, 6), round(p.y, 6), round(p.z, 6)) for p in ps) == {
            (1.0, 2.0, 3.0),
            (4.0, 5.0, 6.0),
        }

    def test_q3_ipns_intersection_deferred(self):
        b = BasisQ3(opns=False)
        q1 = b.multivector({1 << i: 1.0 for i in range(10)})
        q2 = b.multivector({1 << i: float(i) for i in range(10)})
        blade = q1 ^ q2
        with pytest.raises(NotImplementedError):
            analyze_entity(blade)
