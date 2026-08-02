# Operator Data Classes

Operator data classes are algebra-independent `@dataclass` types that represent
versors (geometric transformations). They can be used as input to
[`create()`](create.md) and as output from [`analyze_operator()`](analysis.md).

All classes are imported from `pytanga.geometry` (defined in `pytanga.geometry.operators`).

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

## ReflectionOrigin

Reflection about the origin (trivector ``e₁∧e₂∧e₃``).

```python
from pytanga.geometry import ReflectionOrigin

refl_origin = ReflectionOrigin()
```

| Algebra | Supported |
|---------|-----------|
| P3, PGA3, N3 | ✓ |

## Inversion (N3 only)

Inversion in a sphere centered at the origin.

```python
from pytanga.geometry import Inversion, Point

inv = Inversion(origin=Point(0, 0, 0))
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

A uniform dilation (scaling) about the origin.

```python
from pytanga.geometry import Dilator

d = Dilator(factor=2.0)  # double all distances
```

The MV representation is `cosh(γ/2) + sinh(γ/2)·E` where γ = ln(factor) and E = einf∧eo.

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

A general even-grade versor with rotor + translator bivector parts
(like a Motor but without the grade‑4 term). Represents a rotation about
an axis that does **not** pass through the origin.

```python
from pytanga.geometry import GeneralRotor, Rotor, Translator, Direction

gr = GeneralRotor(
    rotor=Rotor(angle=0.5, axis=Direction(0, 0, 1)),
    translator=Translator(vector=Direction(1, 0, 0)),
)
```

| Algebra | Supported |
|---------|-----------|
| PGA3, N3 | ✓ |

## GeneralDilator (N3 only)

A general dilation with optional translation components.

```python
from pytanga.geometry import GeneralDilator, Translator, Direction

gd = GeneralDilator(
    factor=2.0,
    translator=Translator(vector=Direction(1, 0, 0)),
)
```

## Operator Coverage Matrix

| Operator | E3 | P3 | PGA3 | N3 |
|----------|:--:|:--:|:----:|:--:|
| ReflectionPlane | ✓ | ✓ | ✓ | ✓ |
| ReflectionLine | ✓ | ✓ | ✓ | ✓ |
| ReflectionOrigin | — | ✓ | ✓ | ✓ |
| Inversion | — | — | — | ✓ |
| Rotor | ✓ | ✓ | ✓ | ✓ |
| Translator | — | — | ✓ | ✓ |
| Dilator | — | — | — | ✓ |
| GeneralDilator | — | — | — | ✓ |
| Motor | — | — | ✓ | ✓ |
| GeneralRotor | — | — | ✓ | ✓ |
