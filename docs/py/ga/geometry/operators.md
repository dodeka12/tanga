# Operator Data Classes

Operator data classes are algebra-independent `@dataclass` types that represent
versors (geometric transformations). They can be used as input to
[`Geometry.create()`](create.md) (or the plain [`create()`](create.md) function)
and as output from [`Geometry.which_operator()`](analysis.md) (or the plain
[`analyze_operator()`](analysis.md) function).

All classes are imported from `pytanga.geometry` (defined in `pytanga.geometry.operators`).

!!! tip "2D usage"
    2D operators use the same classes as 3D. `Rotor(angle, Direction(0, 0, 1))`
    always rotates in the XY plane — the only rotation plane in 2D.
    For translations in 2D, use `Translator(vector=Direction(dx, dy, 0))`.

## Reflection (ReflectionPlane)

Reflection in a plane through the origin. ``Reflection`` is an alias for
``ReflectionPlane``.

```python
from pytanga.geometry import Reflection, Direction

refl = Reflection(normal=Direction(0, 0, 1))
```

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## ReflectionLine

Reflection about a line through the origin (grade‑2 bivector ``d∧e₀``).

```python
from pytanga.geometry import ReflectionLine, Direction

refl_line = ReflectionLine(direction=Direction(0, 0, 1))
```

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## ReflectionPoint

Reflection about the origin (trivector ``e₁∧e₂∧e₃``) — equivalent to
`ReflectionPoint(Point(0, 0, 0))`.

```python
from pytanga.geometry import ReflectionPoint, Point

refl_origin = ReflectionPoint(Point(0, 0, 0))
```

| Algebra | Supported |
|---------|-----------|
| P3, PGA3, N3 | ✓ |

!!! note
    ``ReflectionPoint`` is the general point-reflection operator — pass any
    ``Point`` to reflect about an arbitrary center.

## Inversion (N3 only)

Inversion in a sphere centered at ``center`` with radius ``radius``
(default ``1.0``).

```python
from pytanga.geometry import Inversion, Point

inv = Inversion(center=Point(0, 0, 0))                 # unit sphere (radius 1.0)
inv2 = Inversion(center=Point(1, 0, 0), radius=2.0)    # sphere of radius 2.0
```

| Algebra | Supported |
|---------|-----------|
| N3 | ✓ (requires eo null vector) |

## Rotor

A 3D rotation (even-grade versor: scalar + bivector).

```python
from pytanga.geometry import Rotor, Direction
import math

r = Rotor(angle=math.pi / 2, axis=Direction(0, 0, 1))
```

The MV representation is `cos(θ/2) + sin(θ/2)·B` where B is the unit bivector.

| Algebra | Supported |
|---------|-----------|
| E3, P3, PGA3, N3 | ✓ |

## Translator (PGA3, N3)

A translation in 3D space.

```python
from pytanga.geometry import Translator, Direction

t = Translator(vector=Direction(1, 2, 0))
```

| Algebra | Supported |
|---------|-----------|
| PGA3, N3 | ✓ |

## Dilator (N3 only)

A uniform dilation (scaling) about an origin point.

```python
from pytanga.geometry import Dilator, Point

d = Dilator(factor=2.0)  # scale about origin (0,0,0)
d2 = Dilator(factor=3.0, origin=Point(1, 0, 0))  # scale about point (1,0,0)
```

The MV representation is ``D = 1 + (1−d)/(1+d)·E`` where d is the dilation
factor and E = einf∧eo (Perwass formula). For non-origin dilators,
``D_t = T · D · T̃`` where T translates from global origin to the dilation
center.

| Algebra | Supported |
|---------|-----------|
| N3 | ✓ (requires E = einf∧eo) |

## Motor (PGA3, N3)

A rigid body motion: rotation followed by translation.

```python
from pytanga.geometry import Motor, Rotor, Translator, Direction
import math

m = Motor(
    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
```

| Algebra | Supported |
|---------|-----------|
| PGA3, N3 | ✓ |

## GeneralRotor

A rotation about an axis that does **not** pass through the origin. Takes
the rotation angle, axis direction, and an origin point on the axis.

```python
from pytanga.geometry import GeneralRotor, Direction, Point
import math

gr = GeneralRotor(
    angle=0.5,
    axis=Direction(0, 0, 1),
    origin=Point(1, 0, 0),
)
```

| Algebra | Supported |
|---------|-----------|
| PGA3, N3 | ✓ |

## Operator Coverage Matrix

| Operator | E3 | P3 | PGA3 | N3 | E2 | P2 | PGA2 | N2 |
|----------|:--:|:--:|:----:|:--:|:--:|:--:|:----:|:--:|
| ReflectionPlane | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| ReflectionLine | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ReflectionPoint | — | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Inversion | — | — | — | ✓ | — | — | — | ✓ |
| Rotor | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Translator | — | — | ✓ | ✓ | — | — | — | ✓ |
| Dilator | — | — | — | ✓ | — | — | — | ✓ |
| Motor | — | — | ✓ | ✓ | — | — | — | ✓ |
| GeneralRotor | — | — | ✓ | ✓ | — | — | — | ✓ |
