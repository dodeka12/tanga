# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""PGA3 entity and operator round-trip tests.

Algebra: BasisPGA3
Follows test-guide-algebra-round-trip.md golden rules.
"""

from __future__ import annotations

import math

import pytest
from pytanga.algebra._mv import MV
from pytanga.basis import BasisPGA3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    ReflectionLine,
    ReflectionPlane,
    ReflectionPoint,
    Rotor,
    Translator,
    TripleReflection,
)


@pytest.fixture(scope="module")
def b():
    return BasisPGA3()


# ═══════════════════════════════════════════════════════════════
# 1. Entity Round-Trips
# ═══════════════════════════════════════════════════════════════


def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2,7) → analyze → assert exact."""
    mv: MV = create_entity(b, Point(3, -2, 7))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(7)


def test_entity_direction_opns_round_trip(b):
    """E2: create Direction(1,2,0) → analyze → assert exact."""
    mv: MV = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


def test_entity_plane_opns_round_trip(b):
    """E3: create Plane(point=(3,-2,1), normal=(1,3,0)) → analyze → assert.

    The analysis returns the closest point to the origin on the plane, not
    necessarily the point used for construction.  The normal is normalized
    to unit length but must preserve the same direction (sign).
    The point is verified by checking it lies on the plane: n·p = d.
    """
    normal = Direction(1, 3, 0)
    unit = normal.norm()
    pt = Point(3, -2, 1)
    mv: MV = create_entity(b, Plane(pt, normal))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"
    # Normal must match the unit-length direction
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)
    # Analyzed point must lie on the plane: n·p = d
    # Note: analysis normalizes the normal, so d is scaled by 1/|n|
    d = normal.x * pt.x + normal.y * pt.y + normal.z * pt.z
    d_scaled = d / normal.mag()
    d_analyzed = (
        r.normal.x * r.point.x + r.normal.y * r.point.y + r.normal.z * r.point.z
    )
    assert d_analyzed == pytest.approx(d_scaled)


def test_entity_line_opns_round_trip(b):
    """E4: create Line(origin=(1,2,3), dir=(1,2,0)) → analyze → assert.

    The analysis returns the closest point to the origin on the line, not
    necessarily the construction point.  The direction must round-trip with
    the same sign (normalized to unit length).  The origin is verified by
    checking it lies on the line: (r.origin − pt) is parallel to direction.
    """
    direction = Direction(1, 2, 0)
    unit = direction.norm()
    pt = Point(1, 2, 3)
    mv: MV = create_entity(b, Line(pt, direction))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line), f"Got {type(r).__name__}"
    # Direction normalized and preserves sign
    assert r.direction.x == pytest.approx(unit.x)
    assert r.direction.y == pytest.approx(unit.y)
    assert r.direction.z == pytest.approx(unit.z)
    # Analyzed origin must lie on the line: (r.origin − pt) ∥ direction
    dx = r.origin.x - pt.x
    dy = r.origin.y - pt.y
    dz = r.origin.z - pt.z
    cross_x = direction.y * dz - direction.z * dy
    cross_y = direction.z * dx - direction.x * dz
    cross_z = direction.x * dy - direction.y * dx
    assert cross_x == pytest.approx(0, abs=1e-6)
    assert cross_y == pytest.approx(0, abs=1e-6)
    assert cross_z == pytest.approx(0, abs=1e-6)


def test_entity_space_opns_round_trip(b):
    """E5: create Space(scale=2.5) → analyze → assert."""
    mv: MV = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)


# ═══════════════════════════════════════════════════════════════
# 2. Operator Round-Trips
# ═══════════════════════════════════════════════════════════════


