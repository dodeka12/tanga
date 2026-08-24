# Analysis Pipeline — MV → Geometry

The analysis pipeline extracts geometric meaning from multivectors.

The recommended API is a bound [`Geometry`](https://github.com/dodeka12/tanga/blob/main/py/pytanga/geometry/_geometry.py) instance:

```python
from pytanga.geometry import Geometry
```

## `geo.analyze(mv) → Entity | Operator`

Tries entity analysis first, then operator analysis. Returns the first
successful match.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point

e3 = BasisE3()
geo = Geometry(e3)

point_mv = e3("e1 + 2 e2 + 3 e3")
result = geo.analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)
```

## `geo.which_entity(mv) → Entity`

Determines which geometric entity a multivector represents.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Plane

e3 = BasisE3()
geo = Geometry(e3)

# A grade-2 bivector in E3 = a plane
plane_mv = e3.e12  # bivector e1∧e2
result = geo.which_entity(plane_mv)
print(result)  # Plane(point=Point(0,0,0), normal=Direction(0,0,1))
```

## `geo.which_operator(mv) → Operator`

Determines which versor/operator a multivector represents.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Rotor, Direction, create_operator

e3 = BasisE3()
geo = Geometry(e3)

rotor_mv = create_operator(e3, Rotor(angle=1.57, axis=Direction(0, 0, 1)))
result = geo.which_operator(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))
```

## Plain Functions

The underlying plain functions are also importable directly — they read the
OPNS/IPNS flag from the MV's algebra (`mv.algebra.opns`):

```python
from pytanga.geometry import analyze, analyze_entity, analyze_operator

result = analyze(point_mv)               # Entity or Operator
result = analyze_entity(mv)              # Entity only
result = analyze_operator(mv)            # Operator only
```

### Typed analyzers

Specific per-entity analyzers are public in every `analysis_*` module:
`analyze_point`, `analyze_direction`, `analyze_line`, `analyze_plane`,
`analyze_circle`, `analyze_sphere`, `analyze_point_pair`, `analyze_hpoint`,
`analyze_hdirection`, and `analyze_space` — all reading `mv.algebra.opns`.

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
| PGA3 | Point, Direction, Line, Plane, Space (Gunn/Dorst grade mapping: Plane = 1, Line = 2, Point = 3) | Reflection, ReflectionLine, ReflectionPoint, Rotor, Translator, Motor, GeneralRotor |
| N3 | Point, Direction, PointPair, Line, Circle, Plane, Sphere, Space | Reflection, Inversion, Rotor, Translator, Dilator, Motor, GeneralRotor |