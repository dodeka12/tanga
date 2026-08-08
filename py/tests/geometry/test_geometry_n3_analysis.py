# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""N3 entity & operator round-trip and application tests.

Follows the test guide: dev/todos/test-guide-algebra-round-trip.md
Test plan: dev/todos/test-plan-n3-analysis.md
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisN3
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import *
from pytanga.geometry.operators import *


@pytest.fixture(scope="module")
def b():
    return BasisN3()


# ═══════════════════════════════════════════════════════════════
# Entity round-trips
# ═══════════════════════════════════════════════════════════════

# --- E1. Point ---


def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2,7) → analyze → assert exact."""
    mv = create_entity(b, Point(3, -2, 7))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(7)


# --- E2. Direction ---


def test_entity_direction_opns_round_trip(b):
    """E2: create Direction(1,2,0) → analyze → assert exact."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


# --- E3. PointPair ---


def test_entity_point_pair_opns_round_trip(b):
    """E3: create PointPair → analyze → assert midpoint, separation, direction."""
    a = Point(1, 0, 1)
    b_p = Point(3, 0, 2)
    mv = create_entity(b, PointPair(a, b_p))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, PointPair), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    # Verify midpoint
    mid = Point((a.x + b_p.x) / 2, (a.y + b_p.y) / 2, (a.z + b_p.z) / 2)
    r_mid = Point(
        (r.point_a.x + r.point_b.x) / 2,
        (r.point_a.y + r.point_b.y) / 2,
        (r.point_a.z + r.point_b.z) / 2,
    )
    assert r_mid.x == pytest.approx(mid.x)
    assert r_mid.y == pytest.approx(mid.y)
    assert r_mid.z == pytest.approx(mid.z)
    # Verify separation
    sep = math.sqrt((b_p.x - a.x) ** 2 + (b_p.y - a.y) ** 2 + (b_p.z - a.z) ** 2)
    r_sep = math.sqrt(
        (r.point_b.x - r.point_a.x) ** 2
        + (r.point_b.y - r.point_a.y) ** 2
        + (r.point_b.z - r.point_a.z) ** 2
    )
    assert r_sep == pytest.approx(sep)
    # Verify point_a along −dir, point_b along +dir
    d = Direction(b_p.x - a.x, b_p.y - a.y, b_p.z - a.z)
    r_d = Direction(
        r.point_b.x - r.point_a.x,
        r.point_b.y - r.point_a.y,
        r.point_b.z - r.point_a.z,
    )
    assert r_d.x == pytest.approx(d.x)
    assert r_d.y == pytest.approx(d.y)
    assert r_d.z == pytest.approx(d.z)


# --- E4. HPoint ---


