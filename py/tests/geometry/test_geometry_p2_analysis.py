# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Christian Perwass

"""P2 entity & operator round-trip and application tests.

Follows the test guide: dev/todos/test-guide-algebra-round-trip.md

P2 (Cl(3)) uses homogeneous coordinates: Hop(a) = a + e₃.
Points and lines at any position are representable.
Planes are not supported in 2D (use Line instead).
Operators are restricted to those passing through the origin:
Rotor, ReflectionLine (origin-only), ReflectionPoint (origin-only).
"""

from __future__ import annotations

import math

import pytest
from pytanga.basis import BasisP2
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Point, Space
from pytanga.geometry.operators import (
    ReflectionLine,
    ReflectionPoint,
    Rotor,
)


@pytest.fixture(scope="module")
def b():
    return BasisP2()


# ═══════════════════════════════════════════════════════════════
# Entity round-trips
# ═══════════════════════════════════════════════════════════════

# --- E1. Point ---


def test_entity_point_opns_round_trip(b):
    """E1: create Point(3,-2) → analyze → assert exact fields."""
    mv = create_entity(b, Point(3, -2, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3)
    assert r.y == pytest.approx(-2)
    assert r.z == pytest.approx(0)


# --- E2. Direction ---


def test_entity_direction_opns_round_trip(b):
    """E2: create Direction(1,2) → analyze → assert exact fields."""
    mv = create_entity(b, Direction(1, 2, 0))
    r = analyze_entity(mv)
    assert isinstance(r, Direction), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(1)
    assert r.y == pytest.approx(2)
    assert r.z == pytest.approx(0)


# --- E3. Line ---


def test_entity_line_opns_round_trip(b):
    """E3: create Line(origin=(1,2), dir=(1,2)) → analyze → assert.

    Note: blade_factorize orthogonalizes factors, so the extracted
    origin point may differ from the input origin.  Direction is
    verified up to sign (parallel) since factorization order may swap
    the two point factors.
    """
    direction = Direction(1, 2, 0)
    unit = direction.normalized()
    pt = Point(1, 2, 0)
    mv = create_entity(b, Line(pt, direction))
    r = analyze_entity(mv)
    assert isinstance(r, Line), f"Got {type(r).__name__}"

    # Direction is parallel to expected (dot = ±1)
    dot = r.direction.x * unit.x + r.direction.y * unit.y
    assert abs(dot) == pytest.approx(1.0, abs=1e-6)

    # Analyzed origin must lie on the line: 2D cross product (dx*dy2 - dy*dx2 = 0)
    dx = r.origin.x - pt.x
    dy = r.origin.y - pt.y
    cross = direction.x * dy - direction.y * dx
    assert cross == pytest.approx(0, abs=1e-6)


# --- E4. Space ---


def test_entity_space_opns_round_trip(b):
    """E4: create Space(scale=2.5) → analyze → assert scale."""
    mv = create_entity(b, Space(scale=2.5))
    r = analyze_entity(mv)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(2.5)


# ═══════════════════════════════════════════════════════════════
# Scale-by-2 correctness (a global scale must not change geometry)
# ═══════════════════════════════════════════════════════════════


def test_scale2_point_invariant(b):
    mv = create_entity(b, Point(3, -2, 0)) * 2.0
    r = analyze_entity(mv)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3, abs=1e-6)
    assert r.y == pytest.approx(-2, abs=1e-6)
    assert r.z == pytest.approx(0, abs=1e-6)


def test_scale2_line_invariant(b):
    direction = Direction(1, 2, 0)
    unit = direction.normalized()
    pt = Point(1, 2, 0)
    mv = create_entity(b, Line(pt, direction)) * 2.0
    r = analyze_entity(mv)
    assert isinstance(r, Line), f"Got {type(r).__name__}"

    # Direction is parallel to expected (dot = ±1)
    dot = r.direction.x * unit.x + r.direction.y * unit.y
    assert abs(dot) == pytest.approx(1.0, abs=1e-6)

    # Analyzed origin must lie on the line (2D cross product)
    dx = r.origin.x - pt.x
    dy = r.origin.y - pt.y
    cross = direction.x * dy - direction.y * dx
    assert cross == pytest.approx(0, abs=1e-6)


