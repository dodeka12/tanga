# Phase 11: Example Scripts for the Geometry Submodule

**Goal:** Create short, didactic example scripts under `py/examples/geometry/` that
introduce new users to the geometry submodule's features.  The scripts progress from
the simplest algebra (E3) through P3 and PGA3 to the richest (N3), each building on
concepts already introduced.

**Reference style:** existing example scripts in `py/examples/`, e.g.
`basis_usage.py`, `mv_demo.py`, `base_e3_demo.py`.

---

## 1. Relation to Existing Examples

Existing example scripts under `py/examples/` already cover:

| Script | Topic |
|--------|-------|
| `algebra_demo.py` | `Algebra` construction, signatures, dtypes |
| `mv_demo.py` | `MV` operators, coefficient access, utility methods |
| `basis_usage.py` | Three patterns for accessing named basis blades |
| `base_e3_demo.py` | `BasisE3` — Euclidean 3D |
| `base_p3_demo.py` | `BasisP3` — Projective 3D |
| `base_n3_demo.py` | `BasisN3` — Null / conformal 3D |
| `base_pga3_demo.py` | `BasisPGA3` — PGA 3D |

The new geometry scripts focus **exclusively** on the `pytanga.geometry` submodule
(entity/operator data classes, analysis, creation, OPNS/IPNS).

**Each script assumes the user has already read the corresponding `base_*.py`**
for that algebra and knows how to create basis instances and basic MVs.

---

## 2. Scripts to Create

| # | File | Algebra | Concepts |
|---|------|---------|----------|
| 1 | `py/examples/geometry/e3_entities.py` | E3 | Point, Plane, Space, Reflection, Rotor — create → analyze round-trip, IPNS duality |
| 2 | `py/examples/geometry/p3_entities.py` | P3 | Point, Direction, Line, Plane, Space, Reflection, Rotor — homogeneous weight, OPNS/IPNS |
| 3 | `py/examples/geometry/pga3_entities.py` | PGA3 | Entities + Translator, Motor — versor creation and analysis |
| 4 | `py/examples/geometry/n3_entities.py` | N3 | Full CGA entities: Point, Direction, PointPair, HPoint, Line, Circle, Plane, Sphere, Space — IPNS focus, grade-based distinction |
| 5 | `py/examples/geometry/n3_operators.py` | N3 | Full CGA operators: Reflection, Inversion, Rotor, Translator, Dilator, Motor, GeneralRotor, GeneralDilator — versor analysis, entity/operator duality (Sphere vs Inversion) |

Each script is designed to be **self-contained enough to read alone** but
cross-references the previous scripts where helpful.

---

## 3. Script 1: `e3_entities.py` — Euclidean 3D Entities & Operators

**File:** `py/examples/geometry/e3_entities.py`

**Goal:** Introduce the most basic geometry submodule concepts: entities, operators,
create, analyze, and round-trip, using the simplest algebra E3.

### Topics covered

| Section | Concept | API used |
|---------|---------|----------|
| 1 | Point creation and analysis | `Point(x,y,z)`, `create_entity()`, `analyze_entity()` |
| 2 | Plane creation and analysis | `Plane`, bivector representation |
| 3 | Space (pseudoscalar) | `Space()` |
| 4 | Reflection operator | `Reflection(normal)`, `analyze_operator()` |
| 5 | Rotor operator | `Rotor(angle, axis)`, round-trip |
| 6 | IPNS interpretation | `analyze_entity(mv, opns=False)` — vector → Plane, bivector → Point |
| 7 | Generic `analyze()` / `create()` | Dispatcher with entity/operator fallback |

### Example code structure

```python
# py/examples/geometry/e3_entities.py

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
    Point, Direction, Plane, Space,
    Reflection, Rotor,
    analyze_entity, analyze_operator,
    create_entity, create_operator,
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

from pytanga.geometry import analyze, create

mv_pt = create(e3, Point(-1, 2, 5))
result = analyze(mv_pt)
print(f"  create + analyze Point → {result}")

print("\nDone — E3 geometry demo complete.")
```

### Verification

- [ ] Runs without errors with `uv run python py/examples/geometry/e3_entities.py`
- [ ] Each `analyze()` / `create()` round-trip returns the correct entity type
- [ ] IPNS section demonstrates Point ↔ Plane duality in E3

---

## 4. Script 2: `p3_entities.py` — Projective 3D Entities & Operators

