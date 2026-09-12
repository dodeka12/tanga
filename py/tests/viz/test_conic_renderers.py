# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the 2D conic curve renderer serializers."""

from pytanga.geometry import (
    Cone,
    Direction,
    Hyperbola,
    Line,
    LinePair,
    Parabola,
    ParallelLinePair,
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
        # Member lines are centered on their point: origin == point - d̂·length/2.
        assert d["line1"]["origin"] == [-10.0, 0.0, 0.0]
        assert d["line1"]["direction"] == [1.0, 0.0, 0.0]
        assert d["line1"]["length"] == 20.0
        assert d["line2"]["origin"] == [0.0, -9.0, 0.0]
        assert d["line2"]["direction"] == [0.0, 1.0, 0.0]

    def test_serialize_point_set(self):
        ps = PointSet([Point(1.0, 2.0, 3.0), Point(4.0, 5.0, 6.0)], kind="pair")
        d = serialize_entity(ps, "ps1", kind="PointSet")
        assert d["kind"] == "PointSet"
        assert d["points"] == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        assert d["pointKind"] == "pair"

    def test_serialize_ellipse_line(self):
        e = Ellipse(radius_u=2.0, radius_v=1.0)
        d = serialize_entity(e, "el1", kind="Ellipse")
        assert d["kind"] == "Ellipse"
        assert d["radiusU"] == 2.0
        assert d["radiusV"] == 1.0
        assert d["style"]["thickness"] == 1.0
        for key in ("wireframe", "wireframe_dash", "wireframe_color", "wireframe_opacity"):
            assert key not in d
            assert key not in d["style"]

    def test_serialize_ellipse_directions(self):
        e = Ellipse(
            radius_u=2.0,
            radius_v=1.0,
            dir_u=Direction(1.0, 0.0, 0.0),
            dir_v=Direction(0.0, 1.0, 0.0),
        )
        d = serialize_entity(e, "el2", kind="Ellipse")
        assert d["dirU"] == [1.0, 0.0, 0.0]
        assert d["dirV"] == [0.0, 1.0, 0.0]

    def test_serialize_parallel_line_pair(self):
        l1 = Line(Point(0.0, 0.0, 0.0), Direction(1.0, 0.0, 0.0))
        l2 = Line(Point(0.0, 1.0, 0.0), Direction(1.0, 0.0, 0.0))
        plp = ParallelLinePair(l1, l2)
        d = serialize_entity(plp, "plp1", kind="ParallelLinePair")
        assert d["kind"] == "ParallelLinePair"
        assert d["line1"]["origin"] == [-10.0, 0.0, 0.0]
        assert d["line2"]["origin"] == [-10.0, 1.0, 0.0]
        assert d["line1"]["length"] == 20.0

    def test_extent_defaults(self):
        from pytanga.viz._styles import _DEFAULT_STYLE_FOR_KIND

        assert _DEFAULT_STYLE_FOR_KIND["Hyperbola"].extent == 5.0
        assert _DEFAULT_STYLE_FOR_KIND["Parabola"].extent == 5.0

    def test_serialize_cone(self):
        c = Cone(Point(0.0, 0.0, 0.0), Direction(0.0, 0.0, 1.0), 0.5)
        d = serialize_entity(c, "c1", kind="Cone")
        assert d["kind"] == "Cone"
        assert d["vertex"] == [0.0, 0.0, 0.0]
        assert d["axis"] == [0.0, 0.0, 1.0]
        assert d["halfAngle"] == 0.5


import numpy as np

from pytanga.geometry import Conic, Ellipse, Quadric3D
from pytanga.quadric import to_coeffs
from pytanga.viz import ConicStyle
from pytanga.viz._styles import _style_to_output
from pytanga.viz.scene import _resolve_scene_entity


class TestConicRefineInResolver:
    def test_resolve_refines_conic_to_ellipse(self):
        # x²/4 + y² = 1  ->  symmetric matrix diag(1/4, 1, -1).
        matrix = np.diag([1.0 / 4.0, 1.0, -1.0])
        conic = Conic(to_coeffs(matrix))
        resolved = _resolve_scene_entity(conic)
        assert isinstance(resolved, Ellipse)

    def test_resolve_leaves_quadric3d_unchanged(self):
        q = Quadric3D(tuple(float(i) for i in range(1, 11)))
        assert _resolve_scene_entity(q) is q

    def test_resolve_refines_mv_analyzing_to_conic(self):
        # An MV (grade-1 IPNS conic) must also be refined via analyze().
        from pytanga.quadric import BasisQ2

        matrix = np.diag([1.0 / 4.0, 1.0, -1.0])
        basis = BasisQ2(opns=False)
        coeffs = to_coeffs(matrix)
        mv = basis.multivector({1 << i: coeffs[i] for i in range(6)})
        resolved = _resolve_scene_entity(mv)
        assert isinstance(resolved, Ellipse)

    def test_conic_style_merges_over_refined_default(self):
        merged = _style_to_output(ConicStyle(color="#123456"), "Ellipse")
        assert merged["color"] == "#123456"
        assert merged["thickness"] == 1.0

