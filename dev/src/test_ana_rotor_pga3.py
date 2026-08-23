# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Test the ana_versor algorithm for Rotor/Translator/Motor/GeneralRotor in PGA3.

Round-trip: create → ana_versor → assert correct type and fields.
Application: re-create analyzed versor → apply to point → match original.

Run with: uv run python dev/src/test_ana_rotor_pga3.py
"""

from __future__ import annotations

import math

from pytanga.basis import BasisPGA3
from pytanga.geometry import Geometry
from pytanga.geometry.entities import Direction, Point
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    Rotor,
    Translator,
)

P3 = BasisPGA3()
geo = Geometry(P3)


# ═══════════════════════════════════════════════════════════════
# Streamlined versor analysis
# ═══════════════════════════════════════════════════════════════


def ana_versor(versor):
    """Analyze a PGA3 versor as Rotor, Translator, Motor, or GeneralRotor.

    Classification is based on grade content, not blade factorization:

    - Grade 0 + 2, no e₀-bivector      → Translator
    - Grade 0 + 2, no null bivector    → Rotor
    - Grade 0 + 2, both present        → GeneralRotor
    - Grade 0 + 2 + 4                  → Motor
    """
    s = versor.grade(0)[0]
    bi = versor.grade(2)
    q = versor.grade(4)

    # Project out e₀ bivector parts: bi_e is the pure Euclidean bivector
    bi_e = bi.op(P3.e0).ip(P3.e0_recip)
    bi_e_mag = bi_e.mag

    q_mag = q.mag

    # ── Motor (has grade-4 component) ──
    if q_mag > 1e-15:
        if bi_e_mag < 1e-15:
            raise ValueError("Motor has grade-4 but no Euclidean bivector")
        # Angle from the Euclidean part
        cos_a = s
        sin_a = bi_e_mag
        angle = 2.0 * math.atan2(sin_a, cos_a)
        # Axis = undual of Euclidean bivector: bi_e · e₁₂₃
        axis_mv = bi_e.ip(P3.multivector({P3.E123: 1.0}))
        axis = Direction(axis_mv["e1"], axis_mv["e2"], axis_mv["e3"])
        axis = axis.norm()

        # Factor out the pure rotation: trans = V * R⁻¹
        rot_pure = versor.grade(0) + bi_e
        trans = versor * rot_pure.inv()
        t_bi = trans.grade(2)
        tv = 2.0 * t_bi.ip(P3.e0_recip) / trans.grade(0)[0]

        return Motor(
            rotor=Rotor(angle=angle, axis=axis),
            translator=Translator(Direction(tv["e1"], tv["e2"], tv["e3"])),
        )

    # ── No Euclidean bivector → Translator ──
    if bi_e_mag < 1e-15:
        if abs(s) < 1e-15:
            raise ValueError("Zero scalar — not a valid versor")
        tv = 2.0 * bi.ip(P3.e0_recip) / s
        return Translator(Direction(tv["e1"], tv["e2"], tv["e3"]))

    # ── Angle + axis (shared by Rotor & GeneralRotor) ──
    cos_a = s
    sin_a = bi_e_mag
    angle = 2.0 * math.atan2(sin_a, cos_a)
    axis_mv = bi_e.ip(P3.multivector({P3.E123: 1.0}))
    axis = Direction(axis_mv["e1"], axis_mv["e2"], axis_mv["e3"])
    axis = axis.norm()

    # ── Pure Rotor vs GeneralRotor ──
    tb = bi.ip(P3.e0_recip)  # null bivector part
    if tb.mag < 1e-15:
        return Rotor(angle=angle, axis=axis)

    # GeneralRotor: rotation origin = tb · bi_e⁻¹
    t = tb.ip(bi_e.inv())
    return GeneralRotor(
        angle=angle,
        axis=axis,
        origin=Point(t["e1"], t["e2"], t["e3"]),
    )


# ═══════════════════════════════════════════════════════════════
# Test helpers
# ═══════════════════════════════════════════════════════════════


def assert_close(a, b, tol=1e-6, label=""):
    if abs(a - b) >= tol:
        raise AssertionError(f"{label}: expected {b}, got {a}")
    return True


def test_round_trip(label, created, expected_type, checks):
    """Round-trip: create → ana_versor → assert."""
    analyzed = ana_versor(created)
    ok = isinstance(analyzed, expected_type)
    print(f"  [{('PASS' if ok else 'FAIL')}] {label} → {type(analyzed).__name__}")
    if not ok:
        print(
            f"        Expected {expected_type.__name__}, got {type(analyzed).__name__}"
        )
        return analyzed
    for name, value in checks(analyzed).items():
        print(f"        {name}: {value}")
    return analyzed


def test_application(label, orig_versor, analyzed_op, point):
    """Re-create from analyzed op → apply to point → compare with original."""
    recreated = geo.create(analyzed_op)
    point_mv = geo.create(point)

    y1 = orig_versor * point_mv * orig_versor.rev()
    y2 = recreated * point_mv * recreated.rev()
    p1 = geo.which_entity(y1)
    p2 = geo.which_entity(y2)

    dx = p1.x - p2.x
    dy = p1.y - p2.y
    dz = p1.z - p2.z
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    ok = dist < 1e-6
    print(f"  [{('PASS' if ok else 'FAIL')}] {label}: apply → {p2}")
    if not ok:
        print(f"        Expected {p1}, got {p2}  (dist={dist:.2e})")


# ═══════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════

print("=" * 60)
print("1. ROTOR round-trip")
print("=" * 60)
rotor_op = Rotor(math.pi / 2, Direction(0, 0, 1))
rotor_mv = geo.create(rotor_op)
rotor_ana = test_round_trip(
    "Rotor(90°, z)",
    rotor_mv,
    Rotor,
    lambda r: {"angle": f"{math.degrees(r.angle):.1f}°", "axis": r.axis},
)
if rotor_ana:
    test_application("rotor on (1,0,0)", rotor_mv, rotor_ana, Point(1, 0, 0))

print()
print("=" * 60)
print("2. TRANSLATOR round-trip")
print("=" * 60)
translator_op = Translator(Direction(1, 2, 3))
translator_mv = geo.create(translator_op)
translator_ana = test_round_trip(
    "Translator(1,2,3)",
    translator_mv,
    Translator,
    lambda t: {"vector": t.vector},
)
if translator_ana:
    test_application(
        "translator on (0,0,0)", translator_mv, translator_ana, Point(0, 0, 0)
    )

print()
print("=" * 60)
print("3. MOTOR round-trip")
print("=" * 60)
motor_op = Motor(
    rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
    translator=Translator(Direction(0, 0, 1)),
)
motor_mv = geo.create(motor_op)
motor_ana = test_round_trip(
    "Motor(R(90°,z), T(0,0,1))",
    motor_mv,
    Motor,
    lambda m: {
        "rotor.angle": f"{math.degrees(m.rotor.angle):.1f}°",
        "rotor.axis": m.rotor.axis,
        "translator": m.translator.vector,
    },
)
if motor_ana:
    test_application("motor on (0,0,0)", motor_mv, motor_ana, Point(0, 0, 0))

print()
print("=" * 60)
print("4. GENERAL ROTOR round-trip")
print("=" * 60)
genrotor_op = GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0))
genrotor_mv = geo.create(genrotor_op)
genrotor_ana = test_round_trip(
    "GenRotor(90°,z, at(1,0,0))",
    genrotor_mv,
    GeneralRotor,
    lambda g: {
        "angle": f"{math.degrees(g.angle):.1f}°",
        "axis": g.axis,
        "origin": g.origin,
    },
)
if genrotor_ana:
    test_application("genrotor on (2,0,0)", genrotor_mv, genrotor_ana, Point(2, 0, 0))

print()
print("=" * 60)
print("5. ROUND-TRIP: Rotor angle = 0° (identity)")
print("=" * 60)
identity_mv = geo.create(Rotor(0.0, Direction(0, 0, 1)))
identity_ana = ana_versor(identity_mv)
print(f"  type={type(identity_ana).__name__}")
print(f"  result={identity_ana}")

print()
print("Done.")
