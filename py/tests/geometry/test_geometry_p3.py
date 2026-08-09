# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Phase 3 tests — P3 entity and operator creation/analysis.

Tests against Perwass definitions (see dev/todos/geo_fix/p3_entities.md).
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisP3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space
from pytanga.geometry.operators import (
    ReflectionLine,
    ReflectionPlane,
    Rotor,
    ReflectionPoint,
)


@pytest.fixture(scope="module")
def basis_p3():
    return BasisP3()


# ═══════════════════════════════════════════════════════════════
# Point
# ═══════════════════════════════════════════════════════════════


def test_create_point_round_trip(basis_p3):
    """create_entity(Point(1,2,3)) → analyze OPNS → Point(1,2,3)."""
    mv = create_entity(basis_p3, Point(1, 2, 3))
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(2)
    assert result.z == pytest.approx(3)


# ═══════════════════════════════════════════════════════════════
# Direction
# ═══════════════════════════════════════════════════════════════


def test_create_direction_round_trip(basis_p3):
    """create_entity(Direction(1,0,0)) → analyze → Direction(1,0,0)."""
    mv = create_entity(basis_p3, Direction(1, 0, 0))
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Direction)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(0)
    assert result.z == pytest.approx(0)


# ═══════════════════════════════════════════════════════════════
# Line
# ═══════════════════════════════════════════════════════════════


def test_create_line_through_origin(basis_p3):
    """Line through origin → analyze returns correct direction."""
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_entity(basis_p3, line)
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Line)
    assert abs(result.direction.x) == pytest.approx(1)
    # origin should be on the line
    assert result.origin.x == pytest.approx(0, abs=1e-10)


def test_create_line_offset(basis_p3):
    """Line offset from origin → analyze returns correct direction.

    Note: blade_factorize orthogonalizes factors, so the extracted
    origin point may differ from the input origin.  Only the direction
    is guaranteed to match (up to sign).
    """
    line = Line(origin=Point(1, 2, 3), direction=Direction(1, 0, 0))
    mv = create_entity(basis_p3, line)
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Line)
    # Direction along x
    assert abs(result.direction.x) > 0.9


# ═══════════════════════════════════════════════════════════════
# Plane — OPNS
# ═══════════════════════════════════════════════════════════════


def test_create_plane_opns_round_trip_xy_plane(basis_p3):
    """Plane z=5, normal z → OPNS round-trip."""
    plane = Plane(point=Point(0, 0, 5), normal=Direction(0, 0, 1))
    mv = create_entity(basis_p3, plane, opns=True)
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Plane)
    assert result.normal.z == pytest.approx(1, abs=1e-6)
    # Point on plane: z ≈ 5
    assert result.point.z == pytest.approx(5, abs=1e-6)


def test_create_plane_opns_round_trip_diagonal(basis_p3):
    """Plane x+y+z=1 → OPNS round-trip."""
    plane = Plane(point=Point(1, 0, 0), normal=Direction(1, 0, 1))
    mv = create_entity(basis_p3, plane, opns=True)
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Plane)
    length = math.sqrt(result.normal.x**2 + result.normal.z**2)
    assert length == pytest.approx(1, abs=1e-6)
    # Point on plane
    assert (
        result.point.x * result.normal.x + result.point.z * result.normal.z
        == pytest.approx(
            plane.point.x * plane.normal.x / math.sqrt(2)
            + plane.point.z * plane.normal.z / math.sqrt(2),
            abs=1e-4,
        )
    )


# ═══════════════════════════════════════════════════════════════
# Plane — IPNS
# ═══════════════════════════════════════════════════════════════


