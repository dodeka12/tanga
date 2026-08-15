# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for N3 entity and operator creation/analysis."""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisN3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
)


@pytest.fixture(scope="module")
def b():
    return BasisN3()


# ═══════ Entity tests ═══════


def test_create_point_round_trip(b):
    mv = create_entity(b, Point(1, 2, 3))
    r = analyze_entity(mv)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


def test_create_point_is_null(b):
    mv = create_entity(b, Point(1, 2, 3))
    assert float(mv.sp(mv)) == pytest.approx(0, abs=1e-10)


def test_create_point_inner_product_distance(b):
    a = create_entity(b, Point(0, 0, 0))
    b_pt = create_entity(b, Point(3, 0, 0))
    assert float(a.sp(b_pt)) == pytest.approx(-4.5, abs=1e-6)  # -½‖3‖²


def test_create_line_round_trip(b):
    mv = create_entity(b, Line(Point(1, 2, 3), Direction(1, 0, 0)))
    r = analyze_entity(mv)
    assert isinstance(r, Line)
    assert abs(r.direction.x) > 0.9


def test_create_plane_opns_round_trip(b):
    mv = create_entity(b, Plane(Point(0, 0, 5), Direction(0, 0, 1)))
    r = analyze_entity(mv)
    assert isinstance(r, Plane)
    assert abs(r.normal.z) == pytest.approx(1, abs=1e-6)


def test_create_sphere_opns_round_trip(b):
    mv = create_entity(b, Sphere(Point(1, 2, 3), 2.0))
    r = analyze_entity(mv)
    assert isinstance(r, Sphere)
    assert r.center.x == pytest.approx(1, abs=1e-4)
    assert r.center.y == pytest.approx(2, abs=1e-4)
    assert r.center.z == pytest.approx(3, abs=1e-4)
    assert r.radius == pytest.approx(2.0, abs=1e-4)


def test_create_sphere_ipns_formula(b):
    """S = Cop(c) - ½r²·e∞ should have S² = r²."""
    from pytanga.geometry.create_n3 import create_sphere as n3_create_sphere

    s_ipns = n3_create_sphere(b, Point(0, 0, 0), 3.0, opns=False)
    assert float(s_ipns.sp(s_ipns)) == pytest.approx(9.0, abs=1e-6)


def test_create_plane_ipns_round_trip(b, monkeypatch):
    monkeypatch.setattr(b, "opns", False)
    mv = create_entity(b, Plane(Point(0, 0, 4), Direction(0, 0, 1)), opns=False)
    r = analyze_entity(mv)
    assert isinstance(r, Plane)
    assert r.point.z == pytest.approx(4, abs=1e-4)


def test_create_circle_opns(b):
    mv = create_entity(b, Circle(Point(0, 0, 0), 2.0, Direction(0, 0, 1)))
    r = analyze_entity(mv)
    assert isinstance(r, Circle)
    assert r.radius == pytest.approx(2.0, abs=1e-4)


def test_create_point_pair_round_trip(b):
    mv = create_entity(b, PointPair(Point(1, 0, 0), Point(3, 0, 0)))
    r = analyze_entity(mv)
    assert isinstance(r, PointPair)


def test_create_hpoint_round_trip(b):
    mv = create_entity(b, HPoint(Point(1, 2, 3)))
    r = analyze_entity(mv)
    assert isinstance(r, HPoint)


def test_create_space_round_trip(b):
    mv = create_entity(b, Space(2.0))
    r = analyze_entity(mv)
    assert isinstance(r, Space)
    assert r.scale == pytest.approx(2)


