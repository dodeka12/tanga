# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""e3_entities.py — Euclidean 3D geometry: Points, Planes, Reflections, Rotors.

Introduces the geometry submodule on the simplest algebra (E3).  Covers:
  - Entity creation and analysis (Point, Plane, Space)
  - Operator creation and analysis (Reflection, Rotor)
  - Round-trip: analyze(create(...)) returns the same entity/operator
  - IPNS interpretation via the ``opns=False`` flag

Prerequisite: base_e3_demo.py
Run with:  uv run python py/examples/geometry/e3_entities.py
"""

import math

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Direction,
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


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


e3 = Algebra.from_name("E3")

# ── 1. Point ────────────────────────────────────────────────
hr("1. Point — create, inspect, analyze")

p = Point(3, 4, 0)
mv = create_entity(e3, p)
mv.show("Point(3, 4, 0) as MV")
result = analyze_entity(mv)
print(f"  analyze → {result}")

# ── 2. Plane (through origin) ───────────────────────────────
hr("2. Plane — bivector representation")

pl = Plane(point=Point(0, 0, 0), normal=Direction(0, 0, 1))
mv_plane = create_entity(e3, pl)
mv_plane.show("Plane with normal (0,0,1)")
result = analyze_entity(mv_plane)
print(f"  analyze → {result}")

# ── 3. Space ─────────────────────────────────────────────────
hr("3. Space — pseudoscalar")

sp = Space()
mv_sp = create_entity(e3, sp)
mv_sp.show("Pseudoscalar I")
result = analyze_entity(mv_sp)
print(f"  analyze → {result}")

# ── 4. Reflection ────────────────────────────────────────────
hr("4. Reflection — grade-1 versor")

refl = Reflection(normal=Direction(1, 0, 0))
mv_ref = create_operator(e3, refl)
mv_ref.show("Reflection in plane with normal (1,0,0)")
result = analyze_operator(mv_ref)
print(f"  analyze → {result}")

# ── 5. Rotor ────────────────────────────────────────────────
hr("5. Rotor — rotation about an axis")

r = Rotor(angle=math.pi / 3, axis=Direction(0, 0, 1))
mv_rot = create_operator(e3, r)
mv_rot.show("Rotor: 60° about z-axis")
result = analyze_operator(mv_rot)
print(f"  analyze → {result}")

# ── 6. IPNS (Inner Product Null Space) ───────────────────────
hr("6. IPNS interpretation (opns=False)")

vec = e3.e1
result = analyze_entity(vec, opns=False)
print(f"  IPNS of e1  → {result}")

biv = e3.e12
result = analyze_entity(biv, opns=False)
print(f"  IPNS of e12 → {result}")

# ── 7. Convenience dispatcher ────────────────────────────────
hr("7. Convenience dispatchers: analyze() and create()")

mv_pt = create(e3, Point(-1, 2, 5))
result = analyze(mv_pt)
print(f"  create + analyze Point → {result}")

print("\nDone — E3 geometry demo complete.")