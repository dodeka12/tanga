# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 2 tests — E3 entity and operator creation/analysis.

Tests against Perwass definitions (see dev/todos/geo_fix/e3_entities.md).
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisE3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create, create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space
from pytanga.geometry.operators import ReflectionLine, ReflectionPlane, Rotor


@pytest.fixture(scope="module")
def basis_e3():
    """E3 basis — cached for the whole test module."""
    return BasisE3()


# ═══════════════════════════════════════════════════════════════
# Point — must raise
# ═══════════════════════════════════════════════════════════════


def test_create_point_components(basis_e3):
    """Point maps to e1/e2/e3 components independent of OPNS/IPNS."""
    mv = create_entity(basis_e3, Point(1, 2, 3))
    assert set(mv.grades) == {1}
    assert float(mv[1]) == pytest.approx(1)
    assert float(mv[2]) == pytest.approx(2)
    assert float(mv[4]) == pytest.approx(3)
    # IPNS: same Euclidean components (no dualization)
    mv_ipns = create_entity(BasisE3(opns=False), Point(1, 2, 3))
    assert float(mv_ipns[1]) == pytest.approx(1)
    assert float(mv_ipns[2]) == pytest.approx(2)
    assert float(mv_ipns[4]) == pytest.approx(3)


# ═══════════════════════════════════════════════════════════════
# Direction — round-trip
# ═══════════════════════════════════════════════════════════════


def test_create_direction_round_trip_opns(basis_e3):
    """create → analyze OPNS reproduces Direction."""
    d = Direction(3, 4, 0)
    mv = create_entity(basis_e3, d)
    result = analyze_entity(mv)
    assert isinstance(result, Direction)
    # Length may differ; verify direction ratios
    assert result.x / result.y == pytest.approx(3 / 4)


def test_create_direction_round_trip_ipns(basis_e3, monkeypatch):
    """A direction in IPNS is a bivector, analyzed as IPNS → Line."""
    monkeypatch.setattr(basis_e3, "opns", False)
    d = Direction(0, 0, 1)
    mv = create_entity(basis_e3, d)
    # IPNS direction is the dual — a grade-2 bivector
    assert set(mv.grades) == {2}
    result = analyze_entity(mv)
    # IPNS bivector = intersection of two planes → Line through origin
    assert isinstance(result, Line)
    assert result.origin.x == 0 and result.origin.y == 0 and result.origin.z == 0


# ═══════════════════════════════════════════════════════════════
# Line through origin
# ═══════════════════════════════════════════════════════════════


def test_create_line_through_origin(basis_e3):
    """Line through origin → grade-1 vector."""
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(basis_e3, line)
    grades = set(mv.grades)
    assert grades == {1}


def test_create_line_not_through_origin_raises(basis_e3):
    """Line NOT through origin → ValueError."""
    line = Line(origin=Point(1, 2, 3), direction=Direction(1, 0, 0))
    with pytest.raises(ValueError, match="only lines through the origin"):
        create_entity(basis_e3, line)


def test_line_ipns_round_trip(basis_e3, monkeypatch):
    """IPNS grade 2 (intersection of two planes) → Line through origin."""
    monkeypatch.setattr(basis_e3, "opns", False)
    # Two orthogonal planes through origin: normal z and normal x.
    # Intersection is the y-axis line.
    p1 = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    p2 = Plane(point=Point(0, 0, 0), normal=Direction(1, 0, 0))
    mv1 = create_entity(basis_e3, p1)  # IPNS vector for plane 1
    mv2 = create_entity(basis_e3, p2)  # IPNS vector for plane 2
    # Intersection in IPNS: outer product → grade-2 bivector
    line_mv = mv1.op(mv2)
    result = analyze_entity(line_mv)
    assert isinstance(result, Line)
    assert result.origin.x == pytest.approx(0)
    assert result.origin.y == pytest.approx(0)
    assert result.origin.z == pytest.approx(0)
    # Intersection of z-plane (z=0) and x-plane (x=0) is the y-axis
    assert abs(result.direction.y) > 0.9


# ═══════════════════════════════════════════════════════════════
# Plane through origin
# ═══════════════════════════════════════════════════════════════