def test_create_plane_ipns_round_trip(basis_p3):
    """Plane z=4, normal z → IPNS round-trip."""
    plane = Plane(point=Point(0, 0, 4), normal=Direction(0, 0, 1))
    mv = create_entity(basis_p3, plane, opns=False)
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Plane)
    assert result.normal.z == pytest.approx(1, abs=1e-6)
    assert result.point.z == pytest.approx(4, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# Space
# ═══════════════════════════════════════════════════════════════


def test_create_space_round_trip(basis_p3):
    mv = create_entity(basis_p3, Space(scale=2.0), opns=True)
    result = analyze_entity(mv, opns=True)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(2)


# ═══════════════════════════════════════════════════════════════
# N3 entities/operators — must raise
# ═══════════════════════════════════════════════════════════════

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import (
    Dilator,
    Inversion,
    Motor,
    Translator,
)


@pytest.mark.parametrize(
    "entity_cls,args",
    [
        (Sphere, (Point(0, 0, 0), 1.0)),
        (Circle, (Point(0, 0, 0), Direction(0, 0, 1), 1.0)),
        (PointPair, (Point(0, 0, 0), Point(1, 1, 1))),
        (HPoint, (Point(0, 0, 0),)),
    ],
)
def test_n3_entity_raises(basis_p3, entity_cls, args):
    with pytest.raises(ValueError, match="N3"):
        create_entity(basis_p3, entity_cls(*args))


@pytest.mark.parametrize(
    "op_cls,args",
    [
        (Translator, (Direction(1, 0, 0),)),
        (Dilator, (2.0,)),
        (Inversion, (Point(0, 0, 0),)),
        (Motor, (Rotor(0, Direction(1, 0, 0)), Translator(Direction(1, 0, 0)))),
    ],
)
def test_n3_operator_raises(basis_p3, op_cls, args):
    with pytest.raises(ValueError, match="N3"):
        create_operator(basis_p3, op_cls(*args))


# ═══════════════════════════════════════════════════════════════
# ReflectionLine
# ═══════════════════════════════════════════════════════════════


def test_reflection_line_creation_is_grade_2(basis_p3):
    """create_reflection_line returns grade-2 bivector with e₄ terms."""
    mv = create_operator(basis_p3, ReflectionLine(Direction(1, 0, 0)))
    grades = set(mv.grades)
    assert grades == {2}
    # Components in E14, E24, E34 (blades 9, 10, 12)
    assert float(mv[9]) == pytest.approx(1)  # e14 = nx
    assert float(mv[10]) == pytest.approx(0)  # e24 = ny
    assert float(mv[12]) == pytest.approx(0)  # e34 = nz


def test_reflection_line_round_trip(basis_p3):
    """create → analyze → ReflectionLine."""
    rl = ReflectionLine(Direction(0, 0, 1))
    mv = create_operator(basis_p3, rl)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionLine)
    assert result.line.direction.x == pytest.approx(0)
    assert result.line.direction.y == pytest.approx(0)
    assert abs(result.line.direction.z) == pytest.approx(1)


def test_reflection_line_application(basis_p3):
    """Line reflection on x-axis: apply N∧e₄ to Hop((1,2,3)) → projects to (1,−2,−3)."""
    rl_mv = create_operator(basis_p3, ReflectionLine(Direction(1, 0, 0)))
    a_hop = basis_p3.multivector({1: 1, 2: 2, 4: 3, 8: 1})  # Hop(1,2,3)
    result = rl_mv * a_hop * rl_mv.rev()
    w = float(result[8])  # e4
    assert abs(w) > 1e-15
    x = float(result[1]) / w
    y = float(result[2]) / w
    z = float(result[4]) / w
    assert x == pytest.approx(1.0)
    assert y == pytest.approx(-2.0)
    assert z == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# ReflectionPlane
# ═══════════════════════════════════════════════════════════════


def test_reflection_plane_creation_is_grade_1_no_e4(basis_p3):
    """create_reflection_plane returns grade-1 vector with e₄=0."""
    mv = create_operator(basis_p3, ReflectionPlane(Direction(0, 0, 1)))
    grades = set(mv.grades)
    assert grades == {1}
    assert float(mv[8]) == pytest.approx(0)  # e4 = 0


def test_reflection_plane_round_trip(basis_p3):
    """create → analyze → ReflectionPlane."""
    rp = ReflectionPlane(Direction(0, 0, 1))
    mv = create_operator(basis_p3, rp)
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionPlane)
    assert result.plane.normal.z == pytest.approx(1)


def test_reflection_plane_application(basis_p3):
    """Plane normal z: apply N to Hop((1,2,3)) → (1,2,−3)."""
    rp_mv = create_operator(basis_p3, ReflectionPlane(Direction(0, 0, 1)))
    a_hop = basis_p3.multivector({1: 1, 2: 2, 4: 3, 8: 1})
    result = rp_mv * a_hop * rp_mv.rev()
    w = float(result[8])
    x = float(result[1]) / w
    y = float(result[2]) / w
    z = float(result[4]) / w
    assert x == pytest.approx(1.0)
    assert y == pytest.approx(2.0)
    assert z == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# ReflectionPoint
# ═══════════════════════════════════════════════════════════════


def test_reflection_origin_creation_is_e4(basis_p3):
    """create_reflection_origin returns e₄ (grade 1, only at blade 8)."""
    mv = create_operator(basis_p3, ReflectionPoint(Point(0, 0, 0)))
    assert set(mv.grades) == {1}
    assert float(mv[8]) == pytest.approx(1)
    assert float(mv[1]) == pytest.approx(0)


def test_reflection_origin_round_trip(basis_p3):
    """create → analyze → ReflectionPoint."""
    mv = create_operator(basis_p3, ReflectionPoint(Point(0, 0, 0)))
    result = analyze_operator(mv)
    assert isinstance(result, ReflectionPoint)


def test_reflection_origin_application(basis_p3):
    """e₄·Hop(a)·e₄ → projects to −a."""
    ro_mv = create_operator(basis_p3, ReflectionPoint(Point(0, 0, 0)))
    a_hop = basis_p3.multivector({1: 1, 2: 2, 4: 3, 8: 1})
    result = ro_mv * a_hop * ro_mv.rev()
    w = float(result[8])
    x = float(result[1]) / w
    y = float(result[2]) / w
    z = float(result[4]) / w
    assert x == pytest.approx(-1.0)
    assert y == pytest.approx(-2.0)
    assert z == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# Orthogonality: Line vs Plane reflection
# ═══════════════════════════════════════════════════════════════


