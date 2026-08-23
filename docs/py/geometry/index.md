# Geometry Submodule

The `pytanga.geometry` submodule provides **algebra-independent** data classes
for geometric entities and operators, plus functions to extract geometric meaning
from multivectors and to construct multivectors from geometric descriptions.

The pipeline is **bidirectional**:

```
MV ──[analyze]──→ Entity/Operator    # extract geometric meaning
MV ←──[create]─── Entity/Operator    # construct MV from geometry
```

The recommended way to work with the geometry pipeline is via a
[`Geometry`](https://github.com/dodeka12/tanga/blob/main/py/pytanga/geometry/_geometry.py) instance, which binds an algebra.  The OPNS/IPNS
interpretation is read from the algebra's `opns` flag — so you don't need to
pass it on every call.

```python
from pytanga.geometry import Geometry
```

## Quick Start

```python
from pytanga.algebra import Algebra
from pytanga.geometry import (
    Direction,
    Geometry,
    Point,
    Rotor,
)
import math

# --- Bind an algebra ---
e3 = BasisE3()
geo = Geometry(e3)  # defaults to OPNS

# --- Analysis: MV → Entity/Operator ---
point_mv = e3("e1 + 2 e2 + 3 e3")      # e1 + 2 e2 + 3 e3
result = geo.analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)

from pytanga.geometry import create_operator
rotor_mv = create_operator(e3, Rotor(angle=1.57, axis=Direction(0, 0, 1)))
result = geo.analyze(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))

# --- Creation: Entity/Operator → MV ---
pga = BasisPGA3()
geom_pga = Geometry(pga)
p = Point(5, 0, 0)
mv = geom_pga.create(p)                 # PGA3 point at (5,0,0)

r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
mv = geom_pga.create(r)                 # PGA3 rotor

# --- Round-trip ---
result = geo.analyze(geo.create(Point(1, 2, 3)))
print(result)  # Point(x=1.0, y=2.0, z=3.0)
```

## Plain Functions

The plain functions `analyze()`, `analyze_entity()`, `analyze_operator()`,
`create()`, `create_entity()`, and `create_operator()` are also available
directly.  They read the OPNS/IPNS flag from the algebra (`algebra.opns`):

```python
from pytanga.geometry import analyze, create

result = analyze(point_mv)               # entity or operator
mv = create(e3, Point(1, 2, 3))          # MV from entity
```

The `Geometry` class methods simply delegate to these functions with the
stored algebra.

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Entities](entities.md) | `Point`, `Direction`, `Line`, `Plane`, `Circle`, `Sphere`, `PointPair`, `Space` |
| [MV-accepting constructors](mv-constructors.md) | Building entities from multivectors (`Point(mv)`, `Circle(mv)`, …) and factory auto-conversion (`Line.from_points`, `PointPath.add`) |
| [Operators](operators.md) | `ReflectionPlane`, `ReflectionLine`, `ReflectionPoint`, `Inversion`, `Rotor`, `Translator`, `Dilator`, `Motor`, `GeneralRotor` |
| [Analysis Pipeline](analysis.md) | `analyze()`, `analyze_entity()`, `analyze_operator()` — MV → geometry |
| [Creation Pipeline](create.md) | `create()`, `create_entity()`, `create_operator()` — geometry → MV |
| [Variables & Blade Masks](variables.md) | `mask_for()`, `create_var()`, `geo(name, type)` — geometry-derived `Variable` blade masks |
| [Random Generation](random.md) | Deterministic, seedable random points/directions (`RndPoint()`, `RndDirection()`, `Normal`/`Uniform`) |
| [Round-Trip Examples](round-trip.md) | End-to-end examples and algebra coverage matrices |
