# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Demonstrate the PGA3 test failures systematically.

Each demo shows the create → analyze round-trip (or application) and the
actual vs expected result.  Run with `uv run python dev/src/demo_pga3_failures.py`.
"""

from __future__ import annotations

import math

from pytanga.algebra._algebra import Algebra
from pytanga.geometry.analysis import analyze_entity, analyze_operator
from pytanga.geometry.create import create_entity, create_operator
from pytanga.geometry.entities import Direction, Line, Plane, Point
from pytanga.geometry.operators import (
    GeneralRotor,
    Motor,
    Rotor,
    Translator,
)

b = Algebra.from_name("PGA3")

print("=" * 60)
print("FAILURE 1: Direction sign flip")
print("=" * 60)
mv = create_entity(b, Direction(1, 2, 0))
r = analyze_entity(mv, opns=True)
print("  Created: Direction(1, 2, 0)")
print(f"  Analyzed: {r}")
print("  Expected: Direction(1.00, 2.00, 0.00)")
print()

print("=" * 60)
print("PLANE ROUND-TRIP (should pass — normal preserves sign)")
print("=" * 60)
normal = Direction(1, 3, 0)
unit = normal.norm()
pt = Point(3, -2, 1)
mv = create_entity(b, Plane(pt, normal))
r = analyze_entity(mv, opns=True)
print(f"  Created: Plane(point={pt}, normal={normal})")
print(f"  Analyzed: {r}")
print(f"  Expected normal: {unit}")
d = normal.x * pt.x + normal.y * pt.y
d_scaled = d / normal.mag()
d_analyzed = r.normal.x * r.point.x + r.normal.y * r.point.y + r.normal.z * r.point.z
print(f"  n·p (scaled): expected={d_scaled:.6f}, got={d_analyzed:.6f}")
print("  (analyzed point is the closest point to origin — NOT the construction point)")
print()

print("=" * 60)
print("LINE ROUND-TRIP (should pass — direction preserves sign)")
print("=" * 60)
direction = Direction(1, 2, 0)
unit = direction.norm()
pt = Point(1, 2, 3)
mv = create_entity(b, Line(pt, direction))
r = analyze_entity(mv, opns=True)
print(f"  Created: Line(org={pt}, dir={direction})")
print(f"  Analyzed: {r}")
print(f"  Expected direction: {unit}")
dx = r.origin.x - pt.x
dy = r.origin.y - pt.y
dz = r.origin.z - pt.z
cross_x = direction.y * dz - direction.z * dy
cross_y = direction.z * dx - direction.x * dz
cross_z = direction.x * dy - direction.y * dx
print(f"  (r.origin − pt) × direction = ({cross_x:.1e}, {cross_y:.1e}, {cross_z:.1e})")
print("  (analyzed origin is the closest point to origin — NOT the construction point)")
print()

print("=" * 60)
print("FAILURE 4: Rotor axis sign flip")
print("=" * 60)
mv = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
r = analyze_operator(mv)
print("  Created: Rotor(90.0° about Dir(0,0,1))")
print(f"  Analyzed: {r}")
print("  Expected: Rotor(90.0° about Dir(0.00,0.00,1.00))")
print()

print("=" * 60)
print("FAILURE 5: Motor analyzed as GeneralRotor")
print("=" * 60)
mv = create_operator(
    b,
    Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(1, 0, 0)),
    ),
)
r = analyze_operator(mv)
print("  Created: Motor(T(1,0,0), R(90°, z))")
print(f"  Analyzed: {r}  (type={type(r).__name__})")
print("  Expected: Motor type")
print()

print("=" * 60)
print("FAILURE 6: GeneralRotor axis sign flip")
print("=" * 60)
mv = create_operator(b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0)))
r = analyze_operator(mv)
print("  Created: GenRotor(90° about Dir(0,0,1) at Point(1,0,0))")
print(f"  Analyzed: {r}")
print("  Expected: GenRotor(90.0° about Dir(0.00,0.00,1.00) at Point(1.00,0.00,0.00))")
print()

print("=" * 60)
print("FAILURE 7: Rotor application — wrong rotation direction")
print("=" * 60)
p = create_entity(b, Point(1, 0, 0))
R = create_operator(b, Rotor(math.pi / 2, Direction(0, 0, 1)))
result = R.gp(p).gp(R.rev())
r = analyze_entity(result, opns=True)
print("  Apply: Rotor(90°, z) on Point(1,0,0)")
print(f"  Result: {r}")
print("  Expected: Point(0.00, 1.00, 0.00)  (CCW rotation by +90°)")
print("  (Looks like CW rotation, i.e. -90° about z)")
print()

print("=" * 60)
print("FAILURE 8: Motor application — translation only, no rotation")
print("=" * 60)
p = create_entity(b, Point(0, 0, 0))
M = create_operator(
    b,
    Motor(
        rotor=Rotor(math.pi / 2, Direction(0, 0, 1)),
        translator=Translator(Direction(1, 0, 0)),
    ),
)
result = M.gp(p).gp(M.rev())
r = analyze_entity(result, opns=True)
print("  Apply: Motor(T(1,0,0), R(90°, z)) on origin")
print(f"  Result: {r}")
print("  Expected: Point(0.00, 1.00, 0.00)  (translate→(1,0,0), rotate→(0,1,0))")
print("  (Got pure translation — rotation had no effect)")
print()

print("=" * 60)
print("FAILURE 9: GeneralRotor application — wrong rotation direction")
print("=" * 60)
p = create_entity(b, Point(2, 0, 0))
G = create_operator(b, GeneralRotor(math.pi / 2, Direction(0, 0, 1), Point(1, 0, 0)))
result = G.gp(p).gp(G.rev())
r = analyze_entity(result, opns=True)
print("  Apply: GenRotor(90°, z, at x=1) on Point(2,0,0)")
print(f"  Result: {r}")
print("  Expected: Point(1.00, 1.00, 0.00)")
print("  (Same CW vs CCW issue as failure 7)")
print()

print("=" * 60)
print("SUMMARY")
print("=" * 60)
print("  Failures fall into 4 root causes:")
print("  1. Direction sign: ideal point dual gives negated vector [failure 1]")
print("  2. Line origin not reconstructed correctly [failure 3]")
print("  3. Rotor sign: axis z→-z, rotation goes CW not CCW [failures 4,6,7,9]")
print("  4. Motor factorizes as 2 factors (GeneralRotor) not 4 (Motor) [failures 5,8]")
