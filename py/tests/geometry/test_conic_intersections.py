# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for PointSet analysis and 2D two-conic intersection."""

import numpy as np
import pytest

from pytanga.geometry import (
    Curve,
    PlaneConicPair,
    PointSet,
    analyze_entity,
)
from pytanga.quadric import BasisQ2, BasisQ3
from pytanga.quadric._embedding import _embed_point
from pytanga.quadric._pointset import _two_conic_intersection

_SQRT3_2 = np.sqrt(3.0) / 2.0


def _sorted_pts(ps):  # noqa: ANN001, ANN202
    return sorted(ps, key=lambda p: (p.x, p.y, p.z))


class TestTwoConicIntersection:
    def test_two_circles(self):  # noqa: ANN201
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
        ps = _two_conic_intersection(a, b)
        assert len(ps) == 2
        pts = _sorted_pts(ps)
        assert pts[0].x == pytest.approx(0.5)
        assert pts[0].y == pytest.approx(-_SQRT3_2)
        assert pts[1].x == pytest.approx(0.5)
        assert pts[1].y == pytest.approx(_SQRT3_2)

    def test_two_ellipses_four_points(self):  # noqa: ANN201
        a = np.diag([0.25, 1.0, -1.0])
        b = np.diag([1.0, 0.25, -1.0])
        ps = _two_conic_intersection(a, b)
        assert len(ps) == 4

    def test_tangency_single_point(self):  # noqa: ANN201
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -2.0], [0.0, 1.0, 0.0], [-2.0, 0.0, 3.0]])
        ps = _two_conic_intersection(a, b)
        assert len(ps) == 1
        assert ps[0].x == pytest.approx(1.0, abs=1e-3)
        assert abs(ps[0].y) < 1e-3

    def test_disjoint_empty(self):  # noqa: ANN201
        a = np.diag([1.0, 1.0, -1.0])
        b = np.array([[1.0, 0.0, -10.0], [0.0, 1.0, 0.0], [-10.0, 0.0, 99.0]])
        ps = _two_conic_intersection(a, b)
        assert len(ps) == 0


class TestPointSetJoin:
    def test_q2_join_of_two_points(self):  # noqa: ANN201
        b = BasisQ2()
        blade = _embed_point(b, 1.0, 2.0) ^ _embed_point(b, 3.0, 4.0)
        ps = analyze_entity(blade)
        assert isinstance(ps, PointSet)
        assert len(ps) == 2
        assert set((round(p.x, 6), round(p.y, 6)) for p in ps) == {
            (1.0, 2.0),
            (3.0, 4.0),
        }

    def test_q2_join_of_three_points(self):  # noqa: ANN201
        b = BasisQ2()
        p1 = _embed_point(b, 0.0, 0.0)
        p2 = _embed_point(b, 1.0, 0.0)
        p3 = _embed_point(b, 0.0, 1.0)
        ps = analyze_entity(p1 ^ p2 ^ p3)
        assert len(ps) == 3

    def test_q2_join_of_four_points(self):  # noqa: ANN201
        b = BasisQ2()
        p1 = _embed_point(b, 0.0, 0.0)
        p2 = _embed_point(b, 1.0, 0.0)
        p3 = _embed_point(b, 0.0, 1.0)
        p4 = _embed_point(b, 1.0, 1.0)
        ps = analyze_entity(p1 ^ p2 ^ p3 ^ p4)
        assert len(ps) == 4

    def test_q3_join_of_two_points(self):  # noqa: ANN201
        b = BasisQ3()
        blade = _embed_point(b, 1.0, 2.0, 3.0) ^ _embed_point(b, 4.0, 5.0, 6.0)
        ps = analyze_entity(blade)
        assert isinstance(ps, PointSet)
        assert len(ps) == 2
        assert set((round(p.x, 6), round(p.y, 6), round(p.z, 6)) for p in ps) == {
            (1.0, 2.0, 3.0),
            (4.0, 5.0, 6.0),
        }

    def test_q3_ipns_intersection(self):  # noqa: ANN201
        b = BasisQ3(opns=False)
        q1 = b.multivector({1 << i: 1.0 for i in range(10)})
        q2 = b.multivector({1 << i: float(i) for i in range(10)})
        blade = q1 ^ q2
        result = analyze_entity(blade)
        assert isinstance(result, (PlaneConicPair, Curve))


_Q3_PTS = [
    (0.1, 0.2, 0.3),
    (0.9, 0.1, -0.2),
    (-0.4, 0.7, 0.1),
    (0.3, -0.5, 0.8),
    (-0.6, -0.3, 0.5),
    (0.8, 0.6, -0.7),
    (-0.9, 0.5, -0.4),
]


def _join_q3(b, pts):  # noqa: ANN001, ANN202
    mv = _embed_point(b, *pts[0])
    for p in pts[1:]:
        mv = mv ^ _embed_point(b, *p)
    return mv


def _assert_recovers(ps, pts):  # noqa: ANN001, ANN202
    for p in pts:
        assert any(
            abs(round(q.x, 5) - round(p[0], 5)) < 1e-4
            and abs(round(q.y, 5) - round(p[1], 5)) < 1e-4
            and abs(round(q.z, 5) - round(p[2], 5)) < 1e-4
            for q in ps
        ), f"point {p} not recovered in {ps}"


class TestQ3PointTuples:
    def test_join_of_three_points(self):  # noqa: ANN201
        b = BasisQ3()
        ps = analyze_entity(_join_q3(b, _Q3_PTS[:3]))
        assert len(ps) == 3
        _assert_recovers(ps, _Q3_PTS[:3])

    def test_join_of_four_points(self):  # noqa: ANN201
        b = BasisQ3()
        ps = analyze_entity(_join_q3(b, _Q3_PTS[:4]))
        assert len(ps) == 4
        _assert_recovers(ps, _Q3_PTS[:4])

    def test_join_of_five_points(self):  # noqa: ANN201
        b = BasisQ3()
        ps = analyze_entity(_join_q3(b, _Q3_PTS[:5]))
        assert len(ps) == 5
        _assert_recovers(ps, _Q3_PTS[:5])

    def test_join_of_six_points(self):  # noqa: ANN201
        b = BasisQ3()
        ps = analyze_entity(_join_q3(b, _Q3_PTS[:6]))
        assert len(ps) == 6
        _assert_recovers(ps, _Q3_PTS[:6])

    def test_join_of_seven_points_yields_eight_base_points(self):  # noqa: ANN201
        # A 7-point join in Q3 spans a P6 that meets the Veronese 3-fold in
        # eight rank-1 points (the 7 originals + 1 Cayley-Bacharach point).
        b = BasisQ3()
        ps = analyze_entity(_join_q3(b, _Q3_PTS[:7]))
        assert len(ps) == 8
        _assert_recovers(ps, _Q3_PTS[:7])

    def test_ipns_point_tuple_dualizes_to_opns(self):  # noqa: ANN201
        # IPNS grade 3 is the net of quadrics through 7 points; dualizing it
        # yields the OPNS grade-7 join, whose base points are recovered.
        b = BasisQ3()
        join = _join_q3(b, _Q3_PTS[:7])
        net = join.dual()  # grade 3
        b.opns = False
        ps = analyze_entity(net)
        assert len(ps) == 8
        _assert_recovers(ps, _Q3_PTS[:7])
