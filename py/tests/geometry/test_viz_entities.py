# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the visualization-only Cylinder and Arc entities."""

from __future__ import annotations

import math

import pytest

from pytanga.basis import BasisN3
from pytanga.geometry import (
    Arc,
    Box,
    Cylinder,
    Direction,
    Disk,
    Ellipse,
    Ellipsoid,
    PartialDisk,
    Point,
    RegularPolygon,
    regular_polygon,
)
from pytanga.geometry.create import create


def test_cylinder_defaults():
    c = Cylinder()
    assert c.origin == Point(0, 0, 0)
    assert c.axis == Direction(0, 0, 1)
    assert c.length == pytest.approx(1.0)
    assert c.radius == pytest.approx(0.1)
    assert c.align_center == pytest.approx(0.0)


def test_cylinder_field_population_and_coercion():
    c = Cylinder(origin=Point(1, 2, 3), axis=Direction(0, 1, 0), length=2, radius=0.4)
    assert c.origin == Point(1, 2, 3)
    assert c.axis == Direction(0, 1, 0)
    assert c.length == pytest.approx(2.0)
    assert c.radius == pytest.approx(0.4)


def test_cylinder_align_center_coercion():
    assert Cylinder().align_center == pytest.approx(0.0)
    assert Cylinder(align_center=0.5).align_center == pytest.approx(0.5)
    assert Cylinder(align_center=1).align_center == pytest.approx(1.0)


def test_arc_defaults():
    a = Arc()
    assert a.origin == Point(0, 0, 0)
    assert a.axis == Direction(0, 0, 1)
    assert a.radius == pytest.approx(1.0)
    assert a.tube_radius == pytest.approx(0.05)
    assert a.angle == pytest.approx(2 * math.pi)


def test_arc_start_direction_auto_computed_orthogonal_and_unit():
    a = Arc(axis=Direction(0, 0, 1))
    assert a.start_direction.mag() == pytest.approx(1.0)
    assert a.start_direction.dot(a.axis.normalized()) == pytest.approx(0.0, abs=1e-12)


def test_arc_start_direction_deterministic():
    a1 = Arc(axis=Direction(1, 2, 3))
    a2 = Arc(axis=Direction(1, 2, 3))
    assert a1.start_direction == a2.start_direction


def test_arc_respects_user_start_direction():
    a = Arc(axis=Direction(0, 0, 1), start_direction=Direction(1, 0, 0))
    assert a.start_direction == Direction(1, 0, 0)


def test_arc_user_start_direction_normalized():
    a = Arc(axis=Direction(0, 0, 1), start_direction=Direction(2, 0, 0))
    assert a.start_direction.mag() == pytest.approx(1.0)
    assert a.start_direction.x == pytest.approx(1.0)


def test_arc_arrow_defaults_off():
    a = Arc()
    assert a.show_arrow is False
    assert a.arrow_length is None
    assert a.arrow_radius is None


def test_arc_arrow_explicit_values():
    a = Arc(show_arrow=True, arrow_length=0.2, arrow_radius=0.1)
    assert a.show_arrow is True
    assert a.arrow_length == pytest.approx(0.2)
    assert a.arrow_radius == pytest.approx(0.1)


def test_arc_arrow_defaults_kept_when_show_arrow_true():
    a = Arc(show_arrow=True)
    assert a.show_arrow is True
    assert a.arrow_length is None
    assert a.arrow_radius is None


def test_cylinder_not_convertible_to_mv():
    alg = BasisN3()
    with pytest.raises(TypeError, match="Expected Entity or Operator"):
        create(alg, Cylinder())



def test_disk_defaults():
    d = Disk()
    assert d.center == Point(0, 0, 0)
    assert d.radius == pytest.approx(1.0)
    assert d.normal == Direction(0, 0, 1)


def test_disk_field_population_and_coercion():
    d = Disk(center=Point(1, 2, 3), radius=2, normal=Direction(0, 1, 0))
    assert d.center == Point(1, 2, 3)
    assert d.radius == pytest.approx(2.0)
    assert d.normal == Direction(0, 1, 0)


def test_partial_disk_defaults():
    p = PartialDisk()
    assert p.center == Point(0, 0, 0)
    assert p.radius == pytest.approx(1.0)
    assert p.angle == pytest.approx(2 * math.pi)
    assert p.normal == Direction(0, 0, 1)


def test_partial_disk_start_direction_auto_computed_orthogonal_and_unit():
    p = PartialDisk(normal=Direction(0, 0, 1))
    assert p.start_direction.mag() == pytest.approx(1.0)
    assert p.start_direction.dot(p.normal.normalized()) == pytest.approx(0.0, abs=1e-12)


def test_partial_disk_start_direction_deterministic():
    p1 = PartialDisk(normal=Direction(1, 2, 3))
    p2 = PartialDisk(normal=Direction(1, 2, 3))
    assert p1.start_direction == p2.start_direction


def test_partial_disk_respects_user_start_direction():
    p = PartialDisk(normal=Direction(0, 0, 1), start_direction=Direction(1, 0, 0))
    assert p.start_direction == Direction(1, 0, 0)


def test_box_defaults():
    b = Box()
    assert b.center == Point(0, 0, 0)
    assert b.size == (1.0, 1.0, 1.0)
    assert b.rotation is None


def test_box_field_population_and_coercion():
    b = Box(center=Point(1, 2, 3), size=(2, 3, 4))
    assert b.center == Point(1, 2, 3)
    assert b.size == (2.0, 3.0, 4.0)


def test_ellipsoid_defaults():
    e = Ellipsoid()
    assert e.center == Point(0, 0, 0)
    assert e.radii == (1.0, 1.0, 1.0)
    assert e.rotation is None


def test_ellipsoid_field_population_and_coercion():
    e = Ellipsoid(center=Point(1, 2, 3), radii=(1, 0.5, 0.75))
    assert e.center == Point(1, 2, 3)
    assert e.radii == (1.0, 0.5, 0.75)


def test_ellipse_defaults():
    e = Ellipse()
    assert e.center == Point(0, 0, 0)
    assert e.radius_u == pytest.approx(1.0)
    assert e.radius_v == pytest.approx(0.5)
    assert e.normal == Direction(0, 0, 1)


def test_regular_polygon_defaults():
    p = RegularPolygon()
    assert p.center == Point(0, 0, 0)
    assert p.radius == pytest.approx(1.0)
    assert p.sides == 6
    assert p.normal == Direction(0, 0, 1)
    assert p.angle == pytest.approx(0.0)


def test_regular_polygon_sides_validated():
    with pytest.raises(ValueError):
        RegularPolygon(sides=2)


def test_regular_polygon_sides_coerced_to_int():
    p = RegularPolygon(sides=6.0)
    assert p.sides == 6
    assert isinstance(p.sides, int)


def test_regular_polygon_factory():
    h = regular_polygon(6)
    assert isinstance(h, RegularPolygon)
    assert h.sides == 6
    assert h.radius == pytest.approx(1.0)


@pytest.mark.parametrize(
    "entity",
    [Disk(), PartialDisk(), Box(), Ellipsoid(), Ellipse(), RegularPolygon()],
)
def test_new_viz_entities_not_convertible_to_mv(entity):
    alg = BasisN3()
    with pytest.raises(TypeError, match="Expected Entity or Operator"):
        create(alg, entity)

def test_arc_not_convertible_to_mv():
    alg = BasisN3()
    with pytest.raises(TypeError, match="Expected Entity or Operator"):
        create(alg, Arc())