def test_create_plane_through_origin_opns(basis_e3):
    """Plane through origin → bivector."""
    plane = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    mv = create_entity(basis_e3, plane)
    grades = set(mv.grades)
    assert grades == {2}
    # Components in e23 (nx), e31 (ny), e12 (nz)
    # Normal: (0,0,1). OPNS bivector via sdual of IPNS vector.
    # e23=nx=0, e31=ny=0, e12=nz→ may be ±1 depending on sdual sign convention
    assert mv.grade(2)[6] == pytest.approx(0, abs=1e-10)  # e23 = nx = 0
    assert mv.grade(2)[5] == pytest.approx(0, abs=1e-10)  # e31 = ny = 0
    assert abs(mv.grade(2)[3]) == pytest.approx(1.0)  # e12 = ±nz = ±1


def test_create_plane_not_through_origin_raises(basis_e3):
    """Plane NOT through origin → ValueError."""
    plane = Plane(point=Point(1, 0, 0), normal=Direction(0, 0, 1))
    with pytest.raises(ValueError, match="only planes through the origin"):
        create_entity(basis_e3, plane)


def test_plane_opns_round_trip(basis_e3):
    """Create plane bivector, analyze OPNS → Plane through origin."""
    plane = Plane(point=Point(0, 0, 0), normal=Direction(1, 2, 3))
    mv = create_entity(basis_e3, plane)
    result = analyze_entity(mv)
    assert isinstance(result, Plane)
    assert result.point.x == pytest.approx(0)
    assert result.point.y == pytest.approx(0)
    assert result.point.z == pytest.approx(0)
    # Normal should be unit-length
    length = math.sqrt(result.normal.x**2 + result.normal.y**2 + result.normal.z**2)
    assert length == pytest.approx(1.0, abs=1e-6)


def test_plane_ipns_round_trip(basis_e3, monkeypatch):
    """Create plane IPNS (vector), analyze IPNS → Plane through origin."""
    monkeypatch.setattr(basis_e3, "opns", False)
    plane = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    mv = create_entity(basis_e3, plane)
    result = analyze_entity(mv)
    assert isinstance(result, Plane)
    assert result.normal.x == pytest.approx(0)
    assert result.normal.y == pytest.approx(0)
    assert abs(result.normal.z) == pytest.approx(1)


# ═══════════════════════════════════════════════════════════════
# Space
# ═══════════════════════════════════════════════════════════════


def test_create_space_round_trip(basis_e3):
    """Create pseudoscalar, analyze → Space."""
    mv = create_entity(basis_e3, Space(scale=5.0))
    result = analyze_entity(mv)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(5.0)


def test_create_space_ipns_is_scalar():
    """Space in IPNS is a grade-0 scalar."""
    mv = create_entity(BasisE3(opns=False), Space(scale=2.0))
    assert set(mv.grades) == {0}
    assert float(mv.scalar) == pytest.approx(2.0)


# ═══════════════════════════════════════════════════════════════
# N3 entities/operators — must raise ValueError in E3
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
            (Point(0, 0, 0), Point(1, 1, 1)),
            {},
            "Point pairs require conformal",
        ),
        (HPoint, (Point(0, 0, 0),), {}, "Homogeneous points require conformal"),
    ],
)
def test_n3_entity_creation_raises(basis_e3, entity, args, kwargs, err_match):
    """N3-only entity creation in E3 must raise ValueError."""
    obj = entity(*args, **kwargs)
    with pytest.raises(ValueError, match=err_match):
        create_entity(basis_e3, obj)
    with pytest.raises(ValueError, match=err_match):
        create(basis_e3, obj)


def test_n3_operator_creation_raises_translator(basis_e3):
    with pytest.raises(ValueError, match="Translators require conformal"):
        create_operator(basis_e3, Translator(Direction(1, 0, 0)))


def test_n3_operator_creation_raises_dilator(basis_e3):
    with pytest.raises(ValueError, match="Dilators require conformal"):
        create_operator(basis_e3, Dilator(2.0))


def test_n3_operator_creation_raises_inversion(basis_e3):
    with pytest.raises(ValueError, match="Inversions require conformal"):
        create_operator(basis_e3, Inversion(Point(0, 0, 0), 1.0))


def test_n3_operator_creation_raises_motor(basis_e3):
    with pytest.raises(ValueError, match="Motors require conformal"):
        create_operator(
            basis_e3,
            Motor(Rotor(0, Direction(1, 0, 0)), Translator(Direction(1, 0, 0))),
        )


# ═══════════════════════════════════════════════════════════════
# Rotor — sign convention and round-trip
# ═══════════════════════════════════════════════════════════════


