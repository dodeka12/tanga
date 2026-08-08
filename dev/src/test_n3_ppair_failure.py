#!/usr/bin/env python3
"""Demonstrate N3 PointPair analysis.

The analysis returns the same points and correct separation for a pair
of points. Previously there was a bug where separation returned 5.0
instead of sqrt(5) ≈ 2.236 — this was fixed by the direction
normalization and other changes.

Run: uv run python dev/src/test_n3_ppair_failure.py
"""

from __future__ import annotations

import math

from pytanga.basis import BasisN3
from pytanga.geometry import Point
from pytanga.geometry.analysis import analyze_entity
from pytanga.geometry.create import create_entity
from pytanga.geometry.entities import PointPair

b = BasisN3()

a = Point(1, 0, 1)
b_p = Point(3, 0, 2)
expected_sep = math.sqrt((b_p.x - a.x) ** 2 + (b_p.y - a.y) ** 2 + (b_p.z - a.z) ** 2)
expected_mid = Point((a.x + b_p.x) / 2, (a.y + b_p.y) / 2, (a.z + b_p.z) / 2)

mv = create_entity(b, PointPair(a, b_p))
r = analyze_entity(mv, opns=True)

print("Created: PointPair(Point(1,0,1), Point(3,0,2))")
print(f"Expected midpoint: {expected_mid}")
print(f"Expected separation: {expected_sep:.4f}")
print()
print(f"Analyzed: {r}")
print(f"  r.point_a = {r.point_a}")
print(f"  r.point_b = {r.point_b}")
print()
r_sep = math.sqrt(
    (r.point_b.x - r.point_a.x) ** 2
    + (r.point_b.y - r.point_a.y) ** 2
    + (r.point_b.z - r.point_a.z) ** 2
)
print(f"Analyzed separation: {r_sep:.4f}")
print()
if abs(r_sep - expected_sep) < 1e-6:
    print("OK: Separation matches expected value.")
else:
    print(f"FAIL: Expected separation {expected_sep:.4f}, got {r_sep:.4f}")