def test_scale2_space_doubles(b):
    mv = create_entity(b, Space(scale=2.5)) * 2.0
    r = analyze_entity(mv)
    assert isinstance(r, Space), f"Got {type(r).__name__}"
    assert r.scale == pytest.approx(5.0, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# Operator round-trips
# ═══════════════════════════════════════════════════════════════

# --- O1. Rotor ---


def test_operator_rotor_round_trip(b):
    """O1: create Rotor(π/2) → analyze → assert angle.

    In 2D, the rotation axis is always the pseudoscalar e₁₂ (z-axis).
    Analysis returns positive angle via acos(|dot|).
    """
    mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    r = analyze_operator(mv)
    assert isinstance(r, Rotor), f"Got {type(r).__name__}"
    assert r.angle == pytest.approx(math.pi / 2)
    # Axis is always z in 2D, sign may flip
    assert abs(r.axis.z) == pytest.approx(1)


# --- O2. ReflectionLine ---


def test_operator_reflection_line_round_trip(b):
    """O2: create ReflectionLine(x-axis, through origin) → analyze → assert.

    P2 reflection line versor is N∧e₃ where N = (nx, ny).
    Direction is read directly from bivector coefficients — no
    factorization, so sign is preserved exactly.
    """
    mv = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    r = analyze_operator(mv)
    assert isinstance(r, ReflectionLine), f"Got {type(r).__name__}"
    assert r.line.direction.x == pytest.approx(1)
    assert r.line.direction.y == pytest.approx(0, abs=1e-10)


# --- O3. ReflectionPoint ---


def test_operator_reflection_point_origin_round_trip(b):
    """O3: create ReflectionPoint(origin) → analyze → assert origin.

    P2 only supports point reflection at the origin (the versor is
    simply e₃ — Hop(0)).  Non-origin point reflections are
    representable only in N2 (requires e∞).
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


def test_apply_rotor_point_rotation(b):
    """A1: Rotor(90°) on (1,0) → Point(0,1).

    First-principles derivation: rotating (1,0) by 90° in 2D about
    the origin produces (0,1).
    """
    p = create_entity(b, Point(1, 0, 0))
    R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(0, abs=1e-6)
    assert r.y == pytest.approx(1, abs=1e-6)


def test_apply_rotor_point_rotation_half_turn(b):
    """A1b: Rotor(180°) on (3,-2) → Point(-3,2).

    180° rotation about the origin negates both coordinates.
    """
    p = create_entity(b, Point(3, -2, 0))
    R = create_operator(b, Rotor(math.pi, Direction(0, 0, 1)))
    result = R.gp(p).gp(R.rev())
    r = analyze_entity(result)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-3, abs=1e-6)
    assert r.y == pytest.approx(2, abs=1e-6)


# --- A2. ReflectionLine ---


def test_apply_reflection_line_point_mirror_x(b):
    """A2: ReflectionLine(x-axis) on (3,2) → Point(3,-2).

    Reflection across the x-axis (line through origin along x):
    the x-coordinate stays unchanged; y flips sign.
    """
    p = create_entity(b, Point(3, 2, 0))
    L = create_operator(b, ReflectionLine(Direction(1, 0, 0)))
    result = L.gp(p).gp(L.rev())
    r = analyze_entity(result)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(3, abs=1e-6)
    assert r.y == pytest.approx(-2, abs=1e-6)


# --- A3. ReflectionPoint ---


def test_apply_reflection_point_origin_negation(b):
    """A3: ReflectionPoint(origin) on (5,-3) → Point(-5,3).

    Reflection in the origin negates both coordinates.
    e₃ · Hop(a) · e₃ projects to −a.
    """
    p = create_entity(b, Point(5, -3, 0))
    O = create_operator(b, ReflectionPoint(Point(0, 0, 0)))
    result = O.gp(p).gp(O.rev())
    r = analyze_entity(result)
    assert isinstance(r, Point), f"Got {type(r).__name__}"
    assert r.x == pytest.approx(-5, abs=1e-6)
    assert r.y == pytest.approx(3, abs=1e-6)


# ═══════════════════════════════════════════════════════════════
# Defensive tests
# ═══════════════════════════════════════════════════════════════


def test_create_direction_zero_norm_raises(b):
    """create_entity(Direction(0,0,0)) must raise ValueError."""
    with pytest.raises(ValueError, match="Zero.*norm"):
        create_entity(b, Direction(0, 0, 0))


def test_analyze_zero_vector_raises(b):
    """Zero MV passed to analyze_entity must raise ValueError."""
    zero = b.multivector({})
    with pytest.raises(ValueError):
        analyze_entity(zero)


# ═══════════════════════════════════════════════════════════════
# N2-only entities and operators — must raise in P2
# ═══════════════════════════════════════════════════════════════

from pytanga.geometry.entities import Circle, HPoint, PointPair, Sphere
from pytanga.geometry.operators import (
    Dilator,
    GeneralRotor,
    Inversion,
    Motor,
    Translator,
)


@pytest.mark.parametrize(
    "entity_cls,args",
    [
        (Sphere, (Point(0, 0, 0), 1.0)),
        (Circle, (Point(0, 0, 0), 1.0, Direction(0, 0, 1))),
        (PointPair, (Point(0, 0, 0), Point(1, 0, 0))),
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
    ],
)
def test_n2_operator_raises(b, op_cls, args):
    with pytest.raises(ValueError, match="N2"):
        create_operator(b, op_cls(*args))