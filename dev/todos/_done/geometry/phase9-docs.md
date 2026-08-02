# Phase 9: User Documentation

**Files:**
- `docs/py/geometry/index.md` — geometry submodule overview
- `docs/py/geometry/entities.md` — entity data classes reference
- `docs/py/geometry/operators.md` — operator data classes reference
- `docs/py/geometry/analysis.md` — analysis pipeline usage
- `docs/py/geometry/create.md` — creation pipeline usage
- `docs/py/geometry/round-trip.md` — round-trip examples and algebra coverage

**Goal:** Document the geometry submodule in a user-friendly way under
`docs/py/geometry/`, following the same structure as other `docs/py/` sub-folders
(e.g., `docs/py/solver/`, `docs/py/basis/`).

---

## 1. Documentation Structure

```
docs/py/geometry/
├── index.md          # Overview, quick start, topic index
├── entities.md       # Entity data classes reference
├── operators.md      # Operator data classes reference
├── analysis.md       # analyze_entity(), analyze_operator(), analyze()
├── create.md         # create_entity(), create_operator(), create()
└── round-trip.md     # End-to-end examples: create → analyze → round-trip
```

---

## 2. `docs/py/geometry/index.md`

Follow the pattern of `docs/py/solver/index.md`:

```markdown
# Geometry Submodule

The `pytanga.geometry` submodule provides **algebra-independent** data classes
for geometric entities and operators, plus functions to extract geometric meaning
from multivectors and to construct multivectors from geometric descriptions.

The pipeline is **bidirectional**:

```
MV ──[analyze]──→ Entity/Operator    # extract geometric meaning
MV ←──[create]─── Entity/Operator    # construct MV from geometry
```

## Quick Start

```python
from pytanga.basis import BasisE3, BasisPGA3
from pytanga.geometry import Point, Rotor, analyze, create

# --- Analysis: MV → Entity/Operator ---
e3 = BasisE3()
point_mv = e3.vector(1, 2, 3)        # e1 + 2 e2 + 3 e3
result = analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)

rotor_mv = e3.rotor(1.57, e3.e3)    # 90° rotation about e3
result = analyze(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))

# --- Creation: Entity/Operator → MV ---
pga = BasisPGA3()
p = Point(5, 0, 0)
mv = create(pga, p)                  # conformal point at (5,0,0)

r = Rotor(angle=1.57, axis=Direction(0, 0, 1))
mv = create(pga, r)                  # PGA3 rotor

# --- Round-trip ---
assert analyze(create(pga, p)) == p  # identity up to normalization
```

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Entities](entities.md) | `Point`, `Direction`, `Line`, `Plane`, `Circle`, `Sphere`, `PointPair`, `Space` |
| [Operators](operators.md) | `Reflection`, `Inversion`, `Rotor`, `Translator`, `Dilator`, `Motor`, `GeneralRotor`, `GeneralDilator` |
| [Analysis Pipeline](analysis.md) | `analyze()`, `analyze_entity()`, `analyze_operator()` — MV → geometry |
| [Creation Pipeline](create.md) | `create()`, `create_entity()`, `create_operator()` — geometry → MV |
| [Round-Trip Examples](round-trip.md) | End-to-end examples and algebra coverage matrices |
```

---

## 3. `docs/py/geometry/entities.md`

```markdown
# Entity Data Classes

Entity data classes are algebra-independent `@dataclass` types that represent
geometric primitives in Euclidean 3D space. They can be used as input to
[`create()`](create.md) and as output from [`analyze_entity()`](analysis.md).

All classes are defined in `pytanga.geometry.entities`.

## Point

```python
from pytanga.geometry import Point

p = Point(x=1.0, y=2.0, z=3.0)
print(p)  # Point(x=1.0, y=2.0, z=3.0)
```

| Algebra | MV representation |
|---------|-------------------|
| E3 | `x·e1 + y·e2 + z·e3` |
| P3 | `x·e1 + y·e2 + z·e3 + e4` |
| PGA3 | `x·e1 + y·e2 + z·e3 + einf` |
| N3 | `x·e1 + y·e2 + z·e3 + 0.5(r²-1)·ep + 0.5(r²+1)·em` |

## Direction

An ideal point at infinity (not available in E3).

```python
from pytanga.geometry import Direction

