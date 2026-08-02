# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""pga3_entities.py — Gunn/Dorst PGA 3D geometry with plane‑based representation.

This script demonstrates the Gunn/Dorst projective geometric algebra (PGA)
in 3D, where:

  - Planes  = grade‑1 vectors   ``n + d·einf``
  - Lines   = grade‑2 bivectors (intersection of two planes)
  - Points  = grade‑3 trivectors (intersection of three planes)

Points can also be represented in IPNS (dual) form as
``x·e1 + y·e2 + z·e3 + einf`` (grade 1).  The default ``opns=True`` mode
uses the plane‑based representation.

Prerequisite: base_pga3_demo.py, p3_entities.py
Run with:  uv run python py/examples/geometry/pga3_entities.py
"""

import math

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Direction,
    Line,
    Motor,
    Plane,
    Point,
    Reflection,
    Rotor,
    Space,
    Translator,
    analyze,
    analyze_entity,
    analyze_operator,
    create,
    create_entity,
    create_operator,
)

pga = Algebra.from_name("PGA3")


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Plane ──────────────────────────────────────────────
hr("1. Plane — grade‑1 vector (Gunn/Dorst OPNS)")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
mv = create(pga, plane)
mv.show("Plane at z=3, normal (0,0,1)")
result = analyze(mv)
print(f"  analyze → {result}")
print("  (OPNS grade 1 = plane)")

# ── 2. Line ───────────────────────────────────────────────
hr("2. Line — grade‑2 bivector (intersection of two planes)")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
mv_l = create(pga, line)
mv_l.show("Line through origin along x‑axis")
print(f"  analyze → {analyze(mv_l)}")
print("  (OPNS grade 2 = line)")

# ── 3. Point ──────────────────────────────────────────────
hr("3. Point — grade‑3 trivector in OPNS")

p = Point(5, 0, 0)
mv = create(pga, p)
print(f"  OPNS point grade: {max(mv.grades)}  (expected 3)")
result = analyze(mv)
print(f"  analyze → {result}")

# IPNS form (dual, grade 1)
mv2 = create(pga, p, opns=False)
print(f"  IPNS point grade: {max(mv2.grades)}  (expected 1)")
result2 = analyze(mv2)
print(f"  analyze (IPNS) → {result2}")

# ── 4. Direction ──────────────────────────────────────────
hr("4. Direction — ideal point at infinity")

d = Direction(1, 0, 0)
mv_d = create(pga, d, opns=False)
print(f"  IPNS Direction: {analyze_entity(mv_d, opns=False)}")
print("  (ideal point: no einf component in the grade‑1 dual)")

# ── 5. Space ──────────────────────────────────────────────
hr("5. Space — 4D pseudoscalar I_4d = e1∧e2∧e3∧einf")

sp = Space()
mv_sp = create(pga, sp)
print(f"  Space OPNS grade: {max(mv_sp.grades)}  (expected 4)")
result = analyze(mv_sp)
print(f"  analyze → {result}")

# ── 6. Operators ──────────────────────────────────────────
hr("6. Operators (unchanged from N3 embedding)")

ops = [
    ("Reflection", Reflection(normal=Direction(0, 0, 1))),
    ("Rotor", Rotor(angle=0.5, axis=Direction(0, 1, 0))),
    ("Translator", Translator(vector=Direction(2, 0, 0))),
]

for name, op in ops:
    result_op = analyze_operator(create_operator(pga, op))
    print(f"  {name}: {type(result_op).__name__} ✓")

# Motor
m = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = create_operator(pga, m)
print(f"  Motor created: grade‑{max(mv_m.grades)} versor ✓")

# ── 7. IPNS interpretation ────────────────────────────────
hr("7. IPNS interpretation (opns=False)")

mv_pt = create(pga, Point(3, 0, 0), opns=False)
result = analyze_entity(mv_pt, opns=False)
print(f"  IPNS create + analyze of Point(3,0,0) → {result}")

# ── 8. Entity coverage summary ────────────────────────────
hr("8. Entity coverage — all PGA3 types")

entities = [
    ("Plane", Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))),
    ("Line", Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))),
    ("Point", Point(2, -3, 1)),
    ("Direction", Direction(0, 1, 0)),
    ("Space", Space()),
]

for name, e in entities:
    mv = create(pga, e)
    result = analyze(mv)
    ok = "✓" if type(result).__name__ == name else f"→ {type(result).__name__}"
    print(f"  {name}: {ok}")

print("\nDone — PGA3 geometry demo complete.")