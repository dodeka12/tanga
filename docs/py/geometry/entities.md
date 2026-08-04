# Entity Data Classes

Entity data classes are algebra-independent `@dataclass` types that represent
geometric primitives in Euclidean 2D and 3D space. They can be used as input to
[`create()`](create.md) and as output from [`analyze_entity()`](analysis.md).

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
| PGA3 | ✓ (IPNS grade 1, no e₀ component) |
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