def test_entity_hpoint_opns_round_trip(b):
    """E4: create HPoint(Point(2,-1,3), weight=2.5) → analyze → assert."""
    mv = create_entity(b, HPoint(Point(2, -1, 3), weight=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, HPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(2)
    assert r.point.y == pytest.approx(-1)
    assert r.point.z == pytest.approx(3)
    assert r.weight == pytest.approx(2.5)


# --- E5. Line ---


def test_entity_line_opns_round_trip(b):
    """E5: create Line(origin=(1,2,3), dir=(1,2,0)) → analyze → assert."""
    direction = Direction(1, 2, 0)
    unit = direction.norm()
    pt = Point(1, 2, 3)
    mv = create_entity(b, Line(pt, direction))
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


# --- E6. Circle ---


def test_entity_circle_opns_round_trip(b):
    """E6: create Circle(center=(1,0,2), normal=(0,1,0), radius=2.5) → analyze."""
    normal = Direction(0, 1, 0)
    unit = normal.norm()
    mv = create_entity(b, Circle(Point(1, 0, 2), normal, 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Circle), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(1)
    assert r.center.y == pytest.approx(0)
    assert r.center.z == pytest.approx(2)
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)
    assert r.radius == pytest.approx(2.5)


# --- E7. Plane ---


def test_entity_plane_opns_round_trip(b):
    """E7: create Plane(point=(3,-2,1), normal=(1,3,0)) → analyze → assert."""
    normal = Direction(1, 3, 0)
    unit = normal.norm()
    pt = Point(3, -2, 1)
    mv = create_entity(b, Plane(pt, normal))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"
    # Normal must match the unit-length direction
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)
    # Analyzed point must lie on the plane: n·p = d
    d = normal.x * pt.x + normal.y * pt.y + normal.z * pt.z
    d_scaled = d / normal.mag()
    d_analyzed = (
        r.normal.x * r.point.x + r.normal.y * r.point.y + r.normal.z * r.point.z
    )
    assert d_analyzed == pytest.approx(d_scaled)


# --- E8. Sphere ---


def test_entity_sphere_opns_round_trip(b):
    """E8: create Sphere(center=(2,-1,3), radius=2.5) → analyze → assert."""
    mv = create_entity(b, Sphere(Point(2, -1, 3), 2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Sphere), f"Got {type(r).__name__}"
    assert not r.is_imaginary
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(3)
    assert r.radius == pytest.approx(2.5)


# --- E9. Space ---


def test_entity_space_opns_round_trip(b):
    """E9: create Space(scale=2.5) → analyze → assert."""
    mv = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)


# ═══════════════════════════════════════════════════════════════
# Operator round-trips
# ═══════════════════════════════════════════════════════════════

# --- O1. Rotor ---


def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2, z-axis) → analyze → assert angle & axis.

    Analysis returns positive angle; axis sign may flip (both equivalent).
    """
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    # Axis collinear with z — sign may flip
    assert r.axis.z == pytest.approx(1) or r.axis.z == pytest.approx(-1)
    assert r.axis.x == pytest.approx(0, abs=1e-10)
    assert r.axis.y == pytest.approx(0, abs=1e-10)


# --- O2. Translator ---


def test_operator_translator_round_trip(b):
    """O2: create Translator(2,-1,3) → analyze → assert vector.

    N3 convention: T = 1 − ½·t·e∞
    """
    mv = create_operator(b, Translator(Direction(2, -1, 3)))
    r = analyze_operator(mv)
    assert isinstance(r, Translator), f"Got {type(r).__name__}"
    assert r.vector.x == pytest.approx(2)
    assert r.vector.y == pytest.approx(-1)
    assert r.vector.z == pytest.approx(3)


# --- O3. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O3: create ReflectionLine(direction=(1,2,0)) → analyze → assert direction."""
    mv = create_operator(b, ReflectionLine(Direction(1, 2, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    unit = Direction(1, 2, 0).norm()
    assert r.direction.x == pytest.approx(unit.x)
    assert r.direction.y == pytest.approx(unit.y)
    assert r.direction.z == pytest.approx(unit.z)


# --- O4. ReflectionPlane ---


def test_operator_reflection_plane_round_trip(b):
    """O4: create ReflectionPlane(normal=(0,0,1)) → analyze → assert normal."""
    mv = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPlane), f"Got {type(r).__name__}"
    assert r.normal.x == pytest.approx(0)
    assert r.normal.y == pytest.approx(0)
    assert r.normal.z == pytest.approx(1)


# --- O5. ReflectionOrigin ---


def test_operator_reflection_origin_round_trip(b):
    """O5: create ReflectionOrigin → analyze → assert type (no fields)."""
    mv = create_operator(b, ReflectionOrigin())
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionOrigin), f"Got {type(r).__name__}"


# --- O6. Inversion ---


def test_operator_inversion_round_trip(b):
    """O6: create Inversion(center=(2,-1,3), radius=2.5) → analyze → assert."""
    mv = create_operator(b, Inversion(Point(2, -1, 3), 2.5))
    r = analyze_operator(mv)
    assert isinstance(r, Inversion), f"Got {type(r).__name__}"
    assert r.center.x == pytest.approx(2)
    assert r.center.y == pytest.approx(-1)
    assert r.center.z == pytest.approx(3)
    assert r.radius == pytest.approx(2.5)


# --- O7. Dilator (origin) ---


def test_operator_dilator_origin_round_trip(b):
    """O7: create Dilator(factor=2.0) → analyze → assert factor, origin=(0,0,0)."""
    mv = create_operator(b, Dilator(2.0))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(0)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)


# --- O8. Dilator (displaced) ---


def test_operator_dilator_displaced_round_trip(b):
    """O8: create Dilator(factor=2.0, origin=(1,0,0)) → analyze → assert factor & origin."""
    mv = create_operator(b, Dilator(2.0, origin=Point(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, Dilator), f"Got {type(r).__name__}"
    assert r.factor == pytest.approx(2.0)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)


# --- O9. Motor ---


def test_operator_motor_round_trip(b):
    """O9: create Motor(T(0,0,1), R(π/2, z)) → analyze → assert both parts."""
    mv = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(0, 0, 1)),
        ),
    )
    r = analyze_operator(mv)
    assert isinstance(r, Motor), f"Got {type(r).__name__}"
    assert r.rotor.angle == pytest.approx(math.pi / 2)
    assert r.rotor.axis.z == pytest.approx(1) or r.rotor.axis.z == pytest.approx(-1)
    assert r.translator.vector.x == pytest.approx(0)
    assert r.translator.vector.y == pytest.approx(0)
    assert r.translator.vector.z == pytest.approx(1)


