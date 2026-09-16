# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 2 tests — typed per-entity analyzers."""

from __future__ import annotations

import math

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
from pytanga.geometry.create import create_entity, create_operator
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
from pytanga.geometry.operators import (
    GeneralRotor,
    ReflectionLine,
    ReflectionPoint,
    Rotor,
    Translator,
)


def _point(p):  # noqa: ANN001, ANN202
    return Point(p[0], p[1], p[2])


# ═══════════════════════════════════════════════════════════════
# Round-trip tests: create_entity + typed analyzer reproduces entity.
# ═══════════════════════════════════════════════════════════════


@pytest.mark.parametrize("opns", [True, False])
def test_p3_point_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_p3_direction_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Direction(1, 2, 3))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


@pytest.mark.parametrize("opns", [True, False])
def test_p3_line_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisP3(opns=opns)
    mv = create_entity(alg, Line(Point(1, 0, 0), Direction(0, 1, 0)))
    r = analysis.analyze_line(mv)
    assert isinstance(r, Line)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_point_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_circle_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Circle(Point(1, 2, 3), 2.0, Direction(0, 0, 1)))
    r = analysis.analyze_circle(mv)
    assert isinstance(r, Circle)
    assert r.radius == pytest.approx(2.0)


@pytest.mark.parametrize("opns", [True, False])
def test_n3_sphere_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisN3(opns=opns)
    mv = create_entity(alg, Sphere(Point(1, 0, 0), 2.0))
    r = analysis.analyze_sphere(mv)
    assert isinstance(r, Sphere)
    assert r.radius == pytest.approx(2.0)


@pytest.mark.parametrize("opns", [True, False])
def test_pga3_point_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisPGA3(opns=opns)
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