d = Direction(x=1.0, y=0.0, z=0.0)
```

| Algebra | Supported |
|---------|-----------|
| E3 | ✗ |
| P3 | ✓ (e4 coefficient = 0) |
| PGA3 | ✓ (no einf component) |
| N3 | ✓ (SP(point, einf) = 0) |

## Line

```python
from pytanga.geometry import Line, Point, Direction

line = Line(
    origin=Point(0, 0, 0),
    direction=Direction(1, 0, 0),
)
```

| Algebra | Grade | Representation |
|---------|-------|----------------|
| P3 | 2 | `origin ∧ direction` |
| PGA3 | 3 | 2 points + einf |
| N3 | 3 | 2 points + einf |

## Plane

```python
from pytanga.geometry import Plane, Point, Direction

plane = Plane(
    point=Point(0, 0, 0),
    normal=Direction(0, 0, 1),
)
```

| Algebra | Grade | Representation |
|---------|-------|----------------|
| E3 | 2 | Bivector `nx·e23 + ny·e31 + nz·e12` |
| P3 | 3 | 3 points on the plane |
| PGA3/N3 | 4 | 3 points + einf |

## Circle (N3 only)

```python
from pytanga.geometry import Circle, Point, Direction

circle = Circle(
    center=Point(0, 0, 0),
    normal=Direction(0, 0, 1),
    radius=2.0,
)
```

## Sphere (N3 only)

```python
from pytanga.geometry import Sphere, Point

sphere = Sphere(
    center=Point(1, 2, 3),
    radius=5.0,
)
```

## PointPair (N3 only)

A pair of points represented as a grade-2 conformal blade.

```python
from pytanga.geometry import PointPair, Point

pp = PointPair(
    point_a=Point(0, 0, 0),
    point_b=Point(1, 0, 0),
)
```

## Space

The entire 3D volume (pseudoscalar). No parameters.

```python
from pytanga.geometry import Space

space = Space()
```
```

---

## 4. `docs/py/geometry/operators.md`

```markdown
# Operator Data Classes

Operator data classes are algebra-independent `@dataclass` types that represent
versors (geometric transformations). They can be used as input to
[`create()`](create.md) and as output from [`analyze_operator()`](analysis.md).

All classes are defined in `pytanga.geometry.operators`.

## Reflection

```python
from pytanga.geometry import Reflection, Direction

refl = Reflection(normal=Direction(0, 0, 1))
```

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## Rotor

```python
from pytanga.geometry import Rotor, Direction
import math

r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
```

A 3D rotation by `angle` radians about `axis`. The MV representation is
`cos(θ/2) + sin(θ/2)·B` where B is the unit bivector.

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## Translator (PGA3, N3 only)

```python
from pytanga.geometry import Translator, Direction

t = Translator(vector=Direction(1, 2, 0))
```

## Motor (PGA3, N3 only)

A rigid body motion combining rotation and translation.

```python
from pytanga.geometry import Motor, Rotor, Translator

m = Motor(
    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
```

## N3-Only Operators

| Operator | Algebra | Description |
|----------|---------|-------------|
| `Inversion(origin)` | N3 | Inversion in a sphere centered at origin |
| `Dilator(factor)` | N3 | Uniform scaling about the origin |
| `GeneralDilator(factor, translator)` | N3 | Dilation with translation components |
| `GeneralRotor(rotor, translator)` | N3 | Rotor + ei-bivectors |

## Operator Coverage Matrix

| Operator | E3 | P3 | PGA3 | N3 |
|----------|:--:|:--:|:----:|:--:|
| Reflection | ✓ | ✓ | ✓ | ✓ |
| Inversion | — | — | — | ✓ |
| Rotor | ✓ | ✓ | ✓ | ✓ |
| Translator | — | — | ✓ | ✓ |
| Dilator | — | — | — | ✓ |
| General Dilator | — | — | — | ✓ |
| Motor | — | — | ✓ | ✓ |
| General Rotor | — | — | — | ✓ |
```

---

## 5. `docs/py/geometry/analysis.md`

```markdown
# Analysis Pipeline — MV → Geometry

The analysis pipeline extracts geometric meaning from multivectors.

```python
from pytanga.geometry import analyze, analyze_entity, analyze_operator
```

## `analyze(mv) → Entity | Operator`

Tries entity analysis first, then operator analysis. Returns the first
successful match.

```python
from pytanga.basis import BasisE3
from pytanga.geometry import analyze

e3 = BasisE3()
point_mv = e3.vector(1, 2, 3)
result = analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)
```

## `analyze_entity(mv) → Entity`

Determines which geometric entity a multivector represents.

```python
from pytanga.basis import BasisE3
from pytanga.geometry import analyze_entity

