# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.3 tests — P2 entity and operator creation/analysis.

Tests against Perwass definitions.  Mirrors test_geometry_p3.py.
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisP2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import (
    ReflectionLine,
    Rotor,
    ReflectionPoint,
)


@pytest.fixture(scope="module")
def basis_p2():
    return BasisP2()


# ═══════ Point ═══════


def test_create_point_round_trip(basis_p2):
    mv = create_entity(basis_p2, Point(1, 2, 0))
    result = analyze_entity(mv)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(2)


# ═══════ Direction ═══════


def test_create_direction_round_trip(basis_p2):
    mv = create_entity(basis_p2, Direction(1, 0, 0))
    result = analyze_entity(mv)
    assert isinstance(result, Direction)
    assert result.x == pytest.approx(1)


# ═══════ Line ═══════


def test_create_line_through_origin(basis_p2):
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(basis_p2, line)
    result = analyze_entity(mv)
    assert isinstance(result, Line)
    assert abs(result.direction.x) == pytest.approx(1)


def test_create_line_offset(basis_p2):
    line = Line(origin=Point(1, 2, 0), direction=Direction(1, 0, 0))
    mv = create_entity(basis_p2, line)
    result = analyze_entity(mv)
    assert isinstance(result, Line)
    assert abs(result.direction.x) > 0.9


# ═══════ Plane not supported in 2D ═══════

from pytanga.geometry.entities import Plane
from pytanga.geometry.operators import ReflectionPlane


def test_create_plane_raises_in_p2(basis_p2):
    """Plane entity is not supported in 2D (use Line instead)."""
    plane = Plane(point=Point(0, 5, 0), normal=Direction(0, 1, 0))
    with pytest.raises(AttributeError):
        create_entity(basis_p2, plane, opns=True)


# ═══════ Space ═══════


def test_create_space_round_trip(basis_p2):
    mv = create_entity(basis_p2, Space(scale=2.0), opns=True)
    result = analyze_entity(mv)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(2)


# ═══════ N2 entity rejects ═══════

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import Dilator, Inversion, Motor, Translator


@pytest.mark.parametrize(
    "entity_cls,args",
    [
        (Sphere, (Point(0, 0, 0), 1.0)),
        (Circle, (Point(0, 0, 0), 1.0, Direction(0, 0, 1))),
        (PointPair, (Point(0, 0, 0), Point(1, 0, 0))),
        (HPoint, (Point(0, 0, 0),)),
    ],
)
def test_n2_entity_raises(basis_p2, entity_cls, args):
    with pytest.raises(ValueError, match="N2"):
        create_entity(basis_p2, entity_cls(*args))


@pytest.mark.parametrize(
    "op_cls,args",
    [
        (Translator, (Direction(1, 0, 0),)),
        (Dilator, (2.0,)),
        (Inversion, (Point(0, 0, 0),)),
        (Motor, (Rotor(0, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))),
    ],
)
def test_n2_operator_raises(basis_p2, op_cls, args):
    with pytest.raises(ValueError, match="N2"):
        create_operator(basis_p2, op_cls(*args))


# ═══════ ReflectionLine ═══════


def test_reflection_line_creation_is_grade_2(basis_p2):
    from pytanga.basis.p2 import BasisP2

    mv = create_operator(basis_p2, ReflectionLine(Direction(1, 0, 0)))
    assert set(mv.grades) == {2}
    assert float(mv[BasisP2.E13]) == pytest.approx(1)


def test_reflection_line_round_trip(basis_p2):
    rl = ReflectionLine(Direction(0, 1, 0))
    mv = create_operator(basis_p2, rl)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionLine)
    assert abs(result.line.direction.y) == pytest.approx(1)


def test_reflection_line_application(basis_p2):
    rl_mv = create_operator(basis_p2, ReflectionLine(Direction(1, 0, 0)))
    a_hop = basis_p2.multivector({1: 1, 2: 2, 4: 1})
    result = rl_mv * a_hop * rl_mv.rev()
    w = float(result[4])
    assert abs(w) > 1e-15
    assert float(result[1]) / w == pytest.approx(1.0)
    assert float(result[2]) / w == pytest.approx(-2.0)


# ═══════ ReflectionPoint ═══════


def test_reflection_origin_creation_is_e3(basis_p2):
    from pytanga.basis.p2 import BasisP2

    mv = create_operator(basis_p2, ReflectionPoint(Point(0, 0, 0)))
    assert set(mv.grades) == {1}
    assert float(mv[BasisP2.E3]) == pytest.approx(1)


def test_reflection_origin_round_trip(basis_p2):
    mv = create_operator(basis_p2, ReflectionPoint(Point(0, 0, 0)))
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionPoint)


def test_reflection_origin_application(basis_p2):
    ro_mv = create_operator(basis_p2, ReflectionPoint(Point(0, 0, 0)))
    a_hop = basis_p2.multivector({1: 1, 2: 2, 4: 1})
    result = ro_mv * a_hop * ro_mv.rev()
    w = float(result[4])
    assert float(result[1]) / w == pytest.approx(-1.0)
    assert float(result[2]) / w == pytest.approx(-2.0)


# ═══════ Rotor ═══════


def test_rotor_round_trip(basis_p2):
    r = Rotor(math.pi / 3, Direction(1, 0, 0))
    mv = create_operator(basis_p2, r)
    result = analyze_operator(mv)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(math.pi / 3, abs=1e-6)
    assert abs(result.axis.z) == pytest.approx(1, abs=1e-6)


def test_rotor_application_homogeneous(basis_p2):
    r = Rotor(math.pi, Direction(0, 0, 1))
    rotor_mv = create_operator(basis_p2, r)
    a_hop = basis_p2.multivector({1: 1, 2: 2, 4: 1})
    result = rotor_mv * a_hop * rotor_mv.rev()
    w = float(result[4])
    assert float(result[1]) / w == pytest.approx(-1, abs=1e-6)
    assert float(result[2]) / w == pytest.approx(-2, abs=1e-6)


# ═══════ IPNS round-trips ═══════


def test_create_direction_ipns_round_trip(basis_p2, monkeypatch):
    """Direction(1,0,0) → IPNS → analyze IPNS → Direction(1,0,0)."""
    monkeypatch.setattr(basis_p2, "opns", False)
    mv = create_entity(basis_p2, Direction(1, 0, 0), opns=False)
    result = analyze_entity(mv)
    assert isinstance(result, Direction)


def test_create_space_ipns_round_trip(basis_p2, monkeypatch):
    monkeypatch.setattr(basis_p2, "opns", False)
    mv = create_entity(basis_p2, Space(scale=3.0), opns=False)
    assert set(mv.grades) == {0}
    result = analyze_entity(mv)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(3)
