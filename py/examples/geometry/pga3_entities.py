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

Uses the ``Geometry`` class to bind the PGA3 algebra and its default OPNS
flag.  Plain functions remain available as an alternative (see the last
section).

Prerequisite: base_pga3_demo.py, p3_entities.py
Run with:  uv run python py/examples/geometry/pga3_entities.py
"""

import math

from pytanga.basis import BasisPGA3
from pytanga.geometry import (
    Direction,
    Geometry,
    Line,
    Motor,
    Plane,
    Point,
    Rotor,
    Space,
    Translator,
)

pga = BasisPGA3()
geo = Geometry(pga)  # defaults to OPNS


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Plane ──────────────────────────────────────────────
hr("1. Plane — grade‑1 vector (Gunn/Dorst OPNS)")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
mv = geo.create(plane)
mv.show("Plane at z=3, normal (0,0,1)")
result = geo.analyze(mv)
print(f"  analyze → {result}")
print("  (OPNS grade 1 = plane)")

# ── 2. Line ───────────────────────────────────────────────
hr("2. Line — grade‑2 bivector (intersection of two planes)")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
mv_l = geo.create(line)
mv_l.show("Line through origin along x‑axis")
print(f"  analyze → {geo.analyze(mv_l)}")
print("  (OPNS grade 2 = line)")

# ── 3. Point ──────────────────────────────────────────────
hr("3. Point — grade‑3 trivector in OPNS")

p = Point(5, 0, 0)
mv = geo.create(p)
print(f"  OPNS point grade: {max(mv.grades)}  (expected 3)")
result = geo.analyze(mv)
print(f"  analyze → {result}")

# IPNS form (dual, grade 1)
mv2 = geo.create(p, opns=False)
print(f"  IPNS point grade: {max(mv2.grades)}  (expected 1)")
result2 = geo.analyze(mv2)
print(f"  analyze (IPNS) → {result2}")

# ── 4. Direction ──────────────────────────────────────────
hr("4. Direction — ideal point at infinity")

d = Direction(1, 0, 0)
mv_d = geo.create(d, opns=False)
print(f"  IPNS Direction: {geo.which_entity(mv_d, opns=False)}")
print("  (ideal point: no einf component in the grade‑1 dual)")

# ── 5. Space ──────────────────────────────────────────────
hr("5. Space — 4D pseudoscalar I_4d = e1∧e2∧e3∧einf")

sp = Space()
mv_sp = geo.create(sp)
print(f"  Space OPNS grade: {max(mv_sp.grades)}  (expected 4)")
result = geo.analyze(mv_sp)
print(f"  analyze → {result}")

# ── 6. Operators ──────────────────────────────────────────
hr("6. Operators (Rotor, Translator, Motor)")

# Rotor round-trip
r = Rotor(angle=0.5, axis=Direction(0, 1, 0))
result_op = geo.which_operator(geo.create(r))
print(f"  Rotor: {type(result_op).__name__} ✓")

# Translator round-trip
t = Translator(vector=Direction(2, 0, 0))
try:
    result_op = geo.which_operator(geo.create(t))
    print(f"  Translator: {type(result_op).__name__} ✓")
except (ValueError, NotImplementedError):
    print("  Translator: (analysis not yet available for this blade)")

# Motor (combined rotation + translation)
m = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = geo.create(m)
print(f"  Motor created: grade‑{max(mv_m.grades)} versor ✓")

# ── 7. IPNS interpretation ────────────────────────────────
hr("7. IPNS interpretation (opns=False)")

mv_pt = geo.create(Point(3, 0, 0), opns=False)
result = geo.which_entity(mv_pt, opns=False)
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
    mv = geo.create(e)
    result = geo.analyze(mv)
    ok = "✓" if type(result).__name__ == name else f"→ {type(result).__name__}"
    print(f"  {name}: {ok}")

# ── 9. Plain Functions (alternative) ──────────────────────
hr("9. Plain functions — no Geometry wrapper needed")

from pytanga.geometry import analyze, create  # noqa: E402

result = analyze(create(pga, Point(10, 0, 0)))
print(f"  plain create + analyze → {result}")

print("\nDone — PGA3 geometry demo complete.")