def test_rotor_sign_convention_90_deg_z(basis_e3):
    """Rotor of +π/2 about z-axis applied to e₁ gives e₂ (counter‑clockwise).

    Perwass convention: R = cos(θ/2) − sin(θ/2)·N₂ with rotor axis form
    via r = dual(N₂) giving R = cos(θ/2) + sin(θ/2)·axis_bivector.
    The code uses the axis form.  Application: R * v * R.rev().
    +90° about z rotates e₁ to e₂ (counter‑clockwise looking from +z).
    """
    rotor = create_operator(basis_e3, Rotor(math.pi / 2, Direction(0, 0, 1)))
    e1 = basis_e3.e1
    result = rotor * e1 * rotor.rev()
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(1.0, abs=1e-10)
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(0.0, abs=1e-10)


def test_rotor_sign_convention_90_deg_z_y_to_x(basis_e3):
    """Rotor of +π/2 about z-axis applied to e₂ gives −e₁ (counter‑clockwise)."""
    rotor = create_operator(basis_e3, Rotor(math.pi / 2, Direction(0, 0, 1)))
    e2 = basis_e3.e2
    result = rotor * e2 * rotor.rev()
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(-1.0, abs=1e-10)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(0.0, abs=1e-10)


def test_rotor_round_trip(basis_e3):
    """create_rotor → analyze_operator → Rotor.

    The factor order in blade_factorize_versor can flip the axis sign
    (n1∧n2 vs n2∧n1), so we check the absolute axis direction.
    """
    r = Rotor(math.pi / 3, Direction(1, 0, 0))
    mv = create_operator(basis_e3, r)
    result = analyze_operator(mv)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(math.pi / 3, abs=1e-6)
    # Axis should be along ±x (sign depends on factor order)
    assert abs(result.axis.x) == pytest.approx(1.0, abs=1e-6)
    assert result.axis.y == pytest.approx(0.0, abs=1e-6)
    assert result.axis.z == pytest.approx(0.0, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# ReflectionLine
# ═══════════════════════════════════════════════════════════════


def test_reflection_line_creation_is_grade_1(basis_e3):
    """create_reflection_line returns grade-1 vector."""
    mv = create_operator(basis_e3, ReflectionLine(Direction(1, 2, 3)))
    grades = set(mv.grades)
    assert grades == {1}


def test_reflection_line_round_trip_e3(basis_e3):
    """ReflectionLine round-trip: create → analyze."""
    rl = ReflectionLine(Direction(0, 0, 1))
    mv = create_operator(basis_e3, rl)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionLine)
    assert result.line.direction.x == pytest.approx(0)
    assert result.line.direction.y == pytest.approx(0)
    assert abs(result.line.direction.z) == pytest.approx(1)


def test_reflection_line_e3_application(basis_e3):
    """Reflection on z-axis line: z stays, xy flips via d * v * d.rev()."""
    rl_mv = create_operator(basis_e3, ReflectionLine(Direction(0, 0, 1)))
    v = basis_e3.multivector({1: 1, 2: 2, 4: 3})
    result = rl_mv * v * rl_mv.rev()
    # d = e3, a = (1,2,3). Parallel: (0,0,3) stays. Perp: (1,2,0) flips → (-1,-2,0)
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(-1.0)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(-2.0)
    assert float(result[basis_e3.blade_id("e3")]) == pytest.approx(3.0)


def test_reflection_line_e1_application(basis_e3):
    """Reflection on x-axis line: x stays, yz flips."""
    rl_mv = create_operator(basis_e3, ReflectionLine(Direction(1, 0, 0)))
    v = basis_e3.multivector({1: 1, 2: 2, 4: 3})
    result = rl_mv * v * rl_mv.rev()
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(1.0)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(-2.0)
    assert float(result[basis_e3.blade_id("e3")]) == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# ReflectionPlane
# ═══════════════════════════════════════════════════════════════


def test_reflection_plane_creation_is_grade_2(basis_e3):
    """create_reflection_plane returns grade-2 bivector."""
    mv = create_operator(basis_e3, ReflectionPlane(Direction(0, 0, 1)))
    grades = set(mv.grades)
    assert grades == {2}
    # nz=1 → e12 (blade 3)
    assert float(mv[basis_e3.blade_id("e12")]) == pytest.approx(1)


