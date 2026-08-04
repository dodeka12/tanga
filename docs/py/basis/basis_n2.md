# BasisN2 — Conformal / Null 2D

`BasisN2` provides the 2D conformal geometric algebra $G(4, 0\text{b}1000)$
with named blade attributes. It uses the null-vector embedding with $e_p$
($e_3$, squares to $+1$) and $e_m$ ($e_4$, squares to $-1$) combined into the
conventional null vectors $\text{einf}$ and $e_o$.

```python
from pytanga.basis import BasisN2

N2 = BasisN2()            # default dtype='float64'
```

## Algebra Properties

| Property | Value |
|----------|-------|
| Algebra | $G(4, 0\text{b}1000)$ |
| Dimension | 4 |
| Signature | 0b1000 (one negative square) |
| Num blades | $2^4 = 16$ |

## Null Vector Embedding

`BasisN2` uses the null-vector embedding: $e_p$ ($e_3$, squares to $+1$) and
$e_m$ ($e_4$, squares to $-1$) are combined into the conventional null vectors:

$$\text{einf} = e_p + e_m \qquad e_o = -\tfrac{1}{2}e_p + \tfrac{1}{2}e_m$$

Background: [pga\_null\_embedding.md](pga_null_embedding.md).

## Named Blades

| Attribute | Blade |
|-----------|-------|
| `e1`, `e2` | Euclidean basis vectors |
| `ep` | $e_3$ ($e_p^2 = +1$) |
| `em` | $e_4$ ($e_m^2 = -1$) |
| `einf` | $e_p + e_m$ (point at infinity) |
| `eo` | $-\tfrac{1}{2}e_p + \tfrac{1}{2}e_m$ (origin point) |
| `I` | Pseudoscalar |

## Display

`show()` prints in the $\{e_1, e_2, \text{einf}, e_o\}$ display basis rather
than the raw $\{e_1, e_2, e_p, e_m\}$ storage basis. This makes conformal
geometry expressions readable in conventional notation.

```python
N2.show(mv, "v")          # print in display basis
N2.show(mv, "v", ".6f")   # with format specifier
```

## Example: Conformal Points and a Circle

```python
from pytanga.basis import BasisN2

N2 = BasisN2()

# Conformal point at (3, 4)
# IPNS: x·e1 + y·e2 + 0.5·(x²+y²)·einf + eo
p_c = N2.e1 * 3 + N2.e2 * 4 + N2.einf * 0.5 * (3*3 + 4*4) + N2.eo
N2.show(p_c, "point (3,4)")

# The inner product of two conformal points is proportional to distance²
q_c = N2.e1 * 5 + N2.e2 * 1 + N2.einf * 0.5 * (5*5 + 1*1) + N2.eo
dist_sq = -2 * N2.sp(p_c, q_c)
print(f"Distance²: {dist_sq}")   # (5-3)² + (1-4)² = 8

# A circle is the IPNS outer product of 3 conformal points
# (a grade-4 blade in N2)
```

!!! note "Sphere = Circle in 2D"
    In N2, a "sphere" is a circle. The conformal model uses 3 points to define
    a sphere, which in 2D results in a circle.

## Three Patterns for Accessing Blades

The same three patterns described in [Bases](bases.md#three-patterns-for-accessing-named-blades)
apply to `BasisN2`.