# --- O10. GeneralRotor ---


def test_operator_general_rotor_round_trip(b):
    """O10: create GeneralRotor(π/2, z-axis, origin=(1,0,0)) → analyze."""
    mv = create_operator(
        b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))
    )
    r = analyze_operator(mv)
    assert isinstance(r, GeneralRotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    assert r.axis.x == pytest.approx(0)
    assert r.axis.y == pytest.approx(0)
    assert r.axis.z == pytest.approx(1) or r.axis.z == pytest.approx(-1)
    assert r.origin.x == pytest.approx(1)
    assert r.origin.y == pytest.approx(0)
    assert r.origin.z == pytest.approx(0)


# ═══════════════════════════════════════════════════════════════
# Application tests
# ═══════════════════════════════════════════════════════════════

# --- A1. Translator ---


def test_apply_translator_point_displacement(b):
    """A1: Translator(3,0,0) applied to origin → Point(3,0,0)."""
    p = create_entity(b, Point(0, 0, 0))
    T = create_operator(b, Translator(Direction(3, 0, 0)))
    result = T.gp(p).gp(T.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


# --- A2. Rotor ---


def test_apply_rotor_point_rotation_z(b):
    """A2: Rotor(90°, z) on (1,0,0) → Point(0,1,0)."""
    p = create_entity(b, Point(1, 0, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)


# --- A6. Inversion ---


def test_apply_inversion_point_scaling(b):
    """A6: Inversion at origin r=1 on (2,0,0) → Point(0.5,0,0).

    Spherical inversion: p → p·r²/|p|².
    Point (2,0,0) with r=1 → (2·1/4, 0, 0) = (0.5, 0, 0).
    """
    p = create_entity(b, Point(2, 0, 0))
    S = create_operator(b, Inversion(Point(0, 0, 0), 1.0))
    result = S.gp(p).gp(S.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0.5)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


# --- A7. Dilator (origin) ---


def test_apply_dilator_origin_point_scaling(b):
    """A7: Dilator(2.0) on (3,0,0) → Point(6,0,0).

    Dilator scales about the origin by factor d.
    """
    p = create_entity(b, Point(3, 0, 0))
    D = create_operator(b, Dilator(2.0))
    result = D.gp(p).gp(D.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(6)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


# --- A8. Dilator (displaced) ---


def test_apply_dilator_displaced_point_scaling(b):
    """A8: Dilator(2.0, origin=(1,0,0)) on (2,0,0) → Point(3,0,0).

    General dilator: T·D·T̃.  Relative to center (1,0,0):
    (2,0,0) − (1,0,0) = (1,0,0) → scale by 2 → (2,0,0) + center = (3,0,0).
    """
    p = create_entity(b, Point(2, 0, 0))
    D = create_operator(b, Dilator(2.0, origin=Point(1, 0, 0)))
    result = D.gp(p).gp(D.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(0)
    assert r.z == pytest.approx(0)


# --- A9. Motor ---


def test_apply_motor_point_rigid_motion(b):
    """A9: Motor(T(1,2,3), R(90°, z)) on (1,0,0) → Point(1,3,3).

    Motor = T · R: first rotate, then translate.
    (1,0,0) → rotate 90° about z → (0,1,0) → translate (1,2,3) → (1,3,3).
    """
    p = create_entity(b, Point(1, 0, 0))
    M = create_operator(
        b,
        Motor(
            rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
            translator=Translator(Direction(1, 2, 3)),
        ),
    )
    result = M.gp(p).gp(M.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(3, abs=1e-6)
    assert r.z == pytest.approx(3, abs=1e-6)


# --- A10. GeneralRotor ---


def test_apply_general_rotor_point_displaced_rotation(b):
    """A10: GeneralRotor(90°, z, at x=1) on (2,0,0) → Point(1,1,0).

    GeneralRotor(π/2, z-axis, origin=(1,0,0)) rotates about z-axis through x=1.
    Point (2,0,0): subtract center → (1,0,0), rotate 90° about z → (0,1,0),
    add center → (1,1,0).
    """
    p = create_entity(b, Point(2, 0, 0))
    G = create_operator(
        b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))
    )
    result = G.gp(p).gp(G.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)
