# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""E3 entity & operator round-trip and application tests.

Follows the test guide: dev/todos/test-guide-algebra-round-trip.md

E3 (Cl(3)) represents Euclidean 3D vectors, bivectors, and trivectors.
Only entities and operators passing through the origin are representable:
- Entities: Direction (grade-1 OPNS), Plane (grade-2 OPNS / grade-1 IPNS),
  Space (grade-3 OPNS), Line (grade-2 IPNS via plane intersection)
- Operators: Rotor, ReflectionLine, ReflectionPlane
- Points, lines/planes not through origin, and conformal operators
  (Translator, Motor, GeneralRotor, etc.) are NOT available.
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisE3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space
from pytanga.geometry.operators import (
    ReflectionLine,
    ReflectionPlane,
    Rotor,
)


@pytest.fixture(scope="module")
def b():
    return BasisE3()


# ===============================================================
# Entity round-trips
# ===============================================================

# --- E1. Direction (OPNS) ---


def test_entity_direction_opns_round_trip(b):
    """E1: create Direction(1,2,3) → analyze OPNS → assert exact fields."""
    mv = create_entity(b, Direction(1, 2, 3))
    r = analyze_entity(mv)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    # Not normalized — exact coefficients preserved
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(3)


# --- E2. Plane (OPNS, grade-2 bivector) ---


def test_entity_plane_opns_round_trip(b):
    """E2: create Plane(origin, normal=(1,2,3)) → analyze OPNS → assert.

    E3 only supports planes through origin.  Normal is unit-length
    after analysis.  Sign may flip (±n describe the same plane).
    """
    normal = Direction(1, 2, 3)
    unit = normal.normalized()
    plane = Plane(point=Point(0, 0, 0), normal=normal)
    mv = create_entity(b, plane)
    r = analyze_entity(mv)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"
    # Normal may have sign flip (±n describe the same plane through origin)
    assert abs(r.normal.x) == pytest.approx(abs(unit.x))
    assert abs(r.normal.y) == pytest.approx(abs(unit.y))
    assert abs(r.normal.z) == pytest.approx(abs(unit.z))
    assert r.point.x == pytest.approx(0)
    assert r.point.y == pytest.approx(0)
    assert r.point.z == pytest.approx(0)


# --- E3. Space ---


def test_entity_space_opns_round_trip(b):
    """E3: create Space(scale=3.5) → analyze → assert scale."""
    mv = create_entity(b, Space(scale=3.5))
    r = analyze_entity(mv)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(3.5)


# --- E4. Plane (IPNS, grade-1 vector) ---


def test_entity_plane_ipns_round_trip(b, monkeypatch):
    """E4: create Plane(origin, normal=z) → analyze IPNS → assert."""
    monkeypatch.setattr(b, "opns", False)
    plane = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    mv = create_entity(b, plane)
    r = analyze_entity(mv)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"
    assert abs(r.normal.z) == pytest.approx(1)
    assert r.point.x == pytest.approx(0)
    assert r.point.y == pytest.approx(0)
    assert r.point.z == pytest.approx(0)


# --- E5. Line (IPNS, grade-2 bivector via plane intersection) ---


def test_entity_line_ipns_round_trip(b, monkeypatch):
    """E5: two IPNS planes → IPNS bivector → analyze IPNS → Line through origin."""
    monkeypatch.setattr(b, "opns", False)
    p1 = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    p2 = Plane(point=Point(0, 0, 0), normal=Direction(1, 0, 0))
    mv1 = create_entity(b, p1)
    mv2 = create_entity(b, p2)
    line_mv = mv1.op(mv2)  # grade-2 IPNS bivector
    r = analyze_entity(line_mv)
    assert isinstance(r, Line), f"Got {type(r).__name__}"
    assert r.origin.x == pytest.approx(0)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)
    # Intersection of z-plane (z=0) and x-plane (x=0) is the y-axis
    assert abs(r.direction.y) == pytest.approx(1, abs=1e-6)


# ===============================================================
# Operator round-trips
# ===============================================================

# --- O1. Rotor ---


