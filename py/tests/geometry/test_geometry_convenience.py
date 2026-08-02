# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the Geometry convenience class."""

from __future__ import annotations

import math

import pytest
from pytanga.algebra._algebra import Algebra
from pytanga.geometry import Geometry
from pytanga.geometry.entities import Direction, Point, Sphere
from pytanga.geometry.operators import Rotor


@pytest.fixture(scope="module")
def b():
    return Algebra.from_name("N3")


# ═══ Construction ═══


def test_geometry_algebra_is_read_only(b):
    geo = Geometry(b)
    assert geo.algebra is b
    with pytest.raises(AttributeError):
        geo.algebra = b  # type: ignore[misc]


def test_geometry_default_opns_true(b):
    assert Geometry(b).opns is True


def test_geometry_explicit_opns(b):
    assert Geometry(b, opns=False).opns is False


def test_geometry_importable():
    from pytanga import geometry

    assert hasattr(geometry, "Geometry")


# ═══ create() ═══


def test_create_uses_default_opns(b):
    geo = Geometry(b, opns=True)
    mv = geo.create(Point(1, 2, 3))
    # OPNS point is grade-1
    assert 1 in mv.grades


def test_create_override_opns(b):
    geo = Geometry(b, opns=True)
    mv = geo.create(Sphere(Point(0, 0, 0), 3.0), opns=False)
    # IPNS sphere is grade-1
    assert max(mv.grades) == 1


def test_create_with_opns_false_default(b):
    geo = Geometry(b, opns=False)
    mv = geo.create(Point(1, 2, 3))
    # IPNS point is grade-4 (dual of grade-1 point)
    assert 4 in mv.grades


def test_create_opns_can_be_changed(b):
    geo = Geometry(b, opns=True)
    geo.opns = False
    mv = geo.create(Point(1, 2, 3))
    assert 4 in mv.grades


# ═══ which_entity() ═══


def test_which_entity_round_trip(b):
    geo = Geometry(b, opns=True)
    sphere = Sphere(Point(1, 2, 3), 2.0)
    mv = geo.create(sphere)
    result = geo.which_entity(mv)
    assert isinstance(result, Sphere)
    assert result.center.x == pytest.approx(1, abs=1e-4)
    assert result.radius == pytest.approx(2, abs=1e-4)


def test_which_entity_override_opns(b):
    geo = Geometry(b, opns=False)
    mv = geo.create(Point(0, 0, 5), opns=False)
    # Analyze with matching opns
    result = geo.which_entity(mv)
    assert isinstance(result, Point)


# ═══ which_operator() ═══


def test_which_operator_round_trip(b):
    geo = Geometry(b)
    rotor = Rotor(math.pi / 3, Direction(1, 0, 0))
    mv = geo.create(rotor)
    result = geo.which_operator(mv)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(math.pi / 3, abs=1e-6)


def test_which_operator_does_not_accept_opns(b):
    geo = Geometry(b)
    rotor_mv = geo.create(Rotor(0.5, Direction(0, 0, 1)))
    # which_operator should work without opns param
    result = geo.which_operator(rotor_mv)
    assert isinstance(result, Rotor)
