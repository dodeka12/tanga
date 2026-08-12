# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""P3 entity & operator round-trip and application tests.

Follows the test guide: dev/todos/test-guide-algebra-round-trip.md

P3 (Cl(4)) uses homogeneous coordinates: Hop(a) = a + e₄.
Points, lines, and planes at any position are representable.
Operators are restricted to those passing through the origin:
Rotor, ReflectionLine (origin-only), ReflectionPlane (origin-only),
ReflectionPoint (origin-only).
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
    ReflectionPoint,
    Rotor,
)


@pytest.fixture(scope="module")
def b():
    return BasisP3()


# ═══════════════════════════════════════════════════════════════
# Entity round-trips
# ═══════════════════════════════════════════════════════════════

# --- E1. Point ---


def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2,7) → analyze → assert exact fields."""
    mv = create_entity(b, Point(3, -2, 7))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(7)


# --- E2. Direction ---


def test_entity_direction_opns_round_trip(b):
    """E2: create Direction(1,2,0) → analyze → assert exact fields."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


# --- E3. Line ---


def test_entity_line_opns_round_trip(b):
    """E3: create Line(origin=(1,2,3), dir=(1,2,0)) → analyze → assert.

    Note: blade_factorize orthogonalizes factors, so the extracted
    origin point may differ from the input origin.  Direction is
    verified up to sign (parallel) since factorization order may swap
    the two point factors.
    """
    direction = Direction(1, 2, 0)
    unit = direction.normalized()
    pt = Point(1, 2, 3)
    mv = create_entity(b, Line(pt, direction))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Line), f"Got {type(r).__name__}"

    # Direction is parallel to expected (dot = ±1)
    dot = r.direction.x * unit.x + r.direction.y * unit.y + r.direction.z * unit.z
    assert abs(dot) == pytest.approx(1.0, abs=1e-6)

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


# --- E4. Plane ---


def test_entity_plane_opns_round_trip(b):
    """E4: create Plane(point=(3,-2,1), normal=(1,3,0)) → analyze → assert."""
    normal = Direction(1, 3, 0)
    unit = normal.normalized()
    pt = Point(3, -2, 1)
    mv = create_entity(b, Plane(pt, normal))
    r = analyze_entity(mv, opns=True)
    assert isinstance(r, Plane), f"Got {type(r).__name__}"

    # Normal must match the unit-length direction exactly
    assert r.normal.x == pytest.approx(unit.x)
    assert r.normal.y == pytest.approx(unit.y)
    assert r.normal.z == pytest.approx(unit.z)

    # Analyzed point must lie on the plane: n·p = d
    d_expected = normal.x * pt.x + normal.y * pt.y + normal.z * pt.z
    d_expected_scaled = d_expected / normal.mag()
    d_analyzed = (
        r.normal.x * r.point.x
        + r.normal.y * r.point.y
        + r.normal.z * r.point.z
    )
    assert d_analyzed == pytest.approx(d_expected_scaled)


# --- E5. Space ---


def test_entity_space_opns_round_trip(b):
    """E5: create Space(scale=2.5) → analyze → assert scale."""
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
    """O2: create ReflectionLine(x-axis, through origin) → analyze → assert.

    P3 reflection line versor is N∧e₄ where N = (nx, ny, nz).
    Direction is read directly from bivector coefficients — no
    factorization, so sign is preserved exactly.
    """
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    assert r.line.direction.x == pytest.approx(1)
    assert r.line.direction.y == pytest.approx(0, abs=1e-10)
    assert r.line.direction.z == pytest.approx(0, abs=1e-10)


# --- O3. ReflectionPlane ---


def test_operator_reflection_plane_round_trip(b):
    """O3: create ReflectionPlane(z-normal) → analyze → assert normal.

    P3 reflection plane versor is the unit normal vector (grade 1,
    e₄=0).  Normal is preserved exactly.
    """
    mv = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPlane), f"Got {type(r).__name__}"
    assert r.plane.normal.x == pytest.approx(0, abs=1e-10)
    assert r.plane.normal.y == pytest.approx(0, abs=1e-10)
    assert r.plane.normal.z == pytest.approx(1)


# --- O4. ReflectionPoint ---


def test_operator_reflection_point_origin_round_trip(b):
    """O4: create ReflectionPoint(origin) → analyze → assert origin.

    P3 only supports point reflection at the origin (the versor is
    simply e₄ — Hop(0)).  Non-origin point reflections are
    representable only in N3 (requires e∞).
    """
    mv = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionPoint), f"Got {type(r).__name__}"
    assert r.point.x == pytest.approx(0)
    assert r.point.y == pytest.approx(0)
    assert r.point.z == pytest.approx(0)


