# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 7.2 tests — E2 entity and operator creation/analysis.

Tests against Perwass definitions.  Mirrors test_geometry_e3.py.
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisE2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create, create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import ReflectionLine, ReflectionPoint, Rotor


@pytest.fixture(scope="module")
def basis_e2():
    """E2 basis — cached for the whole test module."""
    return BasisE2()


# ═══════════════════════════════════════════════════════════════
# Point — must raise
# ═══════════════════════════════════════════════════════════════


def test_create_point_raises(basis_e2):
    """Points cannot be represented in E2."""
    with pytest.raises(ValueError, match="Points cannot be represented"):
        create_entity(basis_e2, Point(1, 2, 0))


# ═══════════════════════════════════════════════════════════════
# Direction — round-trip
# ═══════════════════════════════════════════════════════════════


def test_create_direction_round_trip_opns(basis_e2):
    """create → analyze OPNS reproduces Direction."""
    d = Direction(3, 4, 0)
    mv = create_entity(basis_e2, d, opns=True)
    result = analyze_entity(mv)
    assert isinstance(result, Direction)
    assert result.x == pytest.approx(3)
    assert result.y == pytest.approx(4)
    assert result.z == pytest.approx(0)


# ═══════════════════════════════════════════════════════════════
# Line through origin
# ═══════════════════════════════════════════════════════════════


def test_create_line_through_origin(basis_e2):
    """Line through origin → grade-1 vector."""
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(basis_e2, line, opns=True)
    grades = set(mv.grades)
    assert grades == {1}


def test_create_line_not_through_origin_raises(basis_e2):
    """Line NOT through origin → ValueError."""
    line = Line(origin=Point(1, 2, 0), direction=Direction(1, 0, 0))
    with pytest.raises(ValueError, match="only lines through the origin"):
        create_entity(basis_e2, line, opns=True)


# ═══════════════════════════════════════════════════════════════
# Space
# ═══════════════════════════════════════════════════════════════


def test_create_space_round_trip(basis_e2):
    """Create pseudoscalar, analyze → Space."""
    mv = create_entity(basis_e2, Space(scale=5.0), opns=True)
    result = analyze_entity(mv)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(5.0)


# ═══════════════════════════════════════════════════════════════
# N2 entities — must raise ValueError in E2
# ═══════════════════════════════════════════════════════════════

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import (
    Dilator,
    Inversion,
    Motor,
    Translator,
)


@pytest.mark.parametrize(
    "entity,args,kwargs,err_match",
    [
        (Sphere, (Point(0, 0, 0), 1.0), {}, "Spheres require conformal"),
        (
            Circle,
            (Point(0, 0, 0), 1.0, Direction(0, 0, 1)),
            {},
            "Circles require conformal",
        ),
        (
            PointPair,
            (Point(0, 0, 0), Point(1, 0, 0)),
            {},
            "Point pairs require conformal",
        ),
        (HPoint, (Point(0, 0, 0),), {}, "Homogeneous points require conformal"),
    ],
)
def test_n2_entity_creation_raises(basis_e2, entity, args, kwargs, err_match):
    """N2-only entity creation in E2 must raise ValueError."""
    obj = entity(*args, **kwargs)
    with pytest.raises(ValueError, match=err_match):
        create_entity(basis_e2, obj)
    with pytest.raises(ValueError, match=err_match):
        create(basis_e2, obj)


def test_n2_operator_creation_raises_translator(basis_e2):
    with pytest.raises(ValueError, match="Translators require conformal"):
        create_operator(basis_e2, Translator(Direction(1, 0, 0)))


def test_n2_operator_creation_raises_dilator(basis_e2):
    with pytest.raises(ValueError, match="Dilators require conformal"):
        create_operator(basis_e2, Dilator(2.0))


def test_n2_operator_creation_raises_inversion(basis_e2):
    with pytest.raises(ValueError, match="Inversions require conformal"):
        create_operator(basis_e2, Inversion(Point(0, 0, 0), 1.0))


def test_n2_operator_creation_raises_motor(basis_e2):
    with pytest.raises(ValueError, match="Motors require conformal"):
        create_operator(
            basis_e2,
            Motor(Rotor(0, Direction(0, 0, 1)), Translator(Direction(1, 0, 0))),
        )


def test_n2_operator_creation_raises_origin_reflection(basis_e2):
    """E2 raises TypeError for ReflectionPoint."""
    with pytest.raises(TypeError):
        create_operator(basis_e2, ReflectionPoint(Point(0, 0, 0)))
def test_rotor_sign_convention_90_deg_z(basis_e2):
    """Rotor of +π/2 about z-axis applied to e₁ gives e₂ (counter‑clockwise).

    In 2D with R = cos(θ/2) + sin(θ/2)·e₁₂:
    R·e₁·R̃ rotates counter‑clockwise (from +z looking down): e₁ → e₂.
    """
    rotor = create_operator(basis_e2, Rotor(math.pi / 2, Direction(0, 0, 1)))
    e1 = basis_e2.e1
    result = rotor * e1 * rotor.rev()
    assert float(result[basis_e2.blade_id("e2")]) == pytest.approx(1.0, abs=1e-10)
    assert float(result[basis_e2.blade_id("e1")]) == pytest.approx(0.0, abs=1e-10)


def test_rotor_sign_convention_90_deg_z_e2_to_e1(basis_e2):
    """Rotor of +π/2 about z-axis applied to e₂ gives −e₁ (counter‑clockwise)."""
    rotor = create_operator(basis_e2, Rotor(math.pi / 2, Direction(0, 0, 1)))
    e2 = basis_e2.e2
    result = rotor * e2 * rotor.rev()
    assert float(result[basis_e2.blade_id("e1")]) == pytest.approx(-1.0, abs=1e-10)
    assert float(result[basis_e2.blade_id("e2")]) == pytest.approx(0.0, abs=1e-10)


def test_rotor_round_trip(basis_e2):
    """create_rotor → analyze_operator → Rotor."""
    r = Rotor(math.pi / 3, Direction(1, 0, 0))
    mv = create_operator(basis_e2, r)
    result = analyze_operator(mv)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(math.pi / 3, abs=1e-6)
    # Axis always Dir(0,0,1) in 2D
    assert abs(result.axis.z) == pytest.approx(1.0, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# ReflectionLine
# ═══════════════════════════════════════════════════════════════


def test_reflection_line_creation_is_grade_1(basis_e2):
    """create_reflection_line returns grade-1 vector."""
    mv = create_operator(basis_e2, ReflectionLine(Direction(1, 0, 0)))
    grades = set(mv.grades)
    assert grades == {1}


def test_reflection_line_round_trip(basis_e2):
    """ReflectionLine round-trip: create → analyze."""
    rl = ReflectionLine(Direction(0, 1, 0))
    mv = create_operator(basis_e2, rl)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionLine)
    assert result.line.direction.x == pytest.approx(0)
    assert abs(result.line.direction.y) == pytest.approx(1)


def test_reflection_line_application(basis_e2):
    """Reflection on y-axis line: y stays, x flips via d * v * d.rev()."""
    rl_mv = create_operator(basis_e2, ReflectionLine(Direction(0, 1, 0)))
    v = basis_e2.multivector({1: 1, 2: 2})
    result = rl_mv * v * rl_mv.rev()
    # d = e2. Parallel (e2) stays: (0,2). Perp (e1) flips: (-1,0) → (-1,2)
    assert float(result[basis_e2.blade_id("e1")]) == pytest.approx(-1.0)
    assert float(result[basis_e2.blade_id("e2")]) == pytest.approx(2.0)


def test_reflection_line_e1_application(basis_e2):
    """Reflection on x-axis line: x stays, y flips."""
    rl_mv = create_operator(basis_e2, ReflectionLine(Direction(1, 0, 0)))
    v = basis_e2.multivector({1: 1, 2: 2})
    result = rl_mv * v * rl_mv.rev()
    assert float(result[basis_e2.blade_id("e1")]) == pytest.approx(1.0)
    assert float(result[basis_e2.blade_id("e2")]) == pytest.approx(-2.0)


# ═══════════════════════════════════════════════════════════════
# Convenience wrapper — create()
# ═══════════════════════════════════════════════════════════════


def test_create_convenience_entity(basis_e2):
    """create() with entity works."""
    mv = create(basis_e2, Direction(1, 0, 0))
    assert set(mv.grades) == {1}


def test_create_convenience_operator(basis_e2):
    """create() with operator works."""
    mv = create(basis_e2, Rotor(0.5, Direction(0, 0, 1)))
    grades = set(mv.grades)
    assert 0 in grades