**File:** `py/examples/geometry/p3_entities.py`

**Goal:** Introduce homogeneous coordinates, Direction (ideal point), Line, and
extend operator analysis to P3.

### Topics covered

| Section | Concept | API used |
|---------|---------|----------|
| 1 | Point vs Direction | `Direction(x,y,z)`, homogeneous weight |
| 2 | Line creation | `Line(origin, direction)`, grade-2 blade |
| 3 | Plane with offset | `Plane` in P3, trivector |
| 4 | Round-trip: Point, Direction, Line, Plane | `create_entity()` → `analyze_entity()` |
| 5 | IPNS in P3 | `opns=False`, dualization |
| 6 | Operators: Reflection, Rotor | Same as E3, P3-specific embedding |

### Example outline

```python
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

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Point, Direction, Line, Plane, Space,
    Reflection, Rotor,
    analyze_entity, analyze_operator,
    create_entity, create_operator, create, analyze,
)

p3 = Algebra.from_name("P3")

def hr(title): ...

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
    ("Line", Line(Point(0,0,0), Direction(1,1,0))),
    ("Plane", Plane(Point(1,0,0), Direction(0,1,0))),
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
```

### Verification

- [ ] Runs without errors
- [ ] Point vs Direction correctly distinguished by e4 weight
- [ ] Line and Plane round-trips preserve origin, direction, normal
- [ ] IPNS section shows entity type change via dualization

---

## 5. Script 3: `pga3_entities.py` — PGA3 Entities & Operators

**File:** `py/examples/geometry/pga3_entities.py`

**Goal:** Introduce PGA3-specific features: single null vector (einf), extended
operator set (Translator, Motor).

### Topics covered

| Section | Concept | API used |
|---------|---------|----------|
| 1 | PGA3 Point embedding | `Point` with einf null vector |
| 2 | Line and Plane in IPNS | `Line`, `Plane` as multi-point ∧ einf blades |
| 3 | Translator | `Translator(vector)`, versor analysis |
| 4 | Motor (rotation + translation) | `Motor(rotor, translator)`, 4-factor decomposition |
| 5 | Operator round-trips | Reflection, Rotor, Translator, Motor |
| 6 | IPNS dualization | `opns=False` for entities in PGA3 |

### Example outline

```python
"""pga3_entities.py — PGA3 geometry: Translators, Motors, single null vector.

Extends to Projective Geometric Algebra (PGA3) which uses a single null
vector einf to represent projective geometry.  Introduces:
  - Translator and Motor operators
  - IPNS entity representation (points·einf)
  - how PGA3 differs from full N3 (no eo-dependent entities)

Prerequisite: base_pga3_demo.py, p3_entities.py
Run with:  uv run python py/examples/geometry/pga3_entities.py
"""

from pytanga.algebra import Algebra
from pytanga.geometry import (
    Point, Direction, Line, Plane, Space,
    Reflection, Rotor, Translator, Motor,
    analyze, analyze_entity, analyze_operator,
    create, create_entity, create_operator,
)
import math

pga = Algebra.from_name("PGA3")

def hr(title): ...

# ── 1. Point in PGA3 ────────────────────────────────────────
hr("1. PGA3 Point — embedded with einf null vector")
p = Point(5, 0, 0)
mv = create(pga, p)
mv.show("Point(5,0,0) in PGA3")
result = analyze(mv)
print(f"  analyze → {result}")

# ── 2. Line and Plane ──────────────────────────────────────
hr("2. Line and Plane in PGA3 (IPNS)")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
mv_l = create(pga, line)
mv_l.show("Line along x-axis", label="")
print(f"  analyze → {analyze(mv_l)}")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
mv_p = create(pga, plane)
print(f"  Plane at z=3 → {analyze(mv_p)}")

# ── 3. Translator ───────────────────────────────────────────
hr("3. Translator — new operator type")

t = Translator(vector=Direction(1, 2, 0))
mv_t = create_operator(pga, t)
mv_t.show("Translator by (1, 2, 0)")
result = analyze_operator(mv_t)
print(f"  analyze → {result}")
print(f"  vector = ({result.vector.x:.1f}, {result.vector.y:.1f}, {result.vector.z:.1f})")

# ── 4. Motor (rotation + translation) ───────────────────────
hr("4. Motor — rigid body motion")

m = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = create_operator(pga, m)
mv_m.show("Motor: 90° around z + shift along x", label="")
result = analyze_operator(mv_m)
print(f"  analyze → {result}")

# ── 5. Operator round-trips ─────────────────────────────────
hr("5. Operator round-trips")

ops = [
    ("Reflection", Reflection(normal=Direction(0, 0, 1))),
    ("Rotor", Rotor(angle=0.5, axis=Direction(0, 1, 0))),
    ("Translator", Translator(vector=Direction(2, 0, 0))),
]

for name, op in ops:
    result = analyze_operator(create_operator(pga, op))
    print(f"  {name}: {type(result).__name__} ✓")

# The motor round-trip may not perfectly reconstruct parameters
# (factorization is non-unique), but the type is correct:
result = analyze_operator(create_operator(pga, m))
print(f"  Motor: {type(result).__name__} ✓")
if isinstance(result, Motor):
    print(f"    rotor angle={result.rotor.angle:.3f} rad")

# ── 6. IPNS in PGA3 ─────────────────────────────────────────
hr("6. IPNS interpretation in PGA3")

mv_pt = create(pga, Point(3, 0, 0), opns=False)
result = analyze_entity(mv_pt, opns=False)
print(f"  IPNS create + analyze of Point(3,0,0) → {result}")

print("\nDone — PGA3 geometry demo complete.")
```

