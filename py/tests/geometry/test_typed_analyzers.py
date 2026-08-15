# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 2 tests — typed per-entity analyzers."""

from __future__ import annotations

import pytest

from pytanga.basis import (
    BasisE2,
    BasisE3,
    BasisN2,
    BasisN3,
    BasisP2,
    BasisP3,
    BasisPGA2,
    BasisPGA3,
)
from pytanga.geometry import analysis
from pytanga.geometry.create import create_entity
from pytanga.geometry.entities import (
    Circle,
    Direction,
    HDirection,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)


def _point(p):
    return Point(p[0], p[1], p[2])


# ═══════════════════════════════════════════════════════════════
# Round-trip tests: create_entity + typed analyzer reproduces entity.
# ═══════════════════════════════════════════════════════════════


@pytest.mark.parametrize("opns", [True, False])
def test_p3_point_round_trip(opns):
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_p3_direction_round_trip(opns):
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Direction(1, 2, 3))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


@pytest.mark.parametrize("opns", [True, False])
def test_p3_line_round_trip(opns):
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Line(Point(1, 0, 0), Direction(0, 1, 0)))
    r = analysis.analyze_line(mv)
    assert isinstance(r, Line)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_point_round_trip(opns):
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_circle_round_trip(opns):
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Circle(Point(1, 2, 3), 2.0, Direction(0, 0, 1)))
    r = analysis.analyze_circle(mv)
    assert isinstance(r, Circle)
    assert r.radius == pytest.approx(2.0)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_sphere_round_trip(opns):
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Sphere(Point(1, 0, 0), 2.0))
    r = analysis.analyze_sphere(mv)
    assert isinstance(r, Sphere)
    assert r.radius == pytest.approx(2.0)


@pytest.mark.parametrize("opns", [True, False])
def test_pga3_point_round_trip(opns):
    alg = BasisPGA3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_pga3_plane_round_trip(opns):
    alg = BasisPGA3(opns=opns)
    mv = create_entity(alg, Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    r = analysis.analyze_plane(mv)
    assert isinstance(r, Plane)


def test_e3_direction_round_trip():
    alg = BasisE3()
    mv = create_entity(alg, Direction(1, 2, 3))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


@pytest.mark.parametrize("opns", [True, False])
def test_e3_plane_round_trip(opns):
    alg = BasisE3(opns=opns)
    mv = create_entity(alg, Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    r = analysis.analyze_plane(mv)
    assert isinstance(r, Plane)


@pytest.mark.parametrize("opns", [True, False])
def test_e2_direction_round_trip(opns):
    alg = BasisE2(opns=opns)
    mv = create_entity(alg, Direction(1, 2, 0))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


# ═══════════════════════════════════════════════════════════════
# Mismatch tests
# ═══════════════════════════════════════════════════════════════


def test_analyze_point_rejects_line():
    alg = BasisP3()
    line_mv = create_entity(alg, Line(Point(0, 0, 0), Direction(1, 0, 0)))
    with pytest.raises(TypeError, match="Expected a Point"):
        analysis.analyze_point(line_mv)


def test_analyze_space_rejects_point():
    alg = BasisP3()
    point_mv = create_entity(alg, Point(1, 2, 3))
    with pytest.raises(TypeError, match="Expected a Space"):
        analysis.analyze_space(point_mv)


def test_analyze_point_unsupported_in_e3():
    alg = BasisE3()
    mv = alg.multivector({1: 1.0})
    with pytest.raises(TypeError, match="not supported in e3"):
        analysis.analyze_point(mv)


def test_analyze_plane_unsupported_in_e2():
    alg = BasisE2()
    mv = alg.multivector({1: 1.0})
    with pytest.raises(TypeError, match="not supported in e2"):
        analysis.analyze_plane(mv)


def test_ipns_mode_round_trip():
    alg = BasisN3()
    alg.opns = False
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)