def test_line_vs_plane_complementary(basis_p3):
    """Line reflection on e3 + Plane reflection on e3 normal = both negate all? No — origin does."""
    a_hop = basis_p3.multivector({1: 1, 2: 2, 4: 3, 8: 1})
    rl = create_operator(basis_p3, ReflectionLine(Direction(0, 0, 1)))
    rp = create_operator(basis_p3, ReflectionPlane(Direction(0, 0, 1)))
    # Line: z stays, xy flips
    step1 = rl * a_hop * rl.rev()
    # Plane: xy stays, z flips
    result = rp * step1 * rp.rev()
    w = float(result[8])
    x = float(result[1]) / w
    y = float(result[2]) / w
    z = float(result[4]) / w
    assert x == pytest.approx(-1.0)
    assert y == pytest.approx(-2.0)
    assert z == pytest.approx(-3.0)


# ═══════════════════════════════════════════════════════════════
# Rotor
# ═══════════════════════════════════════════════════════════════


def test_rotor_round_trip(basis_p3):
    """create_rotor → analyze → Rotor."""
    r = Rotor(math.pi / 3, Direction(1, 0, 0))
    mv = create_operator(basis_p3, r)
    result = analyze_operator(mv)
    assert isinstance(result, Rotor)
    assert result.angle == pytest.approx(math.pi / 3, abs=1e-6)
    assert abs(result.axis.x) == pytest.approx(1, abs=1e-6)


def test_rotor_application_homogeneous(basis_p3):
    """Rotor applied to Hop(a) gives Hop(R(a))."""
    r = Rotor(math.pi, Direction(0, 0, 1))  # 180° about z
    rotor_mv = create_operator(basis_p3, r)
    a_hop = basis_p3.multivector({1: 1, 2: 2, 4: 3, 8: 1})
    result = rotor_mv * a_hop * rotor_mv.rev()
    w = float(result[8])
    x = float(result[1]) / w
    y = float(result[2]) / w
    z = float(result[4]) / w
    # 180° about z: (1,2,3) → (-1,-2,3)
    assert x == pytest.approx(-1, abs=1e-6)
    assert y == pytest.approx(-2, abs=1e-6)
    assert z == pytest.approx(3, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# Defensive: non‑simple bivector → ValueError (Phase 1)
# ═══════════════════════════════════════════════════════════════


def test_line_non_simple_bivector_raises(basis_p3):
    """Non‑simple bivector (B∧B ≠ 0) must raise ValueError."""
    line1 = create_entity(
        basis_p3, Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    )
    line2 = create_entity(
        basis_p3, Line(origin=Point(0, 1, 0), direction=Direction(0, 0, 1))
    )
    non_simple = line1 + line2
    with pytest.raises(ValueError, match="Non.*simple"):
        analyze_entity(non_simple, opns=True)


# ═══════════════════════════════════════════════════════════════
# Defensive: zero‑norm direction/vector rejection (Phase 2)
# ═══════════════════════════════════════════════════════════════


def test_create_direction_zero_norm_raises(basis_p3):
    """create_entity(Direction(0,0,0)) must raise ValueError."""
    with pytest.raises(ValueError, match="Zero.*norm"):
        create_entity(basis_p3, Direction(0, 0, 0))


def test_analyze_zero_vector_raises(basis_p3):
    """Zero MV passed to analyze_entity must raise ValueError."""
    zero = basis_p3.multivector({})
    with pytest.raises(ValueError):
        analyze_entity(zero, opns=True)


# ═══════════════════════════════════════════════════════════════
# IPNS round‑trip tests (Phase 3)
# ═══════════════════════════════════════════════════════════════


def test_create_point_ipns_round_trip(basis_p3):
    """Point(1,2,3) → IPNS (grade‑3) → analyze IPNS → Point(1,2,3)."""
    mv = create_entity(basis_p3, Point(1, 2, 3), opns=False)
    assert set(mv.grades) == {3}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(2)
    assert result.z == pytest.approx(3)


def test_create_direction_ipns_round_trip(basis_p3):
    """Direction(1,0,0) → IPNS (grade‑3) → analyze IPNS → Direction(1,0,0)."""
    mv = create_entity(basis_p3, Direction(1, 0, 0), opns=False)
    assert set(mv.grades) == {3}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Direction)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(0)
    assert result.z == pytest.approx(0)


def test_create_line_ipns_round_trip(basis_p3):
    """Line → IPNS → analyze IPNS → Line with correct direction."""
    line = Line(origin=Point(1, 2, 3), direction=Direction(0, 0, 1))
    mv = create_entity(basis_p3, line, opns=False)
    assert set(mv.grades) == {2}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Line)
    assert abs(result.direction.z) == pytest.approx(1)
    # origin may differ due to orthogonalization; direction is the invariant


def test_create_space_ipns_round_trip(basis_p3):
    """Space(scale=3) → IPNS (grade‑0 scalar) → analyze IPNS → Space(3)."""
    mv = create_entity(basis_p3, Space(scale=3.0), opns=False)
    assert set(mv.grades) == {0}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(3)