### Verification

- [ ] Runs without errors
- [ ] Translator round-trip returns correct vector
- [ ] Motor created and analyzed (type check passes)
- [ ] IPNS round-trip preserves entity type

---

## 6. Script 4: `n3_entities.py` — Full Conformal (N3) Entities

**File:** `py/examples/geometry/n3_entities.py`

**Goal:** Showcase all 9 entity types available in the full conformal model (N3/CGA),
with a focus on grade-based entity distinction (Line vs Circle, Plane vs Sphere)
and IPNS as the natural representation.

### Topics covered

| Section | Concept | API used |
|---------|---------|----------|
| 1 | Conformal Point | `Point` with second-order embedding, ``create_entity``, ``analyze_entity`` |
| 2 | Direction (ideal point) | `Direction`, SP with einf = 0 |
| 3 | PointPair | Two-point entity, grade-2 blade, ``create``, ``analyze`` |
| 4 | HPoint (flat point) | ``HPoint(point, weight)``, ``A ∧ einf`` |
| 5 | Line vs Circle | Grade-3 distinction: Circle has ``e123`` component |
| 6 | Plane vs Sphere | Grade-4 distinction: Sphere has ``e123o`` component |
| 7 | IPNS — the natural representation | Sphere as grade-1 IPNS, Point as grade-4 IPNS via ``opns=False`` |
| 8 | Entity coverage summary | All 9 entity types in a single round-trip loop |

### Example outline

```python
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
    Point, Direction, HPoint, PointPair,
    Line, Circle, Plane, Sphere, Space,
    analyze, analyze_entity,
    create, create_entity,
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
print(f"    position: ({result.point.x:.1f}, {result.point.y:.1f}, {result.point.z:.1f})")

# ── 5. Line vs Circle (grade-3 distinction) ────────────────
hr("5. Line vs Circle — grade-3 distinction")

line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
print(f"  Line:  {analyze(create(n3, line))}")

circle = Circle(center=Point(0, 0, 0), normal=Direction(0, 0, 1), radius=2.0)
result = analyze(create(n3, circle))
print(f"  Circle: center=({result.center.x:.1f}, {result.center.y:.1f}, {result.center.z:.1f}), radius={result.radius:.1f}")
print("  (Circle has e123 component; Line does not)")

# ── 6. Plane vs Sphere (grade-4 distinction) ───────────────
hr("6. Plane vs Sphere — grade-4 distinction")

plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
print(f"  Plane:  {analyze(create(n3, plane))}")

sphere = Sphere(center=Point(1, 0, 0), radius=3.0)
result = analyze(create(n3, sphere))
print(f"  Sphere: center=({result.center.x:.1f}, {result.center.y:.1f}, {result.center.z:.1f}), radius={result.radius:.1f}")
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
```

### Verification

- [ ] Runs without errors
- [ ] All 9 entity types create and analyze correctly
- [ ] Line vs Circle distinguished (Circle has e123)
- [ ] Plane vs Sphere distinguished (Sphere has e123o)
- [ ] IPNS section shows grade flip (sphere → grade-1, point → grade-4)

---

## 7. Script 5: `n3_operators.py` — Full Conformal (N3) Operators

**File:** `py/examples/geometry/n3_operators.py`

