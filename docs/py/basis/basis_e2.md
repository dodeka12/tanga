# BasisE2 — Euclidean 2D

`BasisE2` provides the Euclidean 2D geometric algebra $G(2, 0)$ with named
blade attributes. It is the simplest tangent-space algebra, supporting
vectors, bivectors, and rotors in the plane.

```python
from pytanga.basis import BasisE2

E2 = BasisE2()            # default dtype='float64'
```

## Algebra Properties

| Property | Value |
|----------|-------|
| Algebra | $G(2, 0)$ |
| Dimension | 2 |
| Signature | 0 (all positive) |
| Num blades | $2^2 = 4$ |

## Named Blades

| Attribute | Blade | Bitmask |
|-----------|-------|---------|
| `e1` | $e_1$ | `0b01` |
| `e2` | $e_2$ | `0b10` |
| `e12` | $e_1 \wedge e_2$ | `0b11` |
| `I` | Pseudoscalar ($e_1 \wedge e_2$) | `0b11` |

## Factory Methods

```python
v = E2.vector(3, 4)                     # 3·e1 + 4·e2

v_rnd = E2.rnd_vector((-5, 5), (0, 10)) # random vector in x∈[-5,5], y∈[0,10]

# Rotor: rotation by angle θ in the e12 plane (the only rotation plane in 2D)
r = E2.rotor(1.57, E2.e12)              # 90° CCW rotor
```

## Display

```python
E2.show(v, "v")          # print in grade order
E2.show(v, "v", ".6f")   # with format specifier
```

## Example: Vectors and Rotors

```python
from pytanga.basis import BasisE2
import math

E2 = BasisE2()

# Create vectors
a = E2.vector(1, 0)
b = E2.vector(0, 1)

# Geometric product
ab = a * b
E2.show(ab, "a*b")       # e12 (bivector)

# Rotor: rotate a by 90° CCW
R = E2.rotor(math.pi / 2, E2.e12)
a_rotated = R * a * ~R
E2.show(a_rotated, "R·a·R⁻¹")  # -e2 (e₁ → -e₂ clockwise by default convention)
```

!!! note "E2 has no points"
    E2 can only represent directions (vectors) and rotors. To work with points,
    use [BasisP2](basis_p2.md) (projective) or [BasisN2](basis_n2.md) (conformal).

## Three Patterns for Accessing Blades

The same three patterns described in [Bases](bases.md#three-patterns-for-accessing-named-blades)
apply to `BasisE2`:

**Pattern 1 — Explicit assignment (recommended)**

```python
E2 = BasisE2()
e1 = E2.e1
e2 = E2.e2
e12 = E2.e12
I = E2.I
```

**Pattern 2 — Attribute access**

```python
v = E2.e1 * E2.e2    # → e12
```

**Pattern 3 — Namespace injection**

```python
globals().update(E2.blades())
```
