# Analysis Pipeline — MV → Geometry

The analysis pipeline extracts geometric meaning from multivectors.

```python
from pytanga.geometry import analyze, analyze_entity, analyze_operator
```

## `analyze(mv) → Entity | Operator`

Tries entity analysis first, then operator analysis. Returns the first
successful match.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import analyze, Point

e3 = Algebra.from_name('E3')
point_mv = e3.vector(1, 2, 3)
result = analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)
```

## `analyze_entity(mv) → Entity`

Determines which geometric entity a multivector represents.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import analyze_entity, Plane

e3 = Algebra.from_name('E3')
# A grade-2 bivector in E3 = a plane
plane_mv = e3.e12  # bivector e1∧e2
result = analyze_entity(plane_mv)
print(result)  # Plane(point=Point(0,0,0), normal=Direction(0,0,1))
```

## `analyze_operator(mv) → Operator`

Determines which versor/operator a multivector represents.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import analyze_operator, Rotor

e3 = Algebra.from_name('E3')
rotor_mv = e3.rotor(1.57, e3.e3)
result = analyze_operator(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))
```

## How It Works

1. **Algebra detection** — determines whether the MV belongs to E3, P3, PGA3, or N3.
   PGA3 and N3 share the same C++ basis but are distinguished via `isinstance()`.

2. **Entity decomposition** — uses [`blade_factorize()`](https://tanga.readthedocs.io)
   (backed by C++ `FactorizeBlade()`) to factor a blade into grade-1 factor vectors,
   which directly correspond to geometric primitives.

3. **Operator decomposition** — uses `blade_factorize_versor()` (backed by
   C++ `FactorizeVersor()`) to factor a versor into reflector factors,
   classified by count and blade composition.

## Entity Type Distinction (N3)

In N3, some grades contain multiple entity types:

| Grade | Entities | Distinction method |
|-------|----------|--------------------|
| 1 | Point vs Direction | `SP(point, einf)` ≠ 0 for finite points |
| 3 | Line vs Circle | `e123` blade component present → Circle |
| 4 | Plane vs Sphere | `e123o` blade component present → Sphere |

## Operator Type Distinction (N3)

| Factors | Operators | Distinction method |
|---------|-----------|--------------------|
| 1 | Reflection vs Inversion | eo component present → Inversion |
| 2 | Rotor vs Translator vs Dilator | Null-vector content of factors |
| 4 | Motor vs GeneralRotor | 2+2 vs 2+1 factor composition |

## Algebra Coverage

| Algebra | Entities Detected | Operators Detected |
|---------|-------------------|-------------------|
| E3 | Point, Plane, Space | Reflection, Rotor |
| P3 | Point, Direction, Line, Plane, Space | Reflection, Rotor |
| PGA3 | Point, Direction, Line, Plane, Space (Gunn/Dorst grade mapping: Plane = 1, Line = 2, Point = 3) | Reflection, ReflectionLine, ReflectionOrigin, Rotor, Translator, Motor, GeneralRotor |
| N3 | Point, Direction, PointPair, Line, Circle, Plane, Sphere, Space | Reflection, Inversion, Rotor, Translator, Dilator, GeneralDilator, Motor, GeneralRotor |