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
from pytanga.algebra import Algebra
from pytanga.geometry import Point, Rotor, Direction, analyze, create
import math

# --- Analysis: MV → Entity/Operator ---
e3 = Algebra.from_name('E3')
point_mv = e3.vector(1, 2, 3)        # e1 + 2 e2 + 3 e3
result = analyze(point_mv)
print(result)  # Point(x=1.0, y=2.0, z=3.0)

rotor_mv = e3.rotor(1.57, e3.e3)    # 90° rotation about e3
result = analyze(rotor_mv)
print(result)  # Rotor(angle=1.57, axis=Direction(0,0,1))

# --- Creation: Entity/Operator → MV ---
pga = Algebra.from_name('PGA3')
p = Point(5, 0, 0)
mv = create(pga, p)                  # PGA3 point at (5,0,0)

r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
mv = create(pga, r)                  # PGA3 rotor

# --- Round-trip ---
result = analyze(create(e3, Point(1, 2, 3)))
print(result)  # Point(x=1.0, y=2.0, z=3.0)
```

## Topics

| Guide | What you will learn |
|-------|---------------------|
| [Entities](entities.md) | `Point`, `Direction`, `Line`, `Plane`, `Circle`, `Sphere`, `PointPair`, `Space` |
| [Operators](operators.md) | `ReflectionPlane`, `ReflectionLine`, `ReflectionOrigin`, `Inversion`, `Rotor`, `Translator`, `Dilator`, `Motor`, `GeneralRotor`, `GeneralDilator` |
| [Analysis Pipeline](analysis.md) | `analyze()`, `analyze_entity()`, `analyze_operator()` — MV → geometry |
| [Creation Pipeline](create.md) | `create()`, `create_entity()`, `create_operator()` — geometry → MV |
| [Round-Trip Examples](round-trip.md) | End-to-end examples and algebra coverage matrices |