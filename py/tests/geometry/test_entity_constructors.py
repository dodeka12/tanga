# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 3 tests — MV-accepting entity constructors."""

from __future__ import annotations

import pytest

from pytanga.basis import BasisE3, BasisN3, BasisP3, BasisPGA3
from pytanga.geometry.create import create_entity
from pytanga.geometry.entities import (
    Circle,
    Direction,
    Line,
    Plane,
    Point,
    Space,
    Sphere,
)


# ═══════════════════════════════════════════════════════════════
# Point / Direction
# ═══════════════════════════════════════════════════════════════


@pytest.mark.parametrize("opns", [True, False])
def test_point_from_n3_mv(opns):
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3), opns=opns)
    p = Point(mv)
    assert p.x == pytest.approx(1)
    assert p.y == pytest.approx(2)
    assert p.z == pytest.approx(3)


def test_point_from_p3_mv():
    alg = BasisP3()
    mv = create_entity(alg, Point(4, 5, 6))
    p = Point(mv)
    assert p.x == pytest.approx(4)
    assert p.y == pytest.approx(5)
    assert p.z == pytest.approx(6)


def test_point_from_pga3_mv():
    alg = BasisPGA3()
    mv = create_entity(alg, Point(7, 8, 9))
    p = Point(mv)
    assert p.x == pytest.approx(7)
    assert p.y == pytest.approx(8)
    assert p.z == pytest.approx(9)


def test_point_rejects_line_mv():
    alg = BasisN3()
    line_mv = create_entity(alg, Line(Point(0, 0, 0), Direction(1, 0, 0)))
    with pytest.raises(TypeError):
        Point(line_mv)


def test_e3_point_convenience():
    alg = BasisE3()
    mv = alg.multivector({1: 1, 2: 2, 4: 3})
    assert Point(mv) == Point(1, 2, 3)


def test_e3_direction_convenience():
    alg = BasisE3()
    mv = alg.multivector({1: 1})
    assert Direction(mv) == Direction(1, 0, 0)


def test_direction_from_p3_mv():
    alg = BasisP3()
    mv = create_entity(alg, Direction(1, 2, 3))
    d = Direction(mv)
    assert isinstance(d, Direction)


# ═══════════════════════════════════════════════════════════════
# Other entities
# ═══════════════════════════════════════════════════════════════


def test_line_from_n3_mv():
    alg = BasisN3()
    mv = create_entity(alg, Line(Point(1, 0, 0), Direction(0, 1, 0)))
    line = Line(mv)
    assert isinstance(line, Line)


def test_line_rejects_point_mv():
    alg = BasisN3()
    point_mv = create_entity(alg, Point(1, 2, 3))
    with pytest.raises(TypeError):
        Line(point_mv)


def test_plane_from_n3_mv():
    alg = BasisN3()
    mv = create_entity(alg, Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    plane = Plane(mv)
    assert isinstance(plane, Plane)


def test_circle_from_n3_mv():
    alg = BasisN3()
    mv = create_entity(alg, Circle(Point(0, 0, 0), 2.0, Direction(0, 0, 1)))
    circle = Circle(mv)
    assert isinstance(circle, Circle)
    assert circle.radius == pytest.approx(2.0)


def test_sphere_from_n3_mv():
    alg = BasisN3()
    mv = create_entity(alg, Sphere(Point(0, 0, 0), 3.0))
    sphere = Sphere(mv)
    assert isinstance(sphere, Sphere)
    assert sphere.radius == pytest.approx(3.0)


def test_space_from_n3_mv():
    alg = BasisN3()
    mv = create_entity(alg, Space(scale=5.0))
    space = Space(mv)
    assert isinstance(space, Space)
    assert space.scale == pytest.approx(5.0, abs=1e-6)


def test_space_rejects_point_mv():
    alg = BasisN3()
    point_mv = create_entity(alg, Point(1, 2, 3))
    with pytest.raises(TypeError):
        Space(point_mv)


# ═══════════════════════════════════════════════════════════════
# Field-level auto-conversion
# ═══════════════════════════════════════════════════════════════


def test_circle_field_auto_conversion():
    alg = BasisN3()
    center_mv = create_entity(alg, Point(1, 2, 3))
    normal_mv = create_entity(alg, Direction(0, 0, 1))
    radius_mv = alg.multivector({0: 2.0})

    circle = Circle(center_mv, radius_mv, normal_mv)
    assert circle.center.x == pytest.approx(1)
    assert circle.center.y == pytest.approx(2)
    assert circle.center.z == pytest.approx(3)
    assert circle.radius == pytest.approx(2.0)
    assert isinstance(circle.normal, Direction)


def test_circle_radius_rejects_non_scalar_mv():
    alg = BasisN3()
    center_mv = create_entity(alg, Point(1, 2, 3))
    nonscalar_mv = create_entity(alg, Direction(0, 0, 1))
    with pytest.raises(ValueError):
        Circle(center_mv, nonscalar_mv, Direction(0, 0, 1))


def test_sphere_field_auto_conversion():
    alg = BasisN3()
    center_mv = create_entity(alg, Point(1, 2, 3))
    radius_mv = alg.multivector({0: 2.5})
    sphere = Sphere(center_mv, radius_mv)
    assert sphere.center.x == pytest.approx(1)
    assert sphere.radius == pytest.approx(2.5)


# ═══════════════════════════════════════════════════════════════
# Line.from_points
# ═══════════════════════════════════════════════════════════════


def test_line_from_points_n3_mvs():
    alg = BasisN3()
    a = create_entity(alg, Point(0, 0, 0))
    b = create_entity(alg, Point(3, 0, 0))
    line = Line.from_points(a, b)
    assert line.origin.x == pytest.approx(0)
    assert line.direction.x == pytest.approx(3)
    assert line.direction.y == pytest.approx(0)
    assert line.direction.z == pytest.approx(0)
    assert line.length == pytest.approx(3)


def test_line_from_points_e3_convenience():
    alg = BasisE3()
    a = alg.multivector({1: 0, 2: 0, 4: 0})
    b = alg.multivector({1: 1})
    line = Line.from_points(a, b)
    assert line.origin.x == pytest.approx(0)
    assert abs(line.direction.x) == pytest.approx(1)


def test_line_from_points_rejects_line_mv():
    alg = BasisN3()
    line_mv = create_entity(alg, Line(Point(0, 0, 0), Direction(1, 0, 0)))
    point_mv = create_entity(alg, Point(1, 2, 3))
    with pytest.raises(TypeError):
        Line.from_points(line_mv, point_mv)