e3 = BasisE3()
# A grade-2 bivector in E3 = a plane
plane_mv = e3.e12  # bivector e1∧e2
result = analyze_entity(plane_mv)
print(result)  # Plane(point=..., normal=Direction(0,0,1))
```

## `analyze_operator(mv) → Operator`

Determines which versor/operator a multivector represents.

```python
from pytanga.basis import BasisE3
from pytanga.geometry import analyze_operator

e3 = BasisE3()
rotor_mv = e3.rotor(1.57, e3.e3)
result = analyze_operator(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))
```

## How It Works

1. **Algebra detection** — determines whether the MV belongs to E3, P3, PGA3, or N3.
   PGA3 and N3 share the same C++ basis but are distinguished via `isinstance()`.

2. **Entity decomposition** — uses `blade_factorize()` (backed by C++
   `FactorizeBlade()`) to factor a blade into grade-1 factor vectors,
   which directly correspond to geometric primitives.

3. **Operator decomposition** — uses `blade_factorize_versor()` (backed by
   C++ `FactorizeVersor()`) to factor a versor into reflector factors,
   classified by count and blade composition.

## Algebra-Specific Notes

| Algebra | Entities Detected | Operators Detected |
|---------|-------------------|-------------------|
| E3 | Point, Plane, Space | Reflection, Rotor |
| P3 | Point, Direction, Line, Plane, Space | Reflection, Rotor |
| PGA3 | Point, Direction, Line, Plane, Space | Reflection, Rotor, Translator, Motor |
| N3 | Point, Direction, PointPair, Line, Circle, Plane, Sphere, Space | Reflection, Inversion, Rotor, Translator, Dilator, GeneralDilator, Motor, GeneralRotor |
```

---

## 6. `docs/py/geometry/create.md`

```markdown
# Creation Pipeline — Geometry → MV

The creation pipeline constructs multivectors from geometric entity/operator
dataclasses. It is the inverse of the [analysis pipeline](analysis.md).

```python
from pytanga.geometry import create, create_entity, create_operator
```

## `create(basis, obj) → MV`

Convenience function that accepts either an Entity or Operator and
dispatches accordingly.

```python
from pytanga.basis import BasisE3, BasisPGA3
from pytanga.geometry import Point, Rotor, Direction, create
import math

e3 = BasisE3()
pga = BasisPGA3()

# Create a point in E3
mv = create(e3, Point(1, 2, 3))
print(mv)  # 1 e1 + 2 e2 + 3 e3

# Create a rotor in PGA3
r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
mv = create(pga, r)
```

## `create_entity(basis, entity) → MV`

Creates an MV from an Entity dataclass. The algebra determines the
representation:

```python
from pytanga.basis import BasisE3, BasisPGA3
from pytanga.geometry import Point, create_entity

e3 = BasisE3()
pga = BasisPGA3()

# Same point, different MVs in different algebras
mv_e3 = create_entity(e3, Point(1, 2, 3))
mv_pga = create_entity(pga, Point(1, 2, 3))
```

## `create_operator(basis, operator) → MV`

Creates an MV from an Operator dataclass:

```python
from pytanga.basis import BasisPGA3
from pytanga.geometry import Translator, Direction, create_operator

pga = BasisPGA3()
t = Translator(vector=Direction(1, 0, 0))
mv = create_operator(pga, t)
```

## Unsupported Entity/Operator Types

Calling `create()` with an entity/operator not supported in the detected
algebra raises `TypeError`:

- E3: `Circle`, `Sphere`, `PointPair`, `Translator`, `Motor`, `Dilator` → `TypeError`
- P3: `Circle`, `Sphere`, `PointPair`, `Translator`, `Motor` → `TypeError`
- PGA3: `PointPair`, `Circle`, `Sphere`, `Inversion`, `Dilator`, `GeneralDilator`, `GeneralRotor` → `TypeError`
```

---

## 7. `docs/py/geometry/round-trip.md`

```markdown
# Round-Trip Examples

The analysis and creation pipelines are inverse operations:

```python
assert analyze(create(basis, entity)) == entity  # up to normalization
```

## E3 Round-Trip

```python
from pytanga.basis import BasisE3
from pytanga.geometry import Point, Rotor, Direction, analyze, create
import math

