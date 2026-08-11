# Entity Data Classes

Entity data classes are algebra-independent `@dataclass` types that represent
geometric primitives in Euclidean 2D and 3D space. They can be used as input to
[`Geometry.create()`](create.md) (or the plain [`create()`](create.md) function)
and as output from [`Geometry.which_entity()`](analysis.md) (or the plain
[`analyze_entity()`](analysis.md) function).

All classes are imported from `pytanga.geometry` (defined in `pytanga.geometry.entities`).

!!! tip "2D usage"
    When working with 2D algebras (E2, P2, N2, PGA2), all entities still use
    3D data fields. The `z` component is always 0. For example, `Point(3, 4, 0)`
    represents the point at (3, 4) in 2D space.

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
| PGA3 | IPNS: `x·e1 + y·e2 + z·e3 + e₀` (OPNS: grade‑3 trivector) |
| N3 | `x·e1 + y·e2 + z·e3 + 0.5(r²-1)·ep + 0.5(r²+1)·em` |

### Construction from a multivector

`Point` can be initialised from a :class:`~pytanga.algebra._mv.MV` (grade‑1 vector
in a BasisE3 algebra). Only the ``e1``, ``e2`` and ``e3`` components are used:

```python
from pytanga.basis import BasisE3

e3 = BasisE3()
mv = e3.vector(3, 4, 5)
p = Point(mv)   # Point(3.00, 4.00, 5.00)
```

### Vector arithmetic operators

For simple 3D calculations that do not require geometric algebra, `Point`
and `Direction` support component‑wise arithmetic operators:

| Expression | Result | Notes |
|---|---|---|
| `Point + Point` | `Point` | component‑wise addition |
| `Point - Point` | `Direction` | vector from right operand to left |
| `Point + Direction` | `Point` | translate point along direction |
| `Point - Direction` | `Point` | translate backwards |
| `scalar * Point` | `Point` | scale by scalar |
| `Point * scalar` | `Point` | scale by scalar |
| `Point / scalar` | `Point` | divide by scalar |
| `-Point` | `Point` | negation |

### Methods

| Method | Returns | Description |
|---|---|---|
| `dot(other)` | `float` | Euclidean dot product with another `Point` or `Direction` |
| `cross(other)` | `Direction` | vector cross product (always returns a `Direction`) |
| `mag()` | `float` | Euclidean magnitude √(x² + y² + z²) |
| `normalized()` | `Point` | normalised copy (same direction, magnitude 1) |

**Example:**

```python
from pytanga.geometry import Point, Direction

p1 = Point(3, 0, 0)
p2 = Point(1, 0, 0)
d = p1 - p2           # Direction(2.00, 0.00, 0.00)
d_norm = d.normalized()     # Direction(1.00, 0.00, 0.00)
mid = (p1 + p2) / 2   # Point(2.00, 0.00, 0.00)
dist = p1.dot(d_norm) # 3.0
```

## Direction

A direction vector in 3D space. In E3 a grade‑1 vector represents a line
through the origin; in P3/N3/PGA3 a direction represents an ideal point
at infinity.

`Direction` can be initialised from a :class:`~pytanga.algebra._mv.MV` (grade‑1
vector in a BasisE3 algebra). Only the ``e1``, ``e2`` and ``e3`` components are used.

```python
from pytanga.geometry import Direction

d = Direction(x=1.0, y=0.0, z=0.0)

# From an MV
from pytanga.basis import BasisE3
e3 = BasisE3()
mv = e3.vector(1, 2, 3)
d = Direction(mv)  # Dir(1.00, 2.00, 3.00)
```

| Algebra | Supported |
|---------|-----------|
| E3 | ✓ (grade‑1 vector) |
| P3 | ✓ (e4 coefficient = 0) |
| PGA3 | ✓ (IPNS grade 1, no e₀ component) |
| N3 | ✓ (SP(point, einf) = 0) |

### Conversion to MV

A `Point` or `Direction` can be passed directly to :meth:`BasisE3.vector`:

```python
e3.vector(Point(1, 2, 3))     # 1 e1 + 2 e2 + 3 e3
e3.vector(Direction(1, 0, 0)) # 1 e1
```

### Vector arithmetic operators

| Expression | Result | Notes |
|---|---|---|
| `Direction + Direction` | `Direction` | component‑wise addition |
| `Direction - Direction` | `Direction` | component‑wise subtraction |
| `Direction + Point` | `Point` | translate point along direction |
| `scalar * Direction` | `Direction` | scale by scalar |
| `Direction * scalar` | `Direction` | scale by scalar |
| `Direction / scalar` | `Direction` | divide by scalar |
| `-Direction` | `Direction` | negation |

