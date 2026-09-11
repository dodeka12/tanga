# Variables & Blade Masks

The `Geometry` facade can derive the blade mask that a geometric type occupies
in its algebra, and wrap it in a symbolic
[`Variable`](../expression/index.md) for the expression system.

```python
from pytanga.basis import BasisN3
from pytanga.geometry import Geometry, Point, Rotor

geo = Geometry(BasisN3())

R = geo.create_var("R", Rotor)   # Variable with the rotor blade mask
P = geo.create_var("P", Point)   # Variable with the point blade mask
```

`create_var(name, typ)` is shorthand for
`Variable(name, geo.mask_for(typ))`; the underlying primitive is
`mask_for(typ)`.

## `geo.mask_for(typ) → BladeMask`

Returns the [`BladeMask`](../blade-mask/index.md) of the blades a geometric type
occupies in this algebra.  It accepts either a **class** (the full type blade
set) or an **instance** (that instance's non-zero blades):

```python
from pytanga.geometry import Direction

geo.mask_for(Rotor)                          # scalar + all 3 Euclidean bivectors
geo.mask_for(Rotor(0.5, Direction(0,0,1)))   # scalar + e12 only
```

The mask is derived by constructing a generic instance of the type and
delegating to `create()`, so it always agrees with the creation pipeline —
including the `opns` interpretation for entities:

```python
alg = BasisN3()
geo = Geometry(alg)

geo.mask_for(Point).names()   # OPNS: grade-1 blades

alg.opns = False
geo.mask_for(Point).names()   # IPNS: grade-4 blades
```

Operators are independent of the `opns` flag.

## `geo.create_var(name, typ) → Variable`

Creates a `Variable` whose blade mask matches *typ*:

```python
R = geo.create_var("R", Rotor)
E = R * P * ~R            # build an expression over the variables
```

## `geo(name, typ) → Variable`

`Geometry` is callable with a `(name, type)` pair as a shortcut:

```python
R = geo("R", Rotor)
P = geo("P", Point)
```

This is equivalent to `create_var`.

## Example

See `py/examples/ga/expression/variable_rotor_entity.py` for a complete example
where both the rotor and the rotated point are variables, and the expression is
applied to a list of point entities in a single batched call.

## Unsupported types

Types without a concrete creation form raise — matching `create()`.  This
includes `ImagCircle`, `ImagSphere`, `ImagPointPair`, `TripleReflection`,
`VersorFactors`, and operators/entities not supported in a given algebra
(e.g. `Translator` in `BasisE3`).