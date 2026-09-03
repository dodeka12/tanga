# Random Entity Generation

The `pytanga.geometry` submodule provides deterministic, seedable random
generators for geometric entities.  Instead of hand-rolling random
coordinates, you build a **generator** object (`RndPoint`, `RndDirection`,
`RndMV`) and pass it to a [`Geometry`](https://github.com/dodeka12/tanga/blob/main/py/pytanga/geometry/_geometry.py) instance, which materializes it
with the geometry's own random number generator and produces multivectors.

> **Note:** the module-level `pytanga.random_mv` was removed.  Use
> `RndMV` (below) for random multivectors; `pytanga.random_mask` remains for
> random blade masks.

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
- `Constant(value)` — a fixed component (no randomness)

```python
from pytanga.geometry import Normal

mv = geo(RndPoint(Normal(0, 1), (-1, 1), Normal(2, 0.1)))
```

A component may also be a plain fixed value, which is turned into a
`Constant` automatically:

```python
mv = geo(RndPoint((-1, 1), 3.45, Normal(1.2, 0.1)))   # y is fixed at 3.45
```

## Directions

`RndDirection` mirrors `RndPoint` exactly, returning `Direction` entities:

```python
from pytanga.geometry import RndDirection

d = geo(RndDirection((-1, 1), (-1, 1), (-1, 1)))
```

## Random multivectors (`RndMV`)

For general multivectors (not geometric entities), use `RndMV(mask, spec)`.
The first argument is a `BladeMask`; the second is a sequence with **one entry
per blade** — a `Distribution`, a `(low, high)` uniform tuple, or a fixed
value.

```python
import numpy as np
from pytanga import BladeMask
from pytanga.geometry import RndMV, Normal

alg = BasisE3()
mask = BladeMask(alg, grades=[1])                     # e1, e2, e3

rnd = RndMV(mask, [(-1, 1), 3.45, Normal(1.2, 0.1)])
mv = rnd(np.random.default_rng(0))                    # one MV
```

`count` returns a list instead of a single MV:

```python
mvs = RndMV(mask, [(-1, 1), (-1, 1), (-1, 1)], count=10)(np.random.default_rng(0))
```

`RndMV` can also be passed to `Geometry`, which uses `geo.rng`:

```python
mv = geo(RndMV(mask, [(-1, 1), (-1, 1), (-1, 1)]))
```

Coefficients are cast to the algebra's dtype (integers for integer algebras).

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