def test_create_direction_round_trip(b):
    mv = create_entity(b, Direction(1, 0, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Direction)


# ═══ Operator tests ═══


def test_reflection_plane_op(b):
    """Reflection in z=0 plane on point (1,2,3) → (1,2,-3)."""
    rp = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    p = create_entity(b, Point(1, 2, 3))
    result = rp * p * rp.rev()
    r = analyze_entity(result)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(-3)


def test_inversion_round_trip(b):
    inv = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    r = analyze_operator(inv)
    assert isinstance(r, Inversion)


def test_inversion_application(b):
    """Inversion in unit sphere at origin: point (2,0,0) → (0.5,0,0)."""
    inv = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    p = create_entity(b, Point(2, 0, 0))
    result = inv * p * inv.rev()
    r = analyze_entity(result)
    assert r.x == pytest.approx(0.5, abs=1e-6)
    assert r.y == pytest.approx(0, abs=1e-6)
    assert r.z == pytest.approx(0, abs=1e-6)


def test_dilator_round_trip(b):
    d = create_operator(b, Dilator(2.0))
    r = analyze_operator(d)
    assert isinstance(r, Dilator)
    assert r.factor == pytest.approx(2.0, abs=1e-6)


def test_dilator_round_trip_half(b):
    d = create_operator(b, Dilator(0.5))
    r = analyze_operator(d)
    assert isinstance(r, Dilator)
    assert r.factor == pytest.approx(0.5, abs=1e-6)


def test_translator_round_trip(b):
    t = create_operator(b, Translator(Direction(1, 0, 0)))
    r = analyze_operator(t)
    assert isinstance(r, Translator)
    assert r.vector.x == pytest.approx(1, abs=1e-6)


def test_translator_application(b):
    t = create_operator(b, Translator(Direction(10, 0, 0)))
    p = create_entity(b, Point(1, 2, 3))
    result = t * p * t.rev()
    r = analyze_entity(result)
    assert r.x == pytest.approx(11, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)
    assert r.z == pytest.approx(3, abs=1e-6)


def test_rotor_round_trip(b):
    r = create_operator(b, Rotor(1.0, Direction(1, 0, 0)))
    result = analyze_operator(r)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(1.0, abs=1e-6)


def test_reflection_line_round_trip(b):
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine)


def test_reflection_origin_round_trip(b):
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint)


# ═══════ Imaginary Sphere ═══════


def test_imag_sphere_not_supported(b):
    """Imaginary spheres are not implemented yet."""
    with pytest.raises(NotImplementedError):
        create_entity(b, Sphere(Point(1, 2, 3), 2.0, is_imaginary=True))


# ═══════ Imaginary Point Pair ═══════


def test_imag_point_pair_not_supported(b):
    """Imaginary point pairs are not implemented yet."""
    with pytest.raises(NotImplementedError):
        create_entity(
            b,
            PointPair(Point(1, 0, 0), Point(3, 0, 0), is_imaginary=True),
        )


# ═══════ Imaginary Circle ═══════


def test_imag_circle_not_supported(b):
    """Imaginary circles are not implemented yet."""
    with pytest.raises(NotImplementedError):
        create_entity(
            b,
            Circle(Point(0, 0, 0), 2.0, Direction(0, 0, 1), is_imaginary=True),
        )


# ═══════ General Rotor ═══════


def test_general_rotor_creation(b):
    """General rotor = T·R·T̃ with T translating to (10,0,0)."""
    gr = create_operator(
        b,
        GeneralRotor(angle=math.pi / 2, axis=Direction(0, 0, 1), origin=Point(10, 0, 0)),
    )
    p = create_entity(b, Point(0, 0, 0))
    result = gr * p * gr.rev()
    r = analyze_entity(result)
    # The point (0,0,0) relative to center (10,0,0) is (−10,0,0).
    # After 90° rotation about z: (0,±10,0) then add center: (10,±10,0).
    assert abs(r.x) == pytest.approx(10, abs=1e-4)
    assert abs(r.y) == pytest.approx(10, abs=1e-4)
    assert r.z == pytest.approx(0, abs=1e-4)


def test_general_rotor_round_trip(b):
    gr_op = GeneralRotor(angle=1.0, axis=Direction(1, 0, 0), origin=Point(0, 0, 0))
    mv = create_operator(b, gr_op)
    r = analyze_operator(mv)
    assert isinstance(r, (GeneralRotor, Rotor))


# ═══════ Dilator at Offset Origin ═══════


def test_dilator_at_offset_creation(b):
    """Dilator at center (1,0,0) with factor 2."""
    gd = create_operator(
        b,
        Dilator(factor=2.0, origin=Point(1, 0, 0)),
    )
    p = create_entity(b, Point(2, 0, 0))
    result = gd * p * gd.rev()
    r = analyze_entity(result)
    assert r.x == pytest.approx(3, abs=1e-4)
    assert r.y == pytest.approx(0, abs=1e-4)


def test_dilator_at_origin_round_trip(b):
    gd_op = Dilator(factor=2.0, origin=Point(0, 0, 0))
    mv = create_operator(b, gd_op)
    r = analyze_operator(mv)
    assert isinstance(r, Dilator)