@pytest.mark.parametrize("opns", [True, False])
def test_pga3_plane_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisPGA3(opns=opns)
    mv = create_entity(alg, Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    r = analysis.analyze_plane(mv)
    assert isinstance(r, Plane)


def test_e3_direction_round_trip():  # noqa: ANN201
    alg = BasisE3()
    mv = create_entity(alg, Direction(1, 2, 3))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


@pytest.mark.parametrize("opns", [True, False])
def test_e3_plane_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisE3(opns=opns)
    mv = create_entity(alg, Plane(Point(0, 0, 0), Direction(0, 0, 1)))
    r = analysis.analyze_plane(mv)
    assert isinstance(r, Plane)


@pytest.mark.parametrize("opns", [True, False])
def test_e2_direction_round_trip(opns):  # noqa: ANN001, ANN201
    alg = BasisE2(opns=opns)
    mv = create_entity(alg, Direction(1, 2, 0))
    r = analysis.analyze_direction(mv)
    assert isinstance(r, Direction)


# ═══════════════════════════════════════════════════════════════
# Mismatch tests
# ═══════════════════════════════════════════════════════════════


def test_analyze_point_rejects_line():  # noqa: ANN201
    alg = BasisP3()
    line_mv = create_entity(alg, Line(Point(0, 0, 0), Direction(1, 0, 0)))
    with pytest.raises(TypeError, match="Expected a Point"):
        analysis.analyze_point(line_mv)


def test_analyze_space_rejects_point():  # noqa: ANN201
    alg = BasisP3()
    point_mv = create_entity(alg, Point(1, 2, 3))
    with pytest.raises(TypeError, match="Expected a Space"):
        analysis.analyze_space(point_mv)


def test_analyze_point_e3_convenience():  # noqa: ANN201
    alg = BasisE3()
    mv = alg.multivector({1: 1.0})
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


def test_analyze_point_e2_convenience():  # noqa: ANN201
    alg = BasisE2()
    mv = alg.multivector({1: 1.0, 2: 2.0})
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


def test_analyze_plane_unsupported_in_e2():  # noqa: ANN201
    alg = BasisE2()
    mv = alg.multivector({1: 1.0})
    with pytest.raises(TypeError, match="not supported in e2"):
        analysis.analyze_plane(mv)


def test_ipns_mode_round_trip():  # noqa: ANN201
    alg = BasisN3()
    alg.opns = False
    mv = create_entity(alg, Point(1, 2, 3))
    r = analysis.analyze_point(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


# ═══════════════════════════════════════════════════════════════
# expect= hint — reflection → half-turn rotation coercion
# ═══════════════════════════════════════════════════════════════


def test_expect_general_rotor_from_reflection_line():  # noqa: ANN201
    alg = BasisN3()
    mv = create_operator(
        alg, GeneralRotor(math.pi, Direction(0, 0, 1), Point(1, 0, 0))
    )
    assert isinstance(analysis.analyze_operator(mv), ReflectionLine)
    gr = analysis.analyze_operator(mv, expect=GeneralRotor)
    assert isinstance(gr, GeneralRotor)
    assert gr.angle == pytest.approx(math.pi)
    assert gr.origin.x == pytest.approx(1.0)


def test_expect_rotor_skips_displaced_reflection_line():  # noqa: ANN201
    alg = BasisN3()
    mv = create_operator(
        alg, GeneralRotor(math.pi, Direction(0, 0, 1), Point(1, 0, 0))
    )
    r = analysis.analyze_operator(mv, expect=Rotor)
    assert isinstance(r, ReflectionLine)  # displaced line cannot be a Rotor


def test_coerce_origin_reflection_line_to_rotor():  # noqa: ANN201
    line = ReflectionLine(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
    r = analysis._coerce_operator(line, Rotor, "n3")
    assert isinstance(r, Rotor)
    assert r.angle == pytest.approx(math.pi)


def test_expect_unrelated_type_returns_natural():  # noqa: ANN201
    alg = BasisN3()
    mv = create_operator(
        alg, GeneralRotor(math.pi, Direction(0, 0, 1), Point(1, 0, 0))
    )
    r = analysis.analyze_operator(mv, expect=Translator)
    assert isinstance(r, ReflectionLine)


def test_expect_general_rotor_from_2d_reflection_point():  # noqa: ANN201
    alg = BasisN2()
    mv = create_operator(alg, ReflectionPoint(Point(2, -1, 0)))
    assert isinstance(analysis.analyze_operator(mv), ReflectionPoint)
    gr = analysis.analyze_operator(mv, expect=GeneralRotor)
    assert isinstance(gr, GeneralRotor)
    assert gr.angle == pytest.approx(math.pi)
    assert gr.origin.x == pytest.approx(2.0)
    assert gr.origin.y == pytest.approx(-1.0)


def test_coerce_origin_reflection_point_to_rotor():  # noqa: ANN201
    r = analysis._coerce_operator(ReflectionPoint(Point(0, 0, 0)), Rotor, "n2")
    assert isinstance(r, Rotor)
    assert r.angle == pytest.approx(math.pi)


def test_3d_reflection_point_not_coerced():  # noqa: ANN201
    alg = BasisN3()
    mv = create_operator(alg, ReflectionPoint(Point(2, -1, 3)))
    assert isinstance(analysis.analyze_operator(mv), ReflectionPoint)
    r = analysis.analyze_operator(mv, expect=GeneralRotor)
    assert isinstance(r, ReflectionPoint)  # 3D point reflection is an inversion


def test_2d_reflection_line_not_coerced():  # noqa: ANN201
    alg = BasisN2()
    mv = create_operator(
        alg, ReflectionLine(Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0)))
    )
    assert isinstance(analysis.analyze_operator(mv), ReflectionLine)
    r = analysis.analyze_operator(mv, expect=GeneralRotor)
    assert isinstance(r, ReflectionLine)  # 2D line reflection is a mirror


def test_geometry_analyze_expect():  # noqa: ANN201
    from pytanga.geometry import Geometry

    geo = Geometry(BasisN3())
    mv = create_operator(
        geo.algebra, GeneralRotor(math.pi, Direction(0, 0, 1), Point(1, 0, 0))
    )
    gr = geo.analyze(mv, expect=GeneralRotor)
    assert isinstance(gr, GeneralRotor)
