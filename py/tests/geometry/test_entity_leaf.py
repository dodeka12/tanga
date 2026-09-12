# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the leaf ``pytanga.entity`` module (Point/Direction parity)."""

import pytest

from pytanga.entity import Direction, Point, Vec3


def test_point_typed_arithmetic():
    p = Point(1, 2, 3)
    assert p + Point(4, 5, 6) == Point(5, 7, 9)
    assert p + Direction(1, 0, 0) == Point(2, 2, 3)
    assert Direction(1, 0, 0) + p == Point(2, 2, 3)
    d = p - Point(0, 0, 0)
    assert isinstance(d, Direction) and d == Direction(1, 2, 3)
    assert p - Direction(1, 0, 0) == Point(0, 2, 3)
    assert isinstance(p.cross(Direction(1, 0, 0)), Direction)
    assert isinstance(p.normalized(), Point)


def test_point_repr_and_eq():
    p = Point(1, 2, 3)
    assert repr(p) == "Point(1.00, 2.00, 3.00)"
    assert p == (1, 2, 3)
    assert p == [1, 2, 3]


def test_direction_typed_arithmetic():
    v = Direction(1, 2, 3)
    assert v + Direction(1, 1, 1) == Direction(2, 3, 4)
    assert v - Direction(1, 1, 1) == Direction(0, 1, 2)
    assert isinstance(v.cross(Direction(1, 0, 0)), Direction)
    assert isinstance(v.normalized(), Direction)


def test_direction_repr_and_eq():
    v = Direction(1, 2, 3)
    assert repr(v) == "Dir(1.00, 2.00, 3.00)"
    assert v == (1, 2, 3)


def test_to_vec3_roundtrip():
    p = Point(1, 2, 3)
    assert p.to_vec3() == Vec3(1, 2, 3)
    assert p.to_vec3().to_point() == p
    v = Direction(1, 2, 3)
    assert v.to_vec3() == Vec3(1, 2, 3)
    assert v.to_vec3().to_direction() == v


def test_point_and_direction_are_vec3():
    assert isinstance(Point(1, 2, 3), Vec3)
    assert isinstance(Direction(1, 2, 3), Vec3)


def test_hashable():
    assert hash(Point(1, 2, 3)) == hash(Point(1, 2, 3))
    assert hash(Direction(1, 2, 3)) == hash(Direction(1, 2, 3))


def test_frozen():
    p = Point(1, 2, 3)
    with pytest.raises(AttributeError):
        p.x = 5.0


def test_mv_to_point_conversion():
    import pytanga.geometry  # noqa: F401  (populates the analyzer registry)

    from pytanga.basis.e3 import BasisE3
    from pytanga.geometry import Point as GPoint

    mv = BasisE3().multivector({1: 1.0, 2: 2.0, 4: 3.0})
    assert GPoint(mv) == Point(1, 2, 3)