def test_reflection_plane_round_trip_e3(basis_e3):
    """ReflectionPlane round-trip: create → analyze."""
    rp = ReflectionPlane(Direction(0.6, 0.0, 0.8))
    mv = create_operator(basis_e3, rp)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionPlane)
    assert result.plane.normal.x == pytest.approx(0.6)
    assert result.plane.normal.y == pytest.approx(0.0)
    assert result.plane.normal.z == pytest.approx(0.8)


def test_reflection_plane_e3_application(basis_e3):
    """Reflection on xy-plane via −B * v * B.rev(): xy stays, z flips."""
    rp_mv = create_operator(basis_e3, ReflectionPlane(Direction(0, 0, 1)))
    v = basis_e3.multivector({1: 1, 2: 2, 4: 3})
    # Plane reflection formula: (−1)^(k+1) B a B⁻¹ with k=2 → −B a B.rev()
    result = -rp_mv * v * rp_mv.rev()
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(1.0)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(2.0)
    assert float(result[basis_e3.blade_id("e3")]) == pytest.approx(-3.0)


def test_reflection_plane_e1_normal_application(basis_e3):
    """Reflection on yz-plane (normal e1): x flips, yz stays."""
    rp_mv = create_operator(basis_e3, ReflectionPlane(Direction(1, 0, 0)))
    v = basis_e3.multivector({1: 1, 2: 2, 4: 3})
    result = -rp_mv * v * rp_mv.rev()
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(-1.0)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(2.0)
    assert float(result[basis_e3.blade_id("e3")]) == pytest.approx(3.0)


# ═══════════════════════════════════════════════════════════════
# Line vs Plane Reflection complement
# ═══════════════════════════════════════════════════════════════


def test_line_vs_plane_reflection_are_complementary_e3(basis_e3):
    """Line reflection on e3 + Plane reflection on e3 normal = full inversion."""
    v = basis_e3.multivector({1: 1, 2: 2, 4: 3})
    rl = create_operator(basis_e3, ReflectionLine(Direction(0, 0, 1)))
    rp = create_operator(basis_e3, ReflectionPlane(Direction(0, 0, 1)))
    # Line reflection: d*v*d.rev() with d=e3 → z stays, xy flips → (-1, -2, 3)
    step1 = rl * v * rl.rev()
    # Plane reflection: -B*step1*B.rev() with B=e12 → xy stays, z flips → (-1, -2, -3)
    result = -rp * step1 * rp.rev()
    assert float(result[basis_e3.blade_id("e1")]) == pytest.approx(-1.0)
    assert float(result[basis_e3.blade_id("e2")]) == pytest.approx(-2.0)
    assert float(result[basis_e3.blade_id("e3")]) == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# Backward compatibility — Reflection alias
# ═══════════════════════════════════════════════════════════════


def test_reflection_alias_is_reflection_plane():
    """Reflection should be an alias for ReflectionPlane."""
    from pytanga.geometry.operators import Reflection as PRefl

    r = PRefl(normal=Direction(1, 0, 0))
    assert isinstance(r, ReflectionPlane)
    assert r.plane.normal.x == 1


# ═══════════════════════════════════════════════════════════════
# IPNS grade 3 — must raise
# ═══════════════════════════════════════════════════════════════


def test_ipns_grade_3_raises(basis_e3, monkeypatch):
    """IPNS grade-3 trivector is trivial-only origin → ValueError."""
    monkeypatch.setattr(basis_e3, "opns", False)
    p1 = Plane(point=Point(0, 0, 0), normal=Direction(1, 0, 0))
    p2 = Plane(point=Point(0, 0, 0), normal=Direction(0, 1, 0))
    p3 = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
    m1 = create_entity(basis_e3, p1)
    m2 = create_entity(basis_e3, p2)
    m3 = create_entity(basis_e3, p3)
    grade3_ipns = m1.op(m2).op(m3)
    with pytest.raises(ValueError, match="trivial"):
        analyze_entity(grade3_ipns)


# ═══════════════════════════════════════════════════════════════
# Convenience wrapper — create()
# ═══════════════════════════════════════════════════════════════


def test_create_convenience_entity(basis_e3):
    """create() with entity works."""
    mv = create(basis_e3, Direction(1, 0, 0))
    assert set(mv.grades) == {1}


def test_create_convenience_operator(basis_e3):
    """create() with operator works."""
    mv = create(basis_e3, Rotor(0.5, Direction(0, 0, 1)))
    # Mixed-grade: scalar + bivector
    grades = set(mv.grades)
    assert 0 in grades
