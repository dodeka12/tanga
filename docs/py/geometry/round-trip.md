# Round-Trip Examples

The analysis and creation pipelines are inverse operations:

```python
result = geo.analyze(geo.create(entity))
assert type(result) == type(entity)  # same type
```

Bind an algebra to a `Geometry` instance once, then use its methods
throughout:

```python
from pytanga.geometry import Geometry

geo = Geometry(algebra, opns=True)
```

## E3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Rotor, Direction, Space
import math

e3 = BasisE3()
geo = Geometry(e3)

# Point round-trip
p = Point(3, -1, 2)
mv = geo.create(p)
result = geo.analyze(mv)
print(result)  # Point(x=3.0, y=-1.0, z=2.0)
assert result == p

# Rotor round-trip
r = Rotor(angle=math.pi / 3, axis=Direction(1, 0, 0))
mv = geo.create(r)
result = geo.analyze(mv)
assert isinstance(result, Rotor)
print(f"Angle: {math.degrees(result.angle):.1f}°")

# Space
s = Space()
mv = geo.create(s)
result = geo.analyze(mv)
assert isinstance(result, Space)
```

## P3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Direction, Line

p3 = BasisP3()
geo = Geometry(p3)

# Point
p = Point(0, 5, 0)
result = geo.analyze(geo.create(p))
assert result == p

# Direction (ideal point)
d = Direction(1, 1, 1)
result = geo.analyze(geo.create(d))
assert isinstance(result, Direction)

# Line
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = geo.analyze(geo.create(line))
assert isinstance(result, Line)
```

## PGA3 Round-Trip (Gunn/Dorst plane‑based PGA)

PG3 uses the Gunn/Dorst model: Planes are grade‑1 vectors, Points are
grade‑3 trivectors, and Space is the 4D pseudoscalar ``I_4d``.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import (
    Geometry,
    Point, Direction, Line, Plane, Space,
    Rotor, Translator,
)
import math

pga = BasisPGA3()
geo = Geometry(pga)

# Plane (grade 1 in OPNS)
plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
result = geo.analyze(geo.create(plane))
assert isinstance(result, Plane)
print(f"Plane: {result}")

# Point (grade 3 trivector in OPNS)
p = Point(2, -1, 5)
result = geo.analyze(geo.create(p))
assert isinstance(result, Point) and abs(result.x - 2) < 0.01
print(f"Point: {result}")

# Direction (ideal point, OPNS grade 3)
d = Direction(1, 0, 0)
result = geo.analyze(geo.create(d))
assert isinstance(result, Direction)
print(f"Direction: {result}")

# Line (grade 2, intersection of two planes)
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = geo.analyze(geo.create(line))
assert isinstance(result, Line)
print(f"Line: {result}")

# Space (grade 4 pseudoscalar I_4d)
result = geo.analyze(geo.create(Space()))
assert isinstance(result, Space)
print(f"Space: {result}")

# Operators unchanged
rot = Rotor(angle=math.pi / 4, axis=Direction(0, 0, 1))
result = geo.analyze(geo.create(rot))
assert isinstance(result, Rotor)
print(f"Rotor: {result}")

t = Translator(vector=Direction(1, 2, 0))
result = geo.analyze(geo.create(t))
assert isinstance(result, Translator)
print(f"Translator: {result}")
```

## N3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Sphere, PointPair

n3 = BasisN3()
geo = Geometry(n3)

# Sphere
s = Sphere(center=Point(1, 0, 0), radius=3.0)
mv = geo.create(s)
result = geo.analyze(mv)
print(isinstance(result, Sphere))  # True
print(f"Radius: {result.radius:.1f}")  # ~3.0

# Point pair
pp = PointPair(point_a=Point(0, 0, 0), point_b=Point(2, 0, 0))
mv = geo.create(pp)
result = geo.analyze(mv)
print(isinstance(result, PointPair))  # True
```

## E2 Round‑Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Direction, Rotor, Space
import math

e2 = BasisE2()
geo = Geometry(e2)

# Direction (E2 has no points)
d = Direction(3, 4, 0)
mv = geo.create(d)
result = geo.analyze(mv)
assert isinstance(result, Direction)
print(f"Direction: {result}")

