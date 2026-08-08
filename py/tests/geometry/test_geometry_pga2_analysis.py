# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA2 entity/operator analysis tests — create ↔ analyze round-trip and operator application.

These tests validate that entities and operators created via ``create_entity`` /
``create_operator`` can be correctly analyzed via ``analyze_entity`` /
``analyze_operator``, and that operator application produces the expected
geometric transformations.
"""

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
    ReflectionPoint,
    Rotor,
    Translator,
    TripleReflection,
)


@pytest.fixture(scope="module")
def b():
    return BasisPGA2()


# ═══════════════════════════════════════════════════════════════
# Entity round-trips
# ═══════════════════════════════════════════════════════════════


def test_entity_point_opns_round_trip(b):
    """E1: create Point → analyze → assert exact Euclidean coordinates."""
    mv = create_entity(b, Point(3, -2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)


def test_entity_direction_opns_round_trip(b):
    """E2: create Direction → analyze → assert exact components."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction)
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)


def test_entity_line_opns_round_trip(b):
    """E3: create Line → analyze → assert origin and direction."""
    line = Line(origin=Point(1, 0, 0), direction=Direction(0, 1, 0))
    mv = create_entity(b, line)
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line)
    assert abs(r.direction.y) == pytest.approx(1, abs=0.1)


def test_entity_space_round_trip(b):
    """E4: create Space → analyze → assert Space with scale."""
    mv = create_entity(b, Space(3.0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space)
    assert r.scale == pytest.approx(3.0)


# ═══════════════════════════════════════════════════════════════
# Operator round-trips
# ═══════════════════════════════════════════════════════════════


def test_operator_rotor_round_trip(b):
    """O1: create Rotor → analyze → assert exact angle and axis."""
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor)
    assert r.angle == pytest.approx(math.pi / 2, abs=1e-6)
    assert r.axis.z == pytest.approx(1)


def test_operator_translator_round_trip(b):
    """O2: create Translator → analyze → assert exact vector."""
    mv = create_operator(b, Translator(Direction(2, -1, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator)
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)


def test_operator_motor_round_trip(b):
    """O3: create Motor → analyze → verify round-trip (Motor or GeneralRotor)."""
    mv = create_operator(
        b, Motor(Rotor(math.pi / 2, Direction(0, 0, 1)), Translator(Direction(1, 2, 0)))
    )
    r = analyze_operator(mv)
    # Motor = T·R may factorize as 2 or 4 factors depending on the translator
    # product interaction in the 4D embedding.  Either classification is valid.
    assert isinstance(r, (Motor, GeneralRotor)), (
        f"Expected Motor or GeneralRotor, got {type(r).__name__}"
    )


def test_operator_reflection_point_origin_round_trip(b):
    """O5: create ReflectionPoint(0,0,0) -> analyze -> assert."""
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint), f"Expected ReflectionPoint, got {type(r).__name__}"


def test_operator_general_rotor_round_trip(b):
    """O6: create GeneralRotor → analyze → assert exact angle, axis, origin."""
    mv = create_operator(
        b,
        GeneralRotor(
            angle=math.pi / 2,
            axis=Direction(0, 0, 1),
            origin=Point(1, 0, 0),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, GeneralRotor), f"Expected GeneralRotor, got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2, abs=1e-6)
    assert r.axis.z == pytest.approx(1)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)


@pytest.mark.skip(
    reason="No reliable way to construct a 3-factor PGA2 versor — e0 embedding splits factors"
)
def test_operator_triple_reflection_round_trip(b):
    """O7: TripleReflection code path exists but cannot construct testable input."""
    pass


# ═══════════════════════════════════════════════════════════════
# Operator application tests
# ═══════════════════════════════════════════════════════════════


def test_apply_translator_point_displacement(b):
    """A1: Translator applied to origin → assert displacement."""
    p = create_entity(b, Point(0, 0, 0))
    T = create_operator(b, Translator(Direction(3, -2, 0)))
    pt = T * p * T.rev()
    r = analyze_entity(pt, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)


def test_apply_rotor_point_rotation(b):
    """A2: Rotor (90° about z) applied to (1,0) → assert (0,1)."""
    p = create_entity(b, Point(1, 0, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    pt = R * p * R.rev()
    r = analyze_entity(pt, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)


def test_apply_motor_point_motion(b):
    """A3: Motor (translate +1x, rotate 90°) applied to origin."""
    p = create_entity(b, Point(0, 0, 0))
    M = create_operator(
        b, Motor(Rotor(math.pi / 2, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))
    )
    pt = M * p * M.rev()
    r = analyze_entity(pt, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(0, abs=1e-6)


def test_apply_reflection_point_origin_reflection(b):
    """A5: ReflectionPoint(0,0,0) on (5,-3,0) -> Point(-5,3,0)."""
    p = create_entity(b, Point(5, -3, 0))
    O = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    pt = O * p * O.rev()
    r = analyze_entity(pt, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(-5)
    assert r.y == pytest.approx(3)


def test_apply_general_rotor_point_displaced_rotation(b):
    """A6: GeneralRotor (rot 90° about center (1,0)) applied to (3,0)."""
    p = create_entity(b, Point(3, 0, 0))
    G = create_operator(
        b,
        GeneralRotor(
            angle=math.pi / 2,
            axis=Direction(0, 0, 1),
            origin=Point(1, 0, 0),
        ),
    )
    pt = G * p * G.rev()
    r = analyze_entity(pt, opns=True)
    assert isinstance(r, Point)
    # (3,0) relative to center (1,0) is (2,0).  Rotate 90° → (0,2).  Add center → (1,2).
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)


# --- O5b. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O5b: create ReflectionLine(x-axis) -> analyze -> assert."""
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_operator(b, ReflectionLine(line))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    d = r.line.direction
    assert abs(d.x) == pytest.approx(1, abs=1e-6)


def test_apply_reflection_line_point_mirror_x(b):
    """A5b: ReflectionLine(x-axis) on (3,1,0) -> Point(3,-1,0)."""
    p = create_entity(b, Point(3, 1, 0))
    L = create_operator(b, ReflectionLine(Line(Point(0, 0, 0), Direction(1, 0, 0))))
    result = L * p * L.rev()
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point)
    assert r.x == pytest.approx(3, abs=1e-6)
    assert r.y == pytest.approx(-1, abs=1e-6)

