# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.4 tests — N2 entity and operator creation/analysis.

Tests against Perwass definitions.  Mirrors test_geometry_n3.py.
N2 (Cl(3,1)) is the conformal model for 2D.
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisN2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import (
    Circle,
    Direction,
    HPoint,
    Line,
    Point,
    PointPair,
    Space,
    Sphere,
)
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionLine,
    ReflectionPoint,
    Rotor,
    Translator,
)


@pytest.fixture(scope="module")
def b():
    return BasisN2()


# ═══════ Entity tests ═══════


def test_create_point_round_trip(b):
    mv = create_entity(b, Point(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)


def test_create_point_is_null(b):
    mv = create_entity(b, Point(1, 2, 0))
    assert float(mv.sp(mv)) == pytest.approx(0, abs=1e-10)


def test_create_point_inner_product_distance(b):
    a = create_entity(b, Point(0, 0, 0))
    b_pt = create_entity(b, Point(3, 0, 0))
    # -½‖3‖² = -4.5
    assert float(a.sp(b_pt)) == pytest.approx(-4.5, abs=1e-6)


def test_create_line_round_trip(b):
    mv = create_entity(b, Line(Point(1, 2, 0), Direction(1, 0, 0)))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line)
    assert abs(r.direction.x) > 0.9


def test_create_sphere_opns_round_trip(b):
    """Sphere in N2 = circle in 2D."""
    mv = create_entity(b, Sphere(Point(1, 2, 0), 2.0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle)
    assert r.radius == pytest.approx(2.0, abs=1e-4)


def test_create_sphere_ipns_formula(b):
    """S = Cop(c) - ½r²·e∞ should have S² = r²."""
    from pytanga.geometry.create_n2 import create_sphere as n2_create_sphere

    s_ipns = n2_create_sphere(b, Point(0, 0, 0), 3.0, opns=False)
    assert float(s_ipns.sp(s_ipns)) == pytest.approx(9.0, abs=1e-6)


def test_create_circle_opns(b):
    """create_circle delegates to create_sphere in N2."""
    mv = create_entity(b, Circle(Point(0, 0, 0), Direction(0, 0, 1), 2.0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle)
    assert r.radius == pytest.approx(2.0, abs=1e-4)


def test_create_point_pair_round_trip(b):
    mv = create_entity(b, PointPair(Point(1, 0, 0), Point(3, 0, 0)))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, PointPair)


def test_create_hpoint_round_trip(b):
    mv = create_entity(b, HPoint(Point(1, 2, 0)))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, HPoint)


def test_create_direction_round_trip(b):
    mv = create_entity(b, Direction(1, 0, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction)


# ═══════ Operator tests ═══════


def test_translator_round_trip(b):
    t = create_operator(b, Translator(Direction(1, 0, 0)))
    r = analyze_operator(t)
    assert isinstance(r, Translator)
    assert r.vector.x == pytest.approx(1, abs=1e-6)


def test_translator_application(b):
    t = create_operator(b, Translator(Direction(10, 0, 0)))
    p = create_entity(b, Point(1, 2, 0))
    result = t * p * t.rev()
    r = analyze_entity(result, opns=True)
    assert r.x == pytest.approx(11, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)


def test_rotor_round_trip(b):
    r = create_operator(b, Rotor(1.0, Direction(1, 0, 0)))
    result = analyze_operator(r)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(1.0, abs=1e-6)


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


def test_inversion_round_trip(b):
    inv = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    r = analyze_operator(inv)
    assert isinstance(r, Inversion)


def test_inversion_application(b):
    inv = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    p = create_entity(b, Point(2, 0, 0))
    result = inv * p * inv.rev()
    r = analyze_entity(result, opns=True)
    assert r.x == pytest.approx(0.5, abs=1e-6)
    assert r.y == pytest.approx(0, abs=1e-6)


def test_reflection_line_round_trip(b):
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine)


def test_reflection_origin_round_trip(b):
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint)


def test_motor_round_trip(b):
    """Motor = T·R creates grades {0,2,4}."""
    m = create_operator(
        b,
        Motor(Rotor(0.5, Direction(0, 0, 1)), Translator(Direction(1, 0, 0))),
    )
    r = analyze_operator(m)
    assert isinstance(r, (Motor, Translator, GeneralRotor))


def test_general_rotor_round_trip(b):
    gr_op = GeneralRotor(angle=1.0, axis=Direction(1, 0, 0), origin=Point(1, 0, 0))
    mv = create_operator(b, gr_op)
    r = analyze_operator(mv)
    assert isinstance(r, (GeneralRotor, Rotor))


def test_dilator_at_origin_round_trip(b):
    gd_op = Dilator(factor=2.0, origin=Point(0, 0, 0))
    mv = create_operator(b, gd_op)
    r = analyze_operator(mv)
    assert isinstance(r, Dilator)


# ═══════ Imaginary Sphere (circle) — using direct N2 API ═══════


def test_imag_sphere_ipns_squared_negative(b):
    """Imag sphere (circle) IPNS has S² = -r². Direct N2 API."""
    from pytanga.geometry.create_n2 import create_sphere as n2_create_sphere

    s_ipns = n2_create_sphere(b, Point(1, 2, 0), 2.0, opns=False, is_imaginary=True)
    assert float(s_ipns.sp(s_ipns)) == pytest.approx(-4.0, abs=1e-6)


def test_imag_sphere_round_trip(b):
    """Imag sphere round-trip via direct N2 API."""
    from pytanga.geometry.create_n2 import create_sphere as n2_create_sphere

    mv = n2_create_sphere(b, Point(0, 0, 0), 3.0, is_imaginary=True, opns=True)
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle)
    assert r.is_imaginary