# Rotor (the only rotation plane is e12)
r = Rotor(angle=math.pi / 4, axis=Direction(0, 0, 1))
mv = geo.create(r)
result = geo.analyze(mv)
assert isinstance(result, Rotor)
print(f"Angle: {math.degrees(result.angle):.1f}°")

# Space
s = Space()
mv = geo.create(s)
result = geo.analyze(mv)
assert isinstance(result, Space)
```

## P2 Round‑Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Direction, Line

p2 = BasisP2()
geo = Geometry(p2)

# Point
p = Point(2, 5, 0)
result = geo.analyze(geo.create(p))
assert isinstance(result, Point)

# Direction (ideal point)
d = Direction(1, 1, 0)
result = geo.analyze(geo.create(d))
assert isinstance(result, Direction)

# Line
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = geo.analyze(geo.create(line))
assert isinstance(result, Line)
```

## N2 Round‑Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Sphere, Line, Rotor, Translator
import math

n2 = BasisN2()
geo = Geometry(n2)

# Point
p = Point(1, 2, 0)
result = geo.analyze(geo.create(p))
assert isinstance(result, Point)

# Sphere → Circle in 2D (conformal sphere with z=0 is a circle)
s = Sphere(center=Point(1, 0, 0), radius=3.0)
result = geo.analyze(geo.create(s))
# In N2, spheres analyze as Circle
from pytanga.geometry import Circle
print(isinstance(result, Circle))

# Rotor
r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
result = geo.analyze(geo.create(r))
assert isinstance(result, Rotor)

# Translator (N2 support)
t = Translator(vector=Direction(1, 2, 0))
result = geo.analyze(geo.create(t))
assert isinstance(result, Translator)
```

## PGA2 Round‑Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Geometry, Point, Direction, Line, Rotor, Space
import math

pga2 = BasisPGA2()
geo = Geometry(pga2)

# Point (OPNS grade‑2 bivector in PGA2)
p = Point(2, -1, 0)
result = geo.analyze(geo.create(p))
assert isinstance(result, Point)
print(f"Point: {result}")

# Line (grade‑1 vector in OPNS)
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = geo.analyze(geo.create(line))
assert isinstance(result, Line)

# Rotor
r = Rotor(angle=math.pi / 4, axis=Direction(0, 0, 1))
result = geo.analyze(geo.create(r))
assert isinstance(result, Rotor)

# Space
result = geo.analyze(geo.create(Space()))
assert isinstance(result, Space)
```

## Plain Functions

The same round‑trips can be written with the plain functions — pass the
algebra and OPNS flag explicitly on each call:

```python
from pytanga.geometry import analyze, create

result = analyze(create(e3, Point(3, -1, 2)))
assert isinstance(result, Point)
```

The `Geometry` class is a convenience wrapper that stores the algebra and
default OPNS flag so you don't need to repeat them.

## Entity Coverage by Algebra

| Entity | E3 | P3 | PGA3 | N3 | E2 | P2 | PGA2 | N2 |
|--------|:--:|:--:|:----:|:--:|:--:|:--:|:----:|:--:|
| Point | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Direction | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PointPair | — | — | — | ✓ | — | — | — | ✓ |
| Line | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Circle | — | — | — | ✓ | — | — | — | ✓ |
| Plane | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | — |
| Sphere | — | — | — | ✓ | — | — | — | ✓ |
| Space | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Operator Coverage by Algebra

| Operator | E3 | P3 | PGA3 | N3 | E2 | P2 | PGA2 | N2 |
|----------|:--:|:--:|:----:|:--:|:--:|:--:|:----:|:--:|
| Reflection | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Inversion | — | — | — | ✓ | — | — | — | ✓ |
| Rotor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Translator | — | — | ✓ | ✓ | — | — | — | ✓ |
| Dilator | — | — | — | ✓ | — | — | — | ✓ |
| Motor | — | — | ✓ | ✓ | — | — | — | ✓ |
| GeneralRotor | — | — | ✓ | ✓ | — | — | — | ✓ |