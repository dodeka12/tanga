# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for per-entity label anchor computation (``_label_anchor.py``)."""

import math

import pytest

from pytanga.geometry import Direction, Line, Point
from pytanga.geometry.entities import Circle, Plane, PointPair, Sphere
from pytanga.geometry.operators import Inversion, ReflectionLine
from pytanga.viz._label_anchor import (
    _normalize_along,
    compute_label_anchor,
)


class TestNormalizeAlong:
    def test_scalar(self):
        assert _normalize_along(0.3) == (0.3, 0.0, 0.0)

    def test_two_tuple(self):
        assert _normalize_along((0.1, 0.2)) == (0.1, 0.2, 0.0)

    def test_three_tuple(self):
        assert _normalize_along((0.1, 0.2, 0.3)) == (0.1, 0.2, 0.3)

    def test_none(self):
        assert _normalize_along(None) is None

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError):
            _normalize_along((0.1, 0.2, 0.3, 0.4))


class TestLineAnchor:
    def test_default_midpoint(self):
        line = Line.from_points(Point(0, 0, 0), Point(4, 0, 0))
        assert compute_label_anchor(line) == (2.0, 0.0, 0.0)

    def test_along_start(self):
        line = Line.from_points(Point(0, 0, 0), Point(4, 0, 0))
        assert compute_label_anchor(line, along=0) == (0.0, 0.0, 0.0)

    def test_along_end(self):
        line = Line.from_points(Point(0, 0, 0), Point(4, 0, 0))
        assert compute_label_anchor(line, along=1) == (4.0, 0.0, 0.0)

    def test_infinite_line_uses_resolved_length(self):
        line = Line(Point(0, 0, 0), Direction(1, 0, 0))
        assert compute_label_anchor(line, line_length=20.0) == (10.0, 0.0, 0.0)

    def test_infinite_line_default_length(self):
        line = Line(Point(0, 0, 0), Direction(1, 0, 0))
        assert compute_label_anchor(line) == (10.0, 0.0, 0.0)

    def test_reflection_line(self):
        rl = ReflectionLine(Line.from_points(Point(0, 0, 0), Point(6, 0, 0)))
        assert compute_label_anchor(rl) == (3.0, 0.0, 0.0)


class TestOtherAnchors:
    def test_direction_default_origin(self):
        assert compute_label_anchor(Direction(1, 0, 0)) == (0.0, 0.0, 0.0)

    def test_direction_along_tip(self):
        assert compute_label_anchor(Direction(1, 0, 0), along=1) == (2.0, 0.0, 0.0)

    def test_point_pair_default_midpoint(self):
        pp = PointPair(Point(0, 0, 0), Point(2, 0, 0))
        assert compute_label_anchor(pp) == (0.0, 0.0, 0.0)

    def test_point_pair_along_endpoints(self):
        pp = PointPair(Point(0, 0, 0), Point(2, 0, 0))
        assert compute_label_anchor(pp, along=0) == (-1.0, 0.0, 0.0)
        assert compute_label_anchor(pp, along=1) == (1.0, 0.0, 0.0)

    def test_circle_default_center(self):
        assert compute_label_anchor(Circle(Point(1, 2, 3), 2.0)) == (0.0, 0.0, 0.0)

    def test_circle_rim(self):
        c = Circle(Point(0, 0, 0), 2.0)
        x, y, z = compute_label_anchor(c, along=(0.25, 1.0))
        assert math.sqrt(x * x + y * y + z * z) == pytest.approx(2.0)

    def test_sphere_default_center(self):
        assert compute_label_anchor(Sphere(Point(1, 2, 3), 2.0)) == (0.0, 0.0, 0.0)

    def test_sphere_pole(self):
        s = Sphere(Point(0, 0, 0), 3.0)
        assert compute_label_anchor(s, along=(1, 0, 0)) == (0.0, 0.0, 3.0)

    def test_plane_default_point(self):
        p = Plane(Point(0, 0, 0), Direction(0, 0, 1))
        assert compute_label_anchor(p) == (0.0, 0.0, 0.0)

    def test_inversion_uses_sphere_anchor(self):
        inv = Inversion(Point(0, 0, 0), 2.0)
        assert compute_label_anchor(inv, along=(1, 0, 0)) == (0.0, 0.0, 2.0)

    def test_unregistered_entity_is_origin(self):
        assert compute_label_anchor(Point(3, 3, 3)) == (0.0, 0.0, 0.0)
