# Round-Trip Examples

The analysis and creation pipelines are inverse operations:

```python
result = analyze(create(basis, entity))
assert type(result) == type(entity)  # same type
```

## E3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Point, Rotor, Direction, Space, analyze, create
import math

e3 = Algebra.from_name('E3')

# Point round-trip
p = Point(3, -1, 2)
mv = create(e3, p)
result = analyze(mv)
print(result)  # Point(x=3.0, y=-1.0, z=2.0)
assert result == p

# Rotor round-trip
r = Rotor(angle=math.pi / 3, axis=Direction(1, 0, 0))
mv = create(e3, r)
result = analyze(mv)
assert isinstance(result, Rotor)
print(f"Angle: {math.degrees(result.angle):.1f}°")

# Space
s = Space()
mv = create(e3, s)
result = analyze(mv)
assert isinstance(result, Space)
```

## P3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Point, Direction, Line, analyze, create

p3 = Algebra.from_name('P3')

# Point
p = Point(0, 5, 0)
result = analyze(create(p3, p))
assert result == p

# Direction (ideal point)
d = Direction(1, 1, 1)
result = analyze(create(p3, d))
assert isinstance(result, Direction)

# Line
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = analyze(create(p3, line))
assert isinstance(result, Line)
```

## PGA3 Round-Trip (Gunn/Dorst plane‑based PGA)

PG3 uses the Gunn/Dorst model: Planes are grade‑1 vectors, Points are
grade‑3 trivectors, and Space is the 4D pseudoscalar ``I_4d``.

```python
from pytanga.algebra import Algebra
from pytanga.geometry import (
    Point, Direction, Line, Plane, Space,
    Rotor, Translator,
    analyze, create,
)
import math

pga = Algebra.from_name('PGA3')

# Plane (grade 1 in OPNS)
plane = Plane(point=Point(0, 0, 3), normal=Direction(0, 0, 1))
result = analyze(create(pga, plane))
assert isinstance(result, Plane)
print(f"Plane: {result}")

# Point (grade 3 trivector in OPNS)
p = Point(2, -1, 5)
result = analyze(create(pga, p))
assert isinstance(result, Point) and abs(result.x - 2) < 0.01
print(f"Point: {result}")

# Direction (ideal point, OPNS grade 3)
d = Direction(1, 0, 0)
result = analyze(create(pga, d))
assert isinstance(result, Direction)
print(f"Direction: {result}")

# Line (grade 2, intersection of two planes)
line = Line(origin=Point(0, 0, 0), direction=Direction(1, 0, 0))
result = analyze(create(pga, line))
assert isinstance(result, Line)
print(f"Line: {result}")

# Space (grade 4 pseudoscalar I_4d)
result = analyze(create(pga, Space()))
assert isinstance(result, Space)
print(f"Space: {result}")

# Operators unchanged
rot = Rotor(angle=math.pi / 4, axis=Direction(0, 0, 1))
result = analyze(create(pga, rot))
assert isinstance(result, Rotor)
print(f"Rotor: {result}")

t = Translator(vector=Direction(1, 2, 0))
result = analyze(create(pga, t))
assert isinstance(result, Translator)
print(f"Translator: {result}")
```

## N3 Round-Trip

```python
from pytanga.algebra import Algebra
from pytanga.geometry import Point, Sphere, PointPair, analyze, create

n3 = Algebra.from_name('N3')

# Sphere
s = Sphere(center=Point(1, 0, 0), radius=3.0)
mv = create(n3, s)
result = analyze(mv)
print(isinstance(result, Sphere))  # True
print(f"Radius: {result.radius:.1f}")  # ~3.0

# Point pair
pp = PointPair(point_a=Point(0, 0, 0), point_b=Point(2, 0, 0))
mv = create(n3, pp)
result = analyze(mv)
print(isinstance(result, PointPair))  # True
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
| GeneralRotor | — | — | ✓ | ✓ |