### Methods

| Method | Returns | Description |
|---|---|---|
| `dot(other)` | `float` | Euclidean dot product with another `Point` or `Direction` |
| `cross(other)` | `Direction` | vector cross product |
| `mag()` | `float` | Euclidean magnitude √(x² + y² + z²) |
| `normalized()` | `Direction` | normalised copy (same direction, magnitude 1) |

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
| PGA3 | 2 | Intersection of 2 planes (grade‑2 bivector) |
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
| PGA3 | 1 | Vector ``n + d·e₀`` (grade‑1 plane vector) |
| N3 | 4 | 3 points + e∞ |

## Circle (N3 only)

```python
from pytanga.geometry import Circle, Point, Direction

circle = Circle(
    center=Point(0, 0, 0),
    normal=Direction(0, 0, 1),
    radius=2.0,
)
```

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 3 | IPNS: sphere ∩ plane |

## ImagCircle (N3 only)

An imaginary circle — the dual of a real point pair.  It has no real
Euclidean points on it and is visualized as a dotted wireframe by default
(fully transparent surface, wireframe-only).

```python
from pytanga.geometry import ImagCircle, Point, Direction

ic = ImagCircle(
    center=Point(0, 0, 0),
    normal=Direction(0, 0, 1),
    radius=2.0,
)
```

`ImagCircle` is a frozen subclass of `Circle` with `is_imaginary=True`.
It can be used as a class-based key in `viz.default_styles`.

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 3 | Dual of a grade-2 point pair (negative squared norm) |

## Sphere (N3 only)

```python
from pytanga.geometry import Sphere, Point

sphere = Sphere(
    center=Point(1, 2, 3),
    radius=5.0,
)
```

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 4 | IPNS: `c - 0.5·r²·einf` |

## ImagSphere (N3 only)

An imaginary sphere — the dual of a real sphere.  It has ``S² = −ρ²``
(negative squared norm — no real points) and is visualized as a dotted
wireframe by default.

```python
from pytanga.geometry import ImagSphere, Point

isp = ImagSphere(
    center=Point(0, 0, 0),
    radius=3.0,
)
```

`ImagSphere` is a frozen subclass of `Sphere` with `is_imaginary=True`.
It can be used as a class-based key in `viz.default_styles`.

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 4 | ``S = A + ½ρ² e∞`` (negative squared norm) |

## PointPair (N3 only)

A pair of points represented as a grade-2 conformal blade.

```python
from pytanga.geometry import PointPair, Point

pp = PointPair(
    point_a=Point(0, 0, 0),
    point_b=Point(1, 0, 0),
)
```

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 2 | `p1_c ∧ p2_c` (wedge of 2 conformal points) |

## ImagPointPair (N3 only)

An imaginary point pair — the dual of a real circle.  It has no real
Euclidean points on it and is visualized as a dotted wireframe by default.

```python
from pytanga.geometry import ImagPointPair, Point

ipp = ImagPointPair(
    point_a=Point(0, 0, 0),
    point_b=Point(1, 0, 0),
)
```

`ImagPointPair` is a frozen subclass of `PointPair` with `is_imaginary=True`.
It can be used as a class-based key in `viz.default_styles`.

| Algebra | Grade | Representation |
|---------|-------|----------------|
| N3 | 2 | `p1_c ∧ p2_c` (negative squared norm) |

## Space

The entire 3D volume (pseudoscalar). No parameters.

```python
from pytanga.geometry import Space

space = Space()
```

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## Entity Coverage Matrix

| Entity | E3 | P3 | PGA3 | N3 | E2 | P2 | PGA2 | N2 |
|--------|:--:|:--:|:----:|:--:|:--:|:--:|:----:|:--:|
| Point | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Direction | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PointPair | — | — | — | ✓ | — | — | — | ✓ |
| ImagPointPair | — | — | — | ✓ | — | — | — | ✓ |
| Line | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Circle | — | — | — | ✓ | — | — | — | ✓ |
| ImagCircle | — | — | — | ✓ | — | — | — | ✓ |
| Plane | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | — |
| Sphere | — | — | — | ✓ | — | — | — | ✓ |
| ImagSphere | — | — | — | ✓ | — | — | — | ✓ |
| Space | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
