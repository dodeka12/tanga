# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the 2D conic curve renderer serializers."""

from pytanga.geometry import (
    Direction,
    Hyperbola,
    Line,
    LinePair,
    Parabola,
    Point,
    PointSet,
)
from pytanga.viz.serializer import serialize_entity


class TestConicRenderers:
    def test_serialize_hyperbola(self):
        h = Hyperbola(
            Point(1.0, 2.0, 0.0),
            Direction(1.0, 0.0, 0.0),
            Direction(0.0, 1.0, 0.0),
            2.0,
            1.0,
        )
        d = serialize_entity(h, "h1", kind="Hyperbola")
        assert d["kind"] == "Hyperbola"
        assert d["center"] == [1.0, 2.0, 0.0]
        assert d["dir1"] == [1.0, 0.0, 0.0]
        assert d["dir2"] == [0.0, 1.0, 0.0]
        assert d["a"] == 2.0
        assert d["b"] == 1.0

    def test_serialize_parabola(self):
        p = Parabola(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0), 1.5)
        d = serialize_entity(p, "p1", kind="Parabola")
        assert d["kind"] == "Parabola"
        assert d["vertex"] == [0.0, 0.0, 0.0]
        assert d["direction"] == [1.0, 0.0, 0.0]
        assert d["p"] == 1.5

    def test_serialize_line_pair(self):
        l1 = Line(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0))
        l2 = Line(Point(0.0, 1.0, 0.0), Direction(0.0, 1.0, 0.0))
        lp = LinePair(l1, l2)
        d = serialize_entity(lp, "lp1", kind="LinePair")
        assert d["kind"] == "LinePair"
        assert d["line1"]["origin"] == [0.0, 0.0, 0.0]
        assert d["line1"]["direction"] == [1.0, 0.0, 0.0]
        assert d["line2"]["origin"] == [0.0, 1.0, 0.0]
        assert d["line2"]["direction"] == [0.0, 1.0, 0.0]

    def test_serialize_point_set(self):
        ps = PointSet([Point(1.0, 2.0, 3.0), Point(4.0, 5.0, 6.0)], kind="pair")
        d = serialize_entity(ps, "ps1", kind="PointSet")
        assert d["kind"] == "PointSet"
        assert d["points"] == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        assert d["pointKind"] == "pair"