**Goal:** Showcase all 8 operator types in N3/CGA, the entity/operator duality
(Sphere vs Inversion), and how versor analysis classifies operators by factor count
and null-vector composition.

### Topics covered

| Section | Concept | API used |
|---------|---------|----------|
| 1 | Reflection | `Reflection(normal)`, single factor, no null |
| 2 | Inversion | `Inversion(origin)`, single factor with eo |
| 3 | Rotor | `Rotor(angle, axis)`, two Euclidean factors |
| 4 | Translator | `Translator(vector)`, two einf factors, direct coefficient extraction |
| 5 | Dilator | `Dilator(factor)`, two eo factors |
| 6 | Motor | `Motor(rotor, translator)`, four factors (2 Euclidean + 2 null) |
| 7 | GeneralRotor / GeneralDilator | Higher-level versor types |
| 8 | Entity/Operator distinction | Same blade → `Sphere` via ``analyze_entity``, ``Inversion`` via ``analyze_operator`` |

### Example outline

```python
"""n3_operators.py — Full conformal (N3) operators: Rotors, Motors, Inversions.

Showcases all operator (versor) types in the conformal geometric algebra:
  - 8 operator types: Reflection, Inversion, Rotor, Translator, Dilator,
    Motor, GeneralRotor, GeneralDilator
  - Versor decomposition via blade_factorize_versor()
  - Entity/Operator distinction: sphere analyzed as Sphere vs Inversion
  - Factor-count-based classification

Entities are covered separately in n3_entities.py.

Prerequisite: n3_entities.py
Run with:  uv run python py/examples/geometry/n3_operators.py
"""

import math
from pytanga.algebra import Algebra
from pytanga.geometry import (
    Point, Direction,
    Reflection, Inversion, Rotor, Translator, Dilator, Motor,
    Sphere,
    analyze, analyze_entity, analyze_operator,
    create, create_entity, create_operator,
)

n3 = Algebra.from_name("N3")


def hr(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("=" * 60)


# ── 1. Reflection ──────────────────────────────────────────
hr("1. Reflection — grade-1 versor, no null components")

refl = Reflection(normal=Direction(0, 0, 1))
mv_ref = create_operator(n3, refl)
mv_ref.show("Reflection in plane with normal (0,0,1)")
result = analyze_operator(mv_ref)
print(f"  analyze → {result}")

# ── 2. Inversion ───────────────────────────────────────────
hr("2. Inversion — grade-1 versor with eo component")

inv = Inversion(origin=Point(2, 0, 0))
mv_inv = create_operator(n3, inv)
mv_inv.show("Inversion at origin (2,0,0)")
result = analyze_operator(mv_inv)
print(f"  analyze → {result}")
print(f"  origin: ({result.origin.x:.1f}, {result.origin.y:.1f}, {result.origin.z:.1f})")

# ── 3. Rotor ───────────────────────────────────────────────
hr("3. Rotor — two Euclidean reflectors")

rot = Rotor(angle=math.pi / 3, axis=Direction(0, 0, 1))
mv_rot = create_operator(n3, rot)
mv_rot.show("Rotor: 60° about z-axis")
result = analyze_operator(mv_rot)
print(f"  analyze → {result}")

# ── 4. Translator ──────────────────────────────────────────
hr("4. Translator — two einf reflectors, direct coefficient extraction")

t = Translator(vector=Direction(3, 1, 0))
mv_t = create_operator(n3, t)
mv_t.show("Translator by (3, 1, 0)")
result = analyze_operator(mv_t)
print(f"  analyze → {result}")
print(f"  vector = ({result.vector.x:.3f}, {result.vector.y:.3f}, {result.vector.z:.3f})")

# ── 5. Dilator ─────────────────────────────────────────────
hr("5. Dilator — two eo reflectors, uniform scaling")

d = Dilator(factor=2.0)
mv_d = create_operator(n3, d)
mv_d.show("Dilator: factor = 2.0")
result = analyze_operator(mv_d)
print(f"  analyze → {result}")
if isinstance(result, Dilator):
    print(f"  factor = {result.factor:.3f}")

# ── 6. Motor — combined rotation + translation ─────────────
hr("6. Motor — rigid body motion (4 factors)")

motor = Motor(
    rotor=Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
mv_m = create_operator(n3, motor)
mv_m.show("Motor: 90° around z + shift along x", label="")
result = analyze_operator(mv_m)
print(f"  analyze → {result}")
if isinstance(result, Motor):
    print(f"    rotor angle = {result.rotor.angle:.3f} rad")
    print(f"    translator  = ({result.translator.vector.x:.1f}, "
          f"{result.translator.vector.y:.1f}, {result.translator.vector.z:.1f})")

# ── 7. Operator coverage summary ───────────────────────────
hr("7. Operator coverage — all N3 operator types")

ops = [
    ("Reflection", Reflection(Direction(0, 0, 1))),
    ("Inversion",  Inversion(Point(1, 0, 0))),
    ("Rotor",      Rotor(angle=0.5, axis=Direction(0, 0, 1))),
    ("Translator", Translator(vector=Direction(3, 0, 0))),
    ("Dilator",    Dilator(factor=2.0)),
]

for name, op in ops:
    mv_op = create_operator(n3, op)
    result = analyze_operator(mv_op)
    print(f"  {name}: {type(result).__name__} ✓")

# Motor via generic dispatcher
result = analyze(create(n3, motor))
print(f"  Motor (via analyze): {type(result).__name__} ✓")

# ── 8. Entity/Operator distinction ─────────────────────────
hr("8. Entity vs Operator — same blade, different interpretation")

sphere = Sphere(center=Point(0, 0, 0), radius=2.0)
mv_sph = create(n3, sphere)

# analyze_entity sees the geometric entity
entity_result = analyze_entity(mv_sph)
print(f"  analyze_entity → {entity_result}")
print("    (sphere is a geometric entity)")

# analyze_operator sees the same blade as an Inversion
op_result = analyze_operator(mv_sph)
print(f"  analyze_operator → {op_result}")
print("    (the same blade is also an inversion operator)")

print("\nDone — N3 operators demo complete.")
```