e3 = BasisE3()

# Point round-trip
p = Point(3, -1, 2)
assert analyze(create(e3, p)) == p

# Rotor round-trip
r = Rotor(angle=math.pi / 3, axis=Direction(1, 0, 0))
result = analyze(create(e3, r))
assert isinstance(result, Rotor)
assert abs(result.angle - r.angle) < 1e-10
```

## P3 Round-Trip

```python
from pytanga.basis import BasisP3
from pytanga.geometry import Point, Direction, Line, analyze, create

p3 = BasisP3()

# Point
p = Point(0, 5, 0)
assert analyze(create(p3, p)) == p

# Direction (ideal point)
d = Direction(1, 1, 1)
assert analyze(create(p3, d)) == d

# Line
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = analyze(create(p3, line))
assert isinstance(result, Line)
```

## PGA3 Round-Trip

```python
from pytanga.basis import BasisPGA3
from pytanga.geometry import Point, Rotor, Translator, Motor, Direction, analyze, create
import math

pga = BasisPGA3()

# Motor (rotation + translation)
m = Motor(
    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(2, 0, 0)),
)
mv = create(pga, m)
result = analyze(mv)
assert isinstance(result, Motor)
```

## N3 Round-Trip

```python
from pytanga.basis import BasisN3
from pytanga.geometry import Point, Sphere, PointPair, analyze, create

n3 = BasisN3()

# Sphere
s = Sphere(center=Point(1, 0, 0), radius=3.0)
mv = create(n3, s)
result = analyze(mv)
assert isinstance(result, Sphere)

# Point pair
pp = PointPair(point_a=Point(0, 0, 0), point_b=Point(2, 0, 0))
mv = create(n3, pp)
result = analyze(mv)
assert isinstance(result, PointPair)
```

## Entity Coverage by Algebra

| Entity | E3 | P3 | PGA3 | N3 |
|--------|:--:|:--:|:----:|:--:|
| Point | ✓ | ✓ | ✓ | ✓ |
| Direction | — | ✓ | ✓ | ✓ |
| PointPair | — | — | — | ✓ |
| Line | — | ✓ | ✓ | ✓ |
| Circle | — | — | — | ✓ |
| Plane | ✓ | ✓ | ✓ | ✓ |
| Sphere | — | — | — | ✓ |
| Space | ✓ | ✓ | ✓ | ✓ |

## Operator Coverage by Algebra

| Operator | E3 | P3 | PGA3 | N3 |
|----------|:--:|:--:|:----:|:--:|
| Reflection | ✓ | ✓ | ✓ | ✓ |
| Inversion | — | — | — | ✓ |
| Rotor | ✓ | ✓ | ✓ | ✓ |
| Translator | — | — | ✓ | ✓ |
| Dilator | — | — | — | ✓ |
| GeneralDilator | — | — | — | ✓ |
| Motor | — | — | ✓ | ✓ |
| GeneralRotor | — | — | — | ✓ |
```

---

## 8. `docs/py/index.md` — Update

Add a row to the topics table linking to the new geometry docs:

```markdown
| [Geometry Submodule](geometry/index.md) | `Point`, `Line`, `Plane`, `Rotor`, `Motor` — algebra-independent entity/operator types, `analyze()` and `create()` pipelines |
```

And add an example script reference:

```markdown
| [`geometry_demo.py`](../../py/examples/geometry_demo.py) | `BasisE3`, `BasisPGA3` — entity analysis and creation round-trip |
```

---

## 9. Implementation Steps

1. Create `docs/py/geometry/` directory.
2. Create `docs/py/geometry/index.md` — overview and quick start.
3. Create `docs/py/geometry/entities.md` — entity reference with algebra coverage.
4. Create `docs/py/geometry/operators.md` — operator reference with coverage matrix.
5. Create `docs/py/geometry/analysis.md` — analysis pipeline usage.
6. Create `docs/py/geometry/create.md` — creation pipeline usage.
7. Create `docs/py/geometry/round-trip.md` — end-to-end examples.
8. Update `docs/py/index.md` — add link to geometry docs.

## 10. Verification Checklist

- [ ] All six documentation pages render correctly
- [ ] Quick start example runs without errors
- [ ] Entity and operator coverage matrices match the implementation
- [ ] Round-trip examples produce equivalent results
- [ ] `docs/py/index.md` links to the new submodule