# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""p3_entities.py — Projective 3D geometry: Points, Directions, Lines, Planes.

Extends the E3 geometry concepts to the homogeneous projective model (P3).
Covers:
  - Finite Points vs ideal Directions (e4 weight)
  - Lines as outer product of point and direction
  - Planes with offset via trivector dualization
  - OPNS/IPNS duality in P3

Prerequisite: base_p3_demo.py, e3_entities.py
Run with:  uv run python py/examples/geometry/p3_entities.py
"""

import math

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Direction,
    Line,
    Plane,
    Point,
    Reflection,
    Rotor,
    Space,
    analyze,
    analyze_entity,
    analyze_operator,
    create,
    create_entity,
    create_operator,
)

p3 = Algebra.from_name("P3")


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Point vs Direction ──────────────────────────────────
hr("1. Point (finite) vs Direction (ideal)")

p = Point(1, 2, 3)
mv_p = create(p3, p)
mv_p.show("Point(1,2,3) in P3")
print(f"  analyze → {analyze(mv_p)}")

d = Direction(4, 0, 0)
mv_d = create(p3, d)
mv_d.show("Direction(4,0,0) — ideal point")
print(f"  analyze → {analyze(mv_d)}")

# ── 2. Line ─────────────────────────────────────────────────
hr("2. Line — outer product of point and direction")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
mv_line = create(p3, line)
mv_line.show("Line through origin along x-axis")
result = analyze(mv_line)
print(f"  analyze → {result}")

# ── 3. Plane with offset ────────────────────────────────────
hr("3. Plane — offset from origin")

plane = Plane(point=Point(0, 0, 5), normal=Direction(0, 0, 1))
mv_pl = create(p3, plane)
mv_pl.show("Plane at z=5 with normal (0,0,1)")
result = analyze(mv_pl)
print(f"  analyze → {result}")

# ── 4. Round-trip all entities ──────────────────────────────
hr("4. Round-trip Point → create → analyze")

for name, e in [
    ("Point", Point(3, -1, 2)),
    ("Direction", Direction(0, 1, 0)),
    ("Line", Line(Point(0, 0, 0), Direction(1, 1, 0))),
    ("Plane", Plane(Point(1, 0, 0), Direction(0, 1, 0))),
]:
    result = analyze(create(p3, e))
    print(f"  {name}: {type(result).__name__} ✓")

# ── 5. IPNS in P3 ───────────────────────────────────────────
hr("5. IPNS interpretation in P3")

# In IPNS, a point becomes a plane, etc.
mv_p = create(p3, Point(1, 0, 0))
result = analyze_entity(mv_p, opns=False)
print(f"  IPNS of Point(1,0,0) → {type(result).__name__}")

# ── 6. Operators ────────────────────────────────────────────
hr("6. Operators: Reflection and Rotor")

refl = Reflection(normal=Direction(0, 1, 0))
result = analyze(create_operator(p3, refl))
print(f"  Reflection → {result}")

rot = Rotor(angle=math.pi / 4, axis=Direction(1, 0, 0))
result = analyze(create_operator(p3, rot))
print(f"  Rotor → {result}")

print("\nDone — P3 geometry demo complete.")