def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis.

    Analysis returns positive angle via acos(|dot|).  Axis sign may
    flip (n1 ∧ n2 vs n2 ∧ n1), both describe the same rotation plane.
    """
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    # Axis collinear with z — sign may flip
    assert r.axis.z == pytest.approx(1) or r.axis.z == pytest.approx(-1)
    assert r.axis.x == pytest.approx(0, abs=1e-10)
    assert r.axis.y == pytest.approx(0, abs=1e-10)


# --- O2. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O2: create ReflectionLine(z-axis) → analyze → assert ReflectionLine.

    E3 reflection line versor is a grade-1 vector (the line direction).
    """
    mv = create_operator(b, ReflectionLine(Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    assert r.line.direction.x == pytest.approx(0, abs=1e-10)
    assert r.line.direction.y == pytest.approx(0, abs=1e-10)
    assert abs(r.line.direction.z) == pytest.approx(1)


# --- O3. ReflectionPlane ---


def test_operator_reflection_plane_round_trip(b):
    """O3: create ReflectionPlane((0.6, 0, 0.8)) → analyze → assert.

    E3 reflection plane versor is a grade-2 bivector n·I⁻¹.
    """
    mv = create_operator(b, ReflectionPlane(Direction(0.6, 0.0, 0.8)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPlane), f"Got {type(r).__name__}"
    assert r.plane.normal.x == pytest.approx(0.6)
    assert r.plane.normal.y == pytest.approx(0, abs=1e-10)
    assert r.plane.normal.z == pytest.approx(0.8)


# ===============================================================
# Operator application tests
# E3 has no points — apply operators to raw vectors via sandwich.
# ===============================================================

# --- A1. Rotor ---


def test_apply_rotor_vector_rotation_z(b):
    """A1: Rotor(90°, z) on e₁ → result is e₂ (counter‑clockwise).

    First-principles: E3 sign convention — +90° about z rotates
    e₁ to e₂ (counter‑clockwise looking from +z).  See existing test
    test_rotor_sign_convention_90_deg_z for confirmation.
    """
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    v = b.multivector({b.E1: 1.0})
    result = R.gp(v).gp(R.rev())
    assert float(result[b.E1]) == pytest.approx(0, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(1, abs=1e-10)
    assert float(result[b.E3]) == pytest.approx(0, abs=1e-10)


def test_apply_rotor_vector_rotation_x(b):
    """A1b: Rotor(90°, x) on e₂ → result is e₃ (counter‑clockwise).

    +90° about x-axis (right‑hand rule): e₂ → e₃, e₃ → −e₂.
    """
    R = create_operator(b, Rotor(math.pi / 2, Direction(1, 0, 0)))
    v = b.multivector({b.E2: 1.0})
    result = R.gp(v).gp(R.rev())
    assert float(result[b.E1]) == pytest.approx(0, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(0, abs=1e-10)
    assert float(result[b.E3]) == pytest.approx(1, abs=1e-10)


def test_apply_rotor_vector_rotation_y(b):
    """A1c: Rotor(90°, y) on e₃ → result is e₁ (counter‑clockwise).

    +90° about y-axis (right‑hand rule): e₃ → e₁, e₁ → −e₃.
    """
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 1, 0)))
    v = b.multivector({b.E3: 1.0})
    result = R.gp(v).gp(R.rev())
    assert float(result[b.E1]) == pytest.approx(1, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(0, abs=1e-10)
    assert float(result[b.E3]) == pytest.approx(0, abs=1e-10)


# --- A2. ReflectionLine ---


def test_apply_reflection_line_vector_mirror_z(b):
    """A2: ReflectionLine(z-axis) on (1,2,3) → (−1,−2,3).

    Line reflection: d·v·d⁻¹.  Component parallel to d stays,
    perpendicular components flip sign.
    """
    L = create_operator(b, ReflectionLine(Direction(0, 0, 1)))
    v = b.multivector({b.E1: 1.0, b.E2: 2.0, b.E3: 3.0})
    result = L.gp(v).gp(L.rev())
    assert float(result[b.E1]) == pytest.approx(-1, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(-2, abs=1e-10)
    assert float(result[b.E3]) == pytest.approx(3, abs=1e-10)


# --- A3. ReflectionPlane ---


def test_apply_reflection_plane_vector_mirror_z(b):
    """A3: ReflectionPlane(normal z, xy-plane) on (1,2,5) → (1,2,−5).

    Plane reflection formula: (−1)^(k+1) B a B⁻¹ with k=2 → −B a B.rev().
    x and y stay; z flips sign.
    """
    F = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    v = b.multivector({b.E1: 1.0, b.E2: 2.0, b.E3: 5.0})
    result = -F.gp(v).gp(F.rev())
    assert float(result[b.E1]) == pytest.approx(1, abs=1e-10)
    assert float(result[b.E2]) == pytest.approx(2, abs=1e-10)
    assert float(result[b.E3]) == pytest.approx(-5, abs=1e-10)


# ===============================================================
# Defensive tests
# ===============================================================


def test_create_point_components(b):
    """Point maps to e1/e2/e3 components independent of OPNS/IPNS."""
    mv = create_entity(b, Point(1, 2, 3))
    assert set(mv.grades) == {1}
    assert float(mv[1]) == pytest.approx(1)
    assert float(mv[2]) == pytest.approx(2)
    assert float(mv[4]) == pytest.approx(3)


def test_create_line_not_through_origin_raises(b):
    """Line offset from origin must raise ValueError in E3."""
    line = Line(origin=Point(1, 2, 3), direction=Direction(1, 0, 0))
    with pytest.raises(ValueError, match="only lines through the origin"):
        create_entity(b, line)


def test_create_plane_not_through_origin_raises(b):
    """Plane not through origin must raise ValueError in E3."""
    plane = Plane(point=Point(1, 0, 0), normal=Direction(0, 0, 1))
    with pytest.raises(ValueError, match="only planes through the origin"):
        create_entity(b, plane)


def test_create_direction_zero_norm_raises(b):
    """E3 create_direction permits zero-norm; analyze_entity rejects it.

    E3 create_direction doesn't validate zero-norm at creation time
    (unlike P2/P3 which raise at create time), but analyze_entity
    rejects the resulting zero vector.
    """
    mv = create_entity(b, Direction(0, 0, 0))
    with pytest.raises(ValueError):
        analyze_entity(mv)


def test_analyze_zero_vector_raises(b):
    """Zero MV passed to analyze_entity must raise ValueError."""
    zero = b.multivector({})
    with pytest.raises(ValueError):
        analyze_entity(zero)


def test_ipns_grade_3_raises(b, monkeypatch):
    """IPNS grade-3 trivector is only the trivial origin → ValueError."""
    monkeypatch.setattr(b, "opns", False)
    p1 = Plane(point=Point(0, 0, 0), normal=Direction(1, 0, 0))
    p2 = Plane(point=Point(0, 0, 0), normal=Direction(0, 1, 0))
    p3 = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    m1 = create_entity(b, p1)
    m2 = create_entity(b, p2)
    m3 = create_entity(b, p3)
    grade3_ipns = m1.op(m2).op(m3)
    with pytest.raises(ValueError, match="trivial"):
        analyze_entity(grade3_ipns)


# ===============================================================
# N3-only entities and operators — must raise in E3
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
def test_n3_entity_raises(b, entity_cls, args):
    with pytest.raises(ValueError, match="N3"):
        create_entity(b, entity_cls(*args))


@pytest.mark.parametrize(
    "op_cls,args",
    [
        (Translator, (Direction(1, 0, 0),)),
        (Dilator, (2.0,)),
        (Inversion, (Point(0, 0, 0),)),
        (Motor, (Rotor(0, Direction(1, 0, 0)), Translator(Direction(1, 0, 0)))),
        (GeneralRotor, (math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))),
        (ReflectionPoint, (Point(0, 0, 0),)),
    ],
)
def test_n3_operator_raises(b, op_cls, args):
    with pytest.raises((ValueError, TypeError)):
        create_operator(b, op_cls(*args))