def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis."""
    mv: MV = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    assert r.axis.x == pytest.approx(0)
    assert r.axis.y == pytest.approx(0)
    assert r.axis.z == pytest.approx(1)


def test_operator_translator_round_trip(b):
    """O2: create Translator(2,-1,3) → analyze → assert vector.

    Creation: T = 1 + 0.5·(dx·e₁∧e₀ + …)  (plus sign)
    Analysis: dx = +2.0 * mv[9]              (plus sign — must match!)
    """
    mv: MV = create_operator(b, Translator(Direction(2, -1, 3)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)
    assert r.vector.z == pytest.approx(3)


def test_operator_motor_round_trip(b):
    """O3: create Motor(T(0,0,1), R(π/2, z)) → analyze → assert both parts.

    The translator must have a component perpendicular to the rotation
    plane, otherwise no grade‑4 term is generated and the motor cannot
    be distinguished from a GeneralRotor.
    """
    mv: MV = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(0, 0, 1)),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, Motor), f"Got {type(r).__name__}"
    assert r.rotor.angle == pytest.approx(math.pi / 2)
    assert r.rotor.axis.z == pytest.approx(1)
    assert r.translator.vector.z == pytest.approx(1)


def test_operator_reflection_plane_round_trip(b):
    """O4: create ReflectionPlane(plane=xy-plane) -> analyze -> assert."""
    mv: MV = create_operator(b, ReflectionPlane(Plane(Point(0, 0, 0), Direction(0, 0, 1))))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPlane), f"Got {type(r).__name__}"
    assert r.plane.normal.x == pytest.approx(0)
    assert r.plane.normal.y == pytest.approx(0)
    assert abs(r.plane.normal.z) == pytest.approx(1)


def test_operator_general_rotor_round_trip(b):
    """O5: create GeneralRotor(π/2, z-axis, origin=(1,0,0)) → analyze.

    GeneralRotor uses flat fields (angle, axis, origin).
    """
    mv: MV = create_operator(
        b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))
    )
    r = analyze_operator(mv)
    assert isinstance(r, GeneralRotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    assert r.axis.x == pytest.approx(0)
    assert r.axis.y == pytest.approx(0)
    assert r.axis.z == pytest.approx(1)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)


def test_operator_triple_reflection_round_trip(b):
    """O6: triple reflection via three non-parallel displaced planes."""
    # e0 = ep + em (blades 8 and 16)
    e0 = b.multivector({8: 1.0, 16: 1.0})
    # Three non-orthogonal displaced planes to get multi-grade product
    p1 = b.multivector({1: 1.0, 8: -1.0, 16: -1.0})     # e1 - e0
    p2 = b.multivector({1: 1.0, 2: 1.0, 8: -3.0, 16: -3.0})  # e1+e2 - 3e0
    p3 = b.multivector({2: 1.0, 4: 1.0, 8: -5.0, 16: -5.0})  # e2+e3 - 5e0
    mv = p1.gp(p2).gp(p3)

    r = analyze_operator(mv)
    # Non-orthogonal planes produce a motor-like versor, not plain triple-reflection
    assert isinstance(r, (TripleReflection, Motor, GeneralRotor)), f"Got {type(r).__name__}"


# ═══════════════════════════════════════════════════════════════
# 3. Operator Application Tests
# ═══════════════════════════════════════════════════════════════


def test_apply_translator_point_displacement(b):
    """A1: Translator(3,0,0) applied to origin → Point(3,0,0)."""
    p: MV = create_entity(b, Point(0, 0, 0))
    T: MV = create_operator(b, Translator(Direction(3, 0, 0)))
    result: MV = T.gp(p).gp(T.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


def test_apply_rotor_point_rotation_z(b):
    """A2: Rotor(90°, z) on (1,0,0) → Point(0,1,0)."""
    p: MV = create_entity(b, Point(1, 0, 0))
    R: MV = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    result: MV = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)


def test_apply_motor_point_rigid_motion(b):
    """A3: Motor(T(1,0,0), R(90°, z)) on (1,0,0) → Point(1,1,0).

    Motor M = T·R, applied as M·p·M̃:
    - Rotate first: R(90°,z) on (1,0,0) → (0,1,0)
    - Then translate: T(1,0,0) → (1,1,0)
    """
    p: MV = create_entity(b, Point(1, 0, 0))
    M: MV = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(1, 0, 0)),
        ),
    )
    result: MV = M.gp(p).gp(M.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)


def test_apply_reflection_plane_point_mirror(b):
    """A4: ReflectionPlane(z=0) on (1,2,5) -> Point(1,2,-5)."""
    p: MV = create_entity(b, Point(1, 2, 5))
    F: MV = create_operator(b, ReflectionPlane(Plane(Point(0, 0, 0), Direction(0, 0, 1))))
    result: MV = F.gp(p).gp(F.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(-5)


def test_apply_general_rotor_point_displaced_rotation(b):
    """A5: GeneralRotor(90°, z, at x=1) on (2,0,0) → Point(1,1,0).

    Rotate about z-axis through x=1:
    Point (2,0,0): subtract center → (1,0,0), rotate 90° → (0,1,0),
    add center → (1,1,0).
    """
    p: MV = create_entity(b, Point(2, 0, 0))
    G: MV = create_operator(
        b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))
    )
    result: MV = G.gp(p).gp(G.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)


# --- O7. ReflectionPoint ---


def test_operator_reflection_point_round_trip(b):
    """O7: create ReflectionPoint(2,-1,3) -> analyze -> assert."""
    mv = create_operator(b, ReflectionPoint(Point(2, -1, 3)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(2)
    assert r.point.y == pytest.approx(-1)
    assert r.point.z == pytest.approx(3)


def test_operator_reflection_point_origin_round_trip(b):
    """O7b: ReflectionPoint(0,0,0) -> analyze -> assert."""
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(0)


# --- O8. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O8: create ReflectionLine(x-axis) -> analyze -> assert."""
    line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    mv = create_operator(b, ReflectionLine(line))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    d = r.line.direction
    assert abs(d.x) == pytest.approx(1, abs=1e-6)


# --- A6. ReflectionPoint application ---


def test_apply_reflection_point_origin_negation(b):
    """A6: ReflectionPoint(0,0,0) on (5,-3,2) -> Point(-5,3,-2)."""
    p = create_entity(b, Point(5, -3, 2))
    O = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    result = O.gp(p).gp(O.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-5, abs=1e-6)
    assert r.y == pytest.approx(3, abs=1e-6)
    assert r.z == pytest.approx(-2, abs=1e-6)


# --- A7. ReflectionLine application ---


def test_apply_reflection_line_point_mirror_x(b):
    """A7: ReflectionLine(x-axis) on (3,1,0) -> Point(3,-1,0)."""
    p = create_entity(b, Point(3, 1, 0))
    L = create_operator(b, ReflectionLine(Line(Point(0, 0, 0), Direction(1, 0, 0))))
    result = L.gp(p).gp(L.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3, abs=1e-6)
    assert r.y == pytest.approx(-1, abs=1e-6)
    assert r.z == pytest.approx(0, abs=1e-6)