### Verification

- [ ] Runs without errors
- [ ] All 5 main operator types (Reflection, Inversion, Rotor, Translator, Dilator) round-trip correctly
- [ ] Motor is decomposed correctly (type check passes)
- [ ] Sphere analyzed as `Sphere` via `analyze_entity`, as `Inversion` via `analyze_operator`
- [ ] Entity/Operator distinction section explains the concept clearly

---

## 8. Documentation Update

After the scripts are created, update `docs/py/index.md` to add links to the new
example scripts in the "Example Scripts" table:

```markdown
| [`geometry/e3_entities.py`](../../py/examples/geometry/e3_entities.py) | E3 Point, Plane, Reflection, Rotor — create, analyze, IPNS |
| [`geometry/p3_entities.py`](../../py/examples/geometry/p3_entities.py) | P3 Point, Direction, Line, Plane — homogeneous, IPNS |
| [`geometry/pga3_entities.py`](../../py/examples/geometry/pga3_entities.py) | PGA3 Translator, Motor — single null vector |
| [`geometry/n3_entities.py`](../../py/examples/geometry/n3_entities.py) | N3 entities: Point, Circle, Sphere, Plane — IPNS, grade distinction |
| [`geometry/n3_operators.py`](../../py/examples/geometry/n3_operators.py) | N3 operators: Rotor, Motor, Inversion, Dilator — entity/operator duality |
```

---

## 9. Implementation Plan

| Step | Action |
|------|--------|
| 1 | Create `py/examples/geometry/` directory |
| 2 | Create `py/examples/geometry/e3_entities.py` |
| 3 | Create `py/examples/geometry/p3_entities.py` |
| 4 | Create `py/examples/geometry/pga3_entities.py` |
| 5 | Create `py/examples/geometry/n3_entities.py` |
| 6 | Create `py/examples/geometry/n3_operators.py` |
| 7 | Run all 5 scripts with `uv run python py/examples/geometry/<script>.py` and verify output |
| 8 | Update `docs/py/index.md` — add geometry example links |
| 9 | Commit all files |

## 10. Verification Checklist

- [ ] All 5 scripts run without errors
- [ ] Each script demonstrates at least 6 distinct concepts
- [ ] OPNS (default) and IPNS (`opns=False`) both shown
- [ ] N3 entities script covers all 9 entity types with grade-based distinction
- [ ] N3 operators script covers entity/operator distinction (Sphere vs Inversion)
- [ ] PGA3 script highlights what is NOT available (no Sphere/Circle/PointPair)
- [ ] `docs/py/index.md` links to all 5 new scripts
- [ ] Commit history is clean (one commit for all 5 scripts + docs update)
