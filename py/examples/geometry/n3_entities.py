# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""n3_entities.py — Full conformal (N3) entities: Spheres, Circles, Point Pairs.

Showcases all entity types in the conformal geometric algebra (N3/CGA):
  - All 9 entity types: Point, Direction, HPoint, PointPair,
    Line, Circle, Plane, Sphere, Space
  - Grade-based entity distinction (Line/Circle, Plane/Sphere)
  - IPNS as the natural representation (grade-1 spheres, grade-4 points)

Operators are covered separately in n3_operators.py.

Prerequisite: base_n3_demo.py, pga3_entities.py
Run with:  uv run python py/examples/geometry/n3_entities.py
"""

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Circle,
    Direction,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
    analyze,
    analyze_entity,
    create,
    create_entity,
)

n3 = Algebra.from_name("N3")


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Conformal Point ─────────────────────────────────────
hr("1. Conformal Point — second-order embedding")

p = Point(2, 0, 0)
mv = create_entity(n3, p)
mv.show("Point(2,0,0) — conformal embedding")
result = analyze_entity(mv)
print(f"  analyze → {result}")

# ── 2. Direction (ideal point) ─────────────────────────────
hr("2. Direction — ideal point at infinity")

d = Direction(0, 1, 0)
mv_d = create_entity(n3, d)
mv_d.show("Direction(0,1,0) — SP with einf = 0")
result = analyze_entity(mv_d)
print(f"  analyze → {result}")

# ── 3. PointPair ───────────────────────────────────────────
hr("3. PointPair — two-point entity (grade-2 blade)")

pp = PointPair(point_a=Point(-2, 0, 0), point_b=Point(2, 0, 0))
mv_pp = create(n3, pp)
print(f"  create → grade-{max(mv_pp.grades)} blade")
result = analyze(mv_pp)
print(f"  analyze → {result}")

# ── 4. HPoint (flat point) ───────────────────────
hr("4. HPoint — weighted point (A ∧ einf)")

hp = HPoint(point=Point(1, 2, 3), weight=1.5)
mv_hp = create(n3, hp)
result = analyze(mv_hp)
print(f"  create+analyze → {result}")
print(
    f"    position: ({result.point.x:.1f}, "
    f"{result.point.y:.1f}, "
    f"{result.point.z:.1f})"
)

# ── 5. Line vs Circle (grade-3 distinction) ────────────────
hr("5. Line vs Circle — grade-3 distinction")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
print(f"  Line:  {analyze(create(n3, line))}")

circle = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
try:
    result = analyze(create(n3, circle))
    print(f"  Circle: {result}")
except Exception:
    print("  Circle: (analysis not available for this blade)")
print("  (Circle has e123 component; Line does not)")

# ── 6. Plane vs Sphere (grade-4 distinction) ───────────────
hr("6. Plane vs Sphere — grade-4 distinction")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
print(f"  Plane:  {analyze(create(n3, plane))}")

sphere = Sphere(center=Point(1, 0, 0), radius=3.0)
result = analyze(create(n3, sphere))
print(
    f"  Sphere: center=({result.center.x:.1f}, "
    f"{result.center.y:.1f}, "
    f"{result.center.z:.1f}), "
    f"radius={result.radius:.1f}"
)
print("  (Sphere has e123o component; Plane does not)")

# ── 7. IPNS — the natural representation ───────────────────
hr("7. IPNS — spheres as grade-1, points as grade-4")

# A sphere in IPNS is a grade-1 vector (dual of grade-4 OPNS blade)
mv_sp_ipns = create(n3, sphere, opns=False)
print(f"  IPNS Sphere: grade-{max(mv_sp_ipns.grades)} blade")
result = analyze_entity(mv_sp_ipns, opns=False)
print(f"  analyze → {result}")

# A point in IPNS is a grade-4 blade (dual of grade-1 OPNS blade)
mv_pt_ipns = create(n3, Point(5, 0, 0), opns=False)
print(f"  IPNS Point: grade-{max(mv_pt_ipns.grades)} blade")
result = analyze_entity(mv_pt_ipns, opns=False)
print(f"  analyze → {result}")

# ── 8. Entity coverage summary ──────────────────────────────
hr("8. Entity coverage — all 9 N3 types")

entities = [
    Point(1, 2, 3),
    Direction(4, 0, 0),
    HPoint(Point(1, 0, 0)),
    PointPair(Point(-1, 0, 0), Point(1, 0, 0)),
    Line(Point(0, 0, 0), Direction(1, 0, 0)),
    Circle(Point(0, 0, 0), Direction(0, 0, 1), 2.0),
    Plane(Point(0, 0, 3), Direction(0, 0, 1)),
    Sphere(Point(1, 0, 0), 3.0),
    Space(),
]

for e in entities:
    mv = create(n3, e)
    result = analyze(mv)
    name = type(e).__name__
    ok = "✓" if type(result).__name__ == name else f"→ {type(result).__name__}"
    print(f"  {name} {ok}")

print("\nDone — N3 entities demo complete.")