# ═══════════════════════════════════════════════════════════════
# Operator application tests
# ═══════════════════════════════════════════════════════════════

# --- A1. Rotor ---


def test_apply_rotor_point_rotation_z(b):
    """A1: Rotor(90°, z) on (1,0,0) → Point(0,1,0).

    First-principles derivation: rotating (1,0,0) by 90° about the
    z-axis produces (0,1,0).
    """
    p = create_entity(b, Point(1, 0, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)
    assert r.z == pytest.approx(0)


def test_apply_rotor_point_rotation_x(b):
    """A1b: Rotor(90°, x) on (0,1,0) → Point(0,0,1).

    +90° about x-axis (right‑hand rule): e₂ → e₃.
    """
    p = create_entity(b, Point(0, 1, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(1, 0, 0)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(0, abs=1e-6)
    assert r.z == pytest.approx(1)


def test_apply_rotor_point_rotation_y(b):
    """A1c: Rotor(90°, y) on (0,0,1) → Point(1,0,0).

    +90° about y-axis (right‑hand rule): e₃ → e₁.
    """
    p = create_entity(b, Point(0, 0, 1))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 1, 0)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(0, abs=1e-6)
    assert r.z == pytest.approx(0)


# --- A2. ReflectionLine ---


def test_apply_reflection_line_point_mirror_x(b):
    """A2: ReflectionLine(x-axis) on (3,1,0) → Point(3,-1,0).

    Reflection across the x-axis (line through origin along x):
    the x-coordinate stays unchanged; y and z flip sign.
    """
    p = create_entity(b, Point(3, 1, 0))
    L = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    result = L.gp(p).gp(L.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3, abs=1e-6)
    assert r.y == pytest.approx(-1, abs=1e-6)
    assert r.z == pytest.approx(0, abs=1e-6)


# --- A3. ReflectionPlane ---


def test_apply_reflection_plane_point_mirror_z(b):
    """A3: ReflectionPlane(z=0, normal z) on (1,2,5) → Point(1,2,-5).

    Reflection across the xy-plane (plane through origin, normal z):
    x and y stay; z flips sign.
    """
    p = create_entity(b, Point(1, 2, 5))
    F = create_operator(b, ReflectionPlane(Direction(0, 0, 1)))
    result = F.gp(p).gp(F.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)
    assert r.z == pytest.approx(-5, abs=1e-6)


# --- A4. ReflectionPoint ---


def test_apply_reflection_point_origin_negation(b):
    """A4: ReflectionPoint(origin) on (5,-3,2) → Point(-5,3,-2).

    Reflection in the origin negates all coordinates.
    e₄ · Hop(a) · e₄ projects to −a.
    """
    p = create_entity(b, Point(5, -3, 2))
    O = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    result = O.gp(p).gp(O.rev())
    r = analyze_entity(result, opns=True)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-5, abs=1e-6)
    assert r.y == pytest.approx(3, abs=1e-6)
    assert r.z == pytest.approx(-2, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# Defensive tests
# ═══════════════════════════════════════════════════════════════


def test_analyze_non_simple_bivector_raises(b):
    """Non‑simple bivector (B∧B ≠ 0) must raise ValueError."""
    line1 = create_entity(
        b, Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
    )
    line2 = create_entity(
        b, Line(origin=Point(0, 1, 0), direction=Direction(0, 0, 1))
    )
    non_simple = line1 + line2
    with pytest.raises(ValueError, match="Non.*simple"):
        analyze_entity(non_simple, opns=True)


def test_create_direction_zero_norm_raises(b):
    """create_entity(Direction(0,0,0)) must raise ValueError."""
    with pytest.raises(ValueError, match="Zero.*norm"):
        create_entity(b, Direction(0, 0, 0))


def test_analyze_zero_vector_raises(b):
    """Zero MV passed to analyze_entity must raise ValueError."""
    zero = b.multivector({})
    with pytest.raises(ValueError):
        analyze_entity(zero, opns=True)


# ═══════════════════════════════════════════════════════════════
# N3-only entities and operators — must raise in P3
# ═══════════════════════════════════════════════════════════════

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import Dilator, GeneralRotor, Inversion, Motor, Translator


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
    ],
)
def test_n3_operator_raises(b, op_cls, args):
    with pytest.raises(ValueError, match="N3"):
        create_operator(b, op_cls(*args))
