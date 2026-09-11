# BasisP2 — Projective 2D

`BasisP2` provides the projective 2D geometric algebra $G(3, 0)$ with named
blade attributes. It extends the Euclidean 2D basis with a homogeneous
coordinate, enabling point and line representations.

```python
from pytanga.basis import BasisP2

P2 = BasisP2()            # default dtype='float64'
```

## Algebra Properties

| Property | Value |
|----------|-------|
| Algebra | $G(3, 0)$ |
| Dimension | 3 |
| Signature | 0 (all positive) |
| Num blades | $2^3 = 8$ |

## Named Blades

| Attribute | Blade | Bitmask |
|-----------|-------|---------|
| `e1` | $e_1$ | `0b001` |
| `e2` | $e_2$ | `0b010` |
| `e3` | $e_3$ (homogeneous direction) | `0b100` |
| `e12` | $e_1 \wedge e_2$ | `0b011` |
| `e13` | $e_1 \wedge e_3$ | `0b101` |
| `e23` | $e_2 \wedge e_3$ | `0b110` |
| `e123` | $e_1 \wedge e_2 \wedge e_3$ | `0b111` |
| `I` | Pseudoscalar ($e_1 \wedge e_2 \wedge e_3$) | `0b111` |

## Constructing Multivectors

Points and directions are built from strings, or through the
[`geometry` submodule](../geometry/index.md):

```python
p = P2("3 e1 + 4 e2 + e3")   # x·e1 + y·e2 + e3  (homogeneous point)
d = P2("e1")                 # x·e1 + y·e2         (ideal point, at infinity)

# Equivalent, via the geometry submodule:
from pytanga.geometry import Direction, Point, create_entity
p = create_entity(P2, Point(3, 4, 0))
d = create_entity(P2, Direction(1, 0, 0))
```

## Display

```python
P2.show(p, "p")          # print in grade order
P2.show(p, "p", ".6f")   # with format specifier
```

## Example: Points and Lines

```python
from pytanga.basis import BasisP2

P2 = BasisP2()

# Create a point
p = P2("2 e1 + 3 e2 + e3")
P2.show(p, "point")               # e1 · 2 + e2 · 3 + e3 · 1

# Create a direction (ideal point at infinity)
d = P2("e1 + e2")
P2.show(d, "direction")           # e1 · 1 + e2 · 1 (no e3 component)

# A line through two points p and q is their outer product
q = P2("5 e1 + e2 + e3")
line = P2.op(p, q)                # p ∧ q = bivector in P2
P2.show(line, "line p∧q")
```

!!! note "Homogeneous coordinate"
    The third basis vector $e_3$ serves as the homogeneous coordinate.
    A point has coefficient 1 for $e_3$; a direction (ideal point) has
    coefficient 0. This distinction is encoded in the multivector
    coefficients (or handled automatically by the [`geometry`](../geometry/index.md)
    submodule).

## Three Patterns for Accessing Blades

The same three patterns described in [Bases](bases.md#three-patterns-for-accessing-named-blades)
apply to `BasisP2`.