# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""E2 entity & operator round-trip and application tests.

Follows the test guide: dev/todos/test-guide-algebra-round-trip.md

E2 (Cl(2)) represents Euclidean 2D vectors and bivectors.
Only entities and operators passing through the origin are representable:
- Entities: Direction (grade-1 OPNS / grade-1 IPNS),
  Space (grade-2 OPNS)
- Operators: Rotor, ReflectionLine
- Points, lines not through origin, and conformal operators
  (Translator, Motor, GeneralRotor, etc.) are NOT available.
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisE2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import (
    ReflectionLine,
    Rotor,
)


@pytest.fixture(scope="module")
def b():
    return BasisE2()


# ===============================================================
# Entity round-trips
# ===============================================================

# --- E1. Direction (OPNS) ---


def test_entity_direction_opns_round_trip(b):
    """E1: create Direction(3,-4,0) → analyze OPNS → assert exact fields."""
    mv = create_entity(b, Direction(3, -4, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    # Not normalized — exact coefficients preserved
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-4)
    assert r.z == pytest.approx(0)


# --- E2. Space ---


def test_entity_space_opns_round_trip(b):
    """E2: create Space(scale=3.5) → analyze → assert scale."""
    mv = create_entity(b, Space(scale=3.5))
    r = analyze_entity(mv)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(3.5)


# --- E3. Direction (IPNS) ---


def test_entity_direction_ipns_round_trip(b, monkeypatch):
    """E3: create Direction(1,2,0) → analyze IPNS → assert normalized Direction.

    In E2 IPNS, a grade-1 blade represents a line through the origin
    with *n* being the line normal.  The IPNS form of a direction is the
    dual of its Euclidean vector — a perpendicular vector `(y, −x)`.
    """
    monkeypatch.setattr(b, "opns", False)
    mv = create_entity(b, Direction(1, 2, 0), opns=False)
    r = analyze_entity(mv)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    # IPNS direction is the dual (perpendicular), normalized to unit length
    mag = math.sqrt(1 * 1 + 2 * 2)
    assert r.x == pytest.approx(2 / mag)
    assert r.y == pytest.approx(-1 / mag)
    assert r.z == pytest.approx(0)


# ===============================================================
# Operator round-trips
# ===============================================================

# --- O1. Rotor ---


def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis.

    Analysis returns positive angle via acos(|dot|).  Axis sign is
    always (0,0,1) in 2D (the pseudoscalar e₁₂ direction).
    """
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    # Axis always Dir(0,0,1) in 2D — only rotation plane is e₁₂
    assert r.axis.z == pytest.approx(1) or r.axis.z == pytest.approx(-1)
    assert r.axis.x == pytest.approx(0, abs=1e-10)
    assert r.axis.y == pytest.approx(0, abs=1e-10)


# --- O2. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O2: create ReflectionLine(y-axis) → analyze → assert ReflectionLine.

    E2 reflection line versor is a grade-1 vector (the line direction).
    """
    mv = create_operator(b, ReflectionLine(Direction(0, 1, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    assert r.line.direction.x == pytest.approx(0, abs=1e-10)
    assert abs(r.line.direction.y) == pytest.approx(1)
    assert r.line.direction.z == pytest.approx(0, abs=1e-10)


# ===============================================================
# Operator application tests
# E2 has no points — apply operators to raw vectors via sandwich.
# ===============================================================

# --- A1. Rotor ---


def test_apply_rotor_vector_rotation_z(b):
    """A1: Rotor(90°, z) on e₁ → result is e₂ (counter‑clockwise).

    First-principles: E2 sign convention — +90° rotates
    e₁ to e₂ (counter‑clockwise looking from +z).  See existing test
    test_rotor_sign_convention_90_deg_z for confirmation.
    """
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    v = b.multivector({b.E1: 1.0})
    result = R.gp(v).gp(R.rev())
    assert float(result[b.E1]) == pytest.approx(0, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(1, abs=1e-10)


# --- A2. ReflectionLine ---


def test_apply_reflection_line_vector_mirror_y(b):
    """A2: ReflectionLine(y-axis) on (3,−2) → (−3,−2).

    Line reflection: d·v·d⁻¹.  Component parallel to d stays,
    perpendicular components flip sign.  d = e₂ flips e₁.
    """
    L = create_operator(b, ReflectionLine(Direction(0, 1, 0)))
    v = b.multivector({b.E1: 3.0, b.E2: -2.0})
    result = L.gp(v).gp(L.rev())
    assert float(result[b.E1]) == pytest.approx(-3, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(-2, abs=1e-10)


def test_apply_reflection_line_vector_mirror_x(b):
    """A2b: ReflectionLine(x-axis) on (3,−2) → (3,2).

    d = e₁ flips e₂, parallel e₁ stays unchanged.
    """
    L = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    v = b.multivector({b.E1: 3.0, b.E2: -2.0})
    result = L.gp(v).gp(L.rev())
    assert float(result[b.E1]) == pytest.approx(3, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(2, abs=1e-10)


# ===============================================================
# Defensive tests
# ===============================================================


def test_create_point_components(b):
    """Point maps to e1/e2 components independent of OPNS/IPNS."""
    mv = create_entity(b, Point(1, 2, 0))
    assert set(mv.grades) == {1}
    assert float(mv[1]) == pytest.approx(1)
    assert float(mv[2]) == pytest.approx(2)


def test_create_line_not_through_origin_raises(b):
    """Line offset from origin must raise ValueError in E2."""
    line = Line(origin=Point(1, 2, 0), direction=Direction(1, 0, 0))
    with pytest.raises(ValueError, match="only lines through the origin"):
        create_entity(b, line, opns=True)


def test_create_direction_zero_norm_raises(b):
    """E2 create_direction permits zero-norm; analyze_entity rejects it.

    E2 create_direction doesn't validate zero-norm at creation time,
    but analyze_entity rejects the resulting zero vector.
    """
    mv = create_entity(b, Direction(0, 0, 0))
    with pytest.raises(ValueError):
        analyze_entity(mv)


def test_analyze_zero_vector_raises(b):
    """Zero MV passed to analyze_entity must raise ValueError."""
    zero = b.multivector({})
    with pytest.raises(ValueError):
        analyze_entity(zero)


def test_ipns_grade_2_raises(b, monkeypatch):
    """IPNS grade-2 bivector is only the trivial origin → ValueError."""
    monkeypatch.setattr(b, "opns", False)
    # Create a grade-2 bivector = pseudoscalar
    grade2_ipns = b.multivector({b.E12: 1.0})
    with pytest.raises(ValueError, match="trivial"):
        analyze_entity(grade2_ipns)


# ===============================================================
# N2-only entities and operators — must raise in E2
# ===============================================================

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    ReflectionPoint,
    Translator,
)


@pytest.mark.parametrize(
    "entity_cls,args",
    [
        (Sphere, (Point(0, 0, 0), 1.0)),
        (Circle, (Point(0, 0, 0), 1.0, Direction(0, 0, 1))),
        (PointPair, (Point(0, 0, 0), Point(1, 1, 1))),
        (HPoint, (Point(0, 0, 0),)),
    ],
)
def test_n2_entity_raises(b, entity_cls, args):
    with pytest.raises(ValueError, match="N2"):
        create_entity(b, entity_cls(*args))


@pytest.mark.parametrize(
    "op_cls,args",
    [
        (Translator, (Direction(1, 0, 0),)),
        (Dilator, (2.0,)),
        (Inversion, (Point(0, 0, 0),)),
        (Motor, (Rotor(0, Direction(0, 0, 1)), Translator(Direction(1, 0, 0)))),
        (GeneralRotor, (math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))),
        (ReflectionPoint, (Point(0, 0, 0),)),
    ],
)
def test_n2_operator_raises(b, op_cls, args):
    with pytest.raises((ValueError, TypeError)):
        create_operator(b, op_cls(*args))
