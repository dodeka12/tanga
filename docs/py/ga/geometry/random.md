# Random Entity Generation

The `pytanga.geometry` submodule provides deterministic, seedable random
generators for geometric entities.  Instead of hand-rolling random
coordinates, you build a **generator** object (`RndPoint`, `RndDirection`)
and pass it to a [`Geometry`](https://github.com/dodeka12/tanga/blob/main/py/pytanga/geometry/_geometry.py) instance, which materializes it
with the geometry's own random number generator and produces multivectors.

## Seeding

A `Geometry` instance owns its own NumPy random number generator, seedable at
construction time:

```python
from pytanga.geometry import Geometry
from pytanga.basis import BasisP3

geo = Geometry(BasisP3(), seed=123)
```

The generator is exposed as `geo.rng` (a `numpy.random.Generator`):

```python
import numpy as np
assert isinstance(geo.rng, np.random.Generator)
```

## Generating points

```python
from pytanga.geometry import RndPoint

geo = Geometry(BasisP3(), seed=0)

p = geo(RndPoint((-1, 1), (-2, 3), (1, 2)))          # a single point MV
pts = geo([RndPoint((-1, 1), (-2, 3), (1, 2))
           for _ in range(10)])                        # 10 point MVs
```

A `RndPoint` takes three positional coordinate specs (with default
`(-1.0, 1.0)` each):

```python
geo(RndPoint())                                       # all coords uniform (-1, 1)
geo(RndPoint((-2, 2)))                                # x uniform (-2, 2); y, z default
```

### `count`

Use the `count` keyword to return a list without a Python comprehension:

```python
pts = geo(RndPoint((-1, 1), (-2, 3), (1, 2), count=10))  # 10 point MVs
```

Returns a list of 10 `Point` entities (then converted to MVs).

## Distributions

A tuple coordinate spec means a uniform distribution.  To use another
distribution, pass a `Distribution` instance per coordinate.

Available distributions:
- `Uniform(low, high)`
- `Normal(mean=0.0, stddev=1.0)`

```python
from pytanga.geometry import Normal

mv = geo(RndPoint(Normal(0, 1), (-1, 1), Normal(2, 0.1)))
```

## Directions

`RndDirection` mirrors `RndPoint` exactly, returning `Direction` entities:

```python
from pytanga.geometry import RndDirection

d = geo(RndDirection((-1, 1), (-1, 1), (-1, 1)))
```

## How it works

`RndPoint` / `RndDirection` are lazy generators deriving from a common
`RndEntity` base.  `Geometry.__call__` checks for `RndEntity` instances,
calls them with `geo.rng`, and then routes the resulting `Point`/`Direction`
dataclasses through the algebra's `create` dispatcher — so the OPNS/IPNS flag
is honored automatically:

```python
from pytanga.basis import BasisN3

opns = Geometry(BasisN3(), seed=1)
ipns = Geometry(BasisN3(opns=False), seed=1)

print(max(opns(RndPoint()).grades))   # OPNS point grade
print(max(ipns(RndPoint()).grades))   # IPNS point grade