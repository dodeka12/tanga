# Full conformal (N3) entities: Spheres, Circles, Point Pairs

**Keywords:** N3 · conformal · Sphere · Circle · Point Pair · IPNS

Showcases all entity types in the conformal geometric algebra (N3/CGA):
  - All 9 entity types: Point, Direction, HPoint, PointPair,
    Line, Circle, Plane, Sphere, Space
  - Grade-based entity distinction (Line/Circle, Plane/Sphere)
  - IPNS as the natural representation (grade-1 spheres, grade-4 points)

Uses the `Geometry` class to bind the N3 algebra and its default OPNS
flag.  The plain functions `analyze()`, `create()`, etc. remain
available as an alternative (see the last section).

Operators are covered separately in n3_operators.py.

Prerequisite: base_n3_demo.py, pga3_entities.py

## Run

```bash
uv run python py/examples/ga/geometry/n3_entities.py
```

## Source

[`ga/geometry/n3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/ga/geometry/n3_entities.py)

## Code

````python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""n3_entities.py — Full conformal (N3) entities: Spheres, Circles, Point Pairs.

Showcases all entity types in the conformal geometric algebra (N3/CGA):
  - All 9 entity types: Point, Direction, HPoint, PointPair,
    Line, Circle, Plane, Sphere, Space
  - Grade-based entity distinction (Line/Circle, Plane/Sphere)
  - IPNS as the natural representation (grade-1 spheres, grade-4 points)

Uses the ``Geometry`` class to bind the N3 algebra and its default OPNS
flag.  The plain functions ``analyze()``, ``create()``, etc. remain
available as an alternative (see the last section).

Operators are covered separately in n3_operators.py.

Prerequisite: base_n3_demo.py, pga3_entities.py
Run with:  uv run python py/examples/ga/geometry/n3_entities.py

Keywords: N3, conformal, Sphere, Circle, Point Pair, IPNS
"""

from pytanga.basis import BasisN3
from pytanga.geometry import (
    Circle,
    Direction,
    Geometry,
    HPoint,
    Line,
    Plane,
    Point,
    PointPair,
    Space,
    Sphere,
)

n3 = BasisN3()
geo = Geometry(n3)  # defaults to OPNS


def hr(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Conformal Point ─────────────────────────────────────
hr("1. Conformal Point — second-order embedding")

p = Point(2, 0, 0)
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv = geo.create(p)
mv.show("Point(2,0,0) — conformal embedding")
# geo(...) creates for Entity/Operator args; analyzes for MV args
result = geo.which_entity(mv)
print(f"  analyze → {result}")

# ── 2. Direction (ideal point) ─────────────────────────────
hr("2. Direction — ideal point at infinity")

d = Direction(0, 1, 0)
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv_d = geo.create(d)
mv_d.show("Direction(0,1,0) — SP with einf = 0")
# geo(...) creates for Entity/Operator args; analyzes for MV args
result = geo.which_entity(mv_d)
print(f"  analyze → {result}")

# ── 3. PointPair ───────────────────────────────────────────
hr("3. PointPair — two-point entity (grade-2 blade)")

pp = PointPair(point_a=Point(-2, 0, 0), point_b=Point(2, 0, 0))
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv_pp = geo.create(pp)
print(f"  create → grade-{max(mv_pp.grades)} blade")
result = geo.analyze(mv_pp)
print(f"  analyze → {result}")

# ── 4. HPoint (flat point) ───────────────────────
hr("4. HPoint — weighted point (A ∧ einf)")

hp = HPoint(point=Point(1, 2, 3), weight=1.5)
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv_hp = geo.create(hp)
result = geo.analyze(mv_hp)
print(f"  create+analyze → {result}")
print(
    f"    position: ({result.point.x:.1f}, {result.point.y:.1f}, {result.point.z:.1f})"
)

# ── 5. Line vs Circle (grade-3 distinction) ────────────────
hr("5. Line vs Circle — grade-3 distinction")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
# geo(...) creates for Entity/Operator args; analyzes for MV args
print(f"  Line:  {geo.analyze(geo.create(line))}")

circle = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
try:
    # geo(...) creates for Entity/Operator args; analyzes for MV args
    result = geo.analyze(geo.create(circle))
    print(f"  Circle: {result}")
except Exception:
    print("  Circle: (analysis not available for this blade)")
print("  (Circle has e123 component; Line does not)")

# ── 6. Plane vs Sphere (grade-4 distinction) ───────────────
hr("6. Plane vs Sphere — grade-4 distinction")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
# geo(...) creates for Entity/Operator args; analyzes for MV args
print(f"  Plane:  {geo.analyze(geo.create(plane))}")

sphere = Sphere(center=Point(1, 0, 0), radius=3.0)
# geo(...) creates for Entity/Operator args; analyzes for MV args
result = geo.analyze(geo.create(sphere))
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
n3.opns = False
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv_sp_ipns = geo.create(sphere)
print(f"  IPNS Sphere: grade-{max(mv_sp_ipns.grades)} blade")
# geo(...) creates for Entity/Operator args; analyzes for MV args
result = geo.which_entity(mv_sp_ipns)
print(f"  analyze → {result}")

# A point in IPNS is a grade-4 blade (dual of grade-1 OPNS blade)
# geo(...) creates for Entity/Operator args; analyzes for MV args
mv_pt_ipns = geo.create(Point(5, 0, 0))
print(f"  IPNS Point: grade-{max(mv_pt_ipns.grades)} blade")
# geo(...) creates for Entity/Operator args; analyzes for MV args
result = geo.which_entity(mv_pt_ipns)
print(f"  analyze → {result}")
n3.opns = True

# ── 8. Entity coverage summary ──────────────────────────────
hr("8. Entity coverage — all 9 N3 types")

entities = [
    Point(1, 2, 3),
    Direction(4, 0, 0),
    HPoint(Point(1, 0, 0)),
    PointPair(Point(-1, 0, 0), Point(1, 0, 0)),
    Line(Point(0, 0, 0), Direction(1, 0, 0)),
    Circle(Point(0, 0, 0), 2.0, Direction(0, 0, 1)),
    Plane(Point(0, 0, 3), Direction(0, 0, 1)),
    Sphere(Point(1, 0, 0), 3.0),
    Space(),
]

for e in entities:
    # geo(...) creates for Entity/Operator args; analyzes for MV args
    mv = geo.create(e)
    result = geo.analyze(mv)
    name = type(e).__name__
    ok = "✓" if type(result).__name__ == name else f"→ {type(result).__name__}"
    print(f"  {name} {ok}")

# ── 9. Plain Functions (alternative) ───────────────────────
hr("9. Plain functions — no Geometry wrapper needed")

from pytanga.geometry import analyze, create  # noqa: E402

mv_pt = create(n3, Point(7, 0, 0))
result = analyze(mv_pt)
print(f"  plain create + analyze → {result}")

print("\nDone — N3 entities demo complete.")
````
