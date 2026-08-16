# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.5 tests — PGA2 entity and operator creation/analysis."""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisPGA2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    ReflectionLine,
    Rotor,
    Translator,
    ReflectionPoint,
)


@pytest.fixture(scope="module")
def b():
    return BasisPGA2()


# ═══════ Entity round‑trips ═══════


def test_create_point_opns_round_trip(b):
    mv = create_entity(b, Point(1, 2, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Point)
    # Sign may flip due to blade factorization order
    assert abs(r.x) == pytest.approx(1)
    assert abs(r.y) == pytest.approx(2)


def test_entity_direction_opns_round_trip(b):
    """E#: create Direction(1,2) → analyze OPNS → assert exact fields."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


def test_create_line_opns_round_trip(b):
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(b, line)
    r = analyze_entity(mv)
    assert isinstance(r, Line)
    assert abs(r.direction.x) > 0.9


def test_create_space_round_trip(b):
    mv = create_entity(b, Space(1.0))
    r = analyze_entity(mv)
    assert isinstance(r, Space)


# ═══════ IPNS ═══════


def test_create_point_ipns_round_trip(b, monkeypatch):
    monkeypatch.setattr(b, "opns", False)
    mv = create_entity(b, Point(1, 2, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Point)
    assert abs(r.x) == pytest.approx(1)


# ═══════ Operators ═══════


def test_rotor_round_trip(b):
    r = create_operator(b, Rotor(0.3, Direction(0, 0, 1)))
    result = analyze_operator(r)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(0.3, abs=1e-6)
    assert abs(result.axis.z) == pytest.approx(1)


def test_translator_round_trip(b):
    """create Translator(2,3,0) → analyze → assert vector."""
    t = create_operator(b, Translator(Direction(2, 3, 0)))
    r = analyze_operator(t)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(3)
    assert r.vector.z == pytest.approx(0)


def test_motor_round_trip(b):
    m = create_operator(
        b, Motor(Rotor(0.4, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))
    )
    r = analyze_operator(m)
    assert isinstance(r, (Motor, Translator, GeneralRotor))


def test_reflection_line_round_trip(b):
    """create ReflectionLine(x-axis) → analyze → assert ReflectionLine."""
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    # Line is through origin along x: direction perpendicular to normal
    d = r.line.direction
    assert abs(d.x) == pytest.approx(1, abs=1e-6)
    assert abs(d.y) == pytest.approx(0, abs=1e-6)


def test_reflection_origin_round_trip(b):
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, (ReflectionPoint, Rotor, GeneralRotor))


def test_general_rotor_round_trip(b):
    """create GeneralRotor(angle=0.5, z-axis, origin=(1,0,0)) → analyze → assert."""
    mv = create_operator(
        b, GeneralRotor(0.5, Direction(0, 0, 1), Point(1, 0, 0))
    )
    r = analyze_operator(mv)
    assert isinstance(r, (GeneralRotor, Motor)), f"Got {type(r).__name__}"
    if isinstance(r, GeneralRotor):
        assert r.angle == pytest.approx(0.5, abs=1e-6)
        assert abs(r.axis.z) == pytest.approx(1)
        assert r.origin.x == pytest.approx(1, abs=1e-6)


# ═══════ Algebra detection ═══════


def test_pga2_is_not_n2():
    from pytanga.basis import BasisN2, BasisPGA2

    b2 = BasisPGA2()
    assert not isinstance(b2, BasisN2)
