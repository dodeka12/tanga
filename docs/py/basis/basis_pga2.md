# BasisPGA2 — Plane‑Based PGA 2D

`BasisPGA2` implements the **Gunn/Dorst plane‑based projective geometric
algebra** (Gunn 2016, Dorst 2020) for 2D Euclidean geometry. It extends
`Algebra` in 4 dimensions via the null-vector embedding $e_0 = e_p + e_m$
where $e_p^2 = +1$ and $e_m^2 = -1$.

In plane‑based PGA, lines are the fundamental primitives (grade‑1 vectors),
and points are formed by intersecting two lines (grade‑2 bivectors).

```python
from pytanga.basis import BasisPGA2

pga2 = BasisPGA2()        # default dtype='float64'
```

## Algebra Properties

| Property | Value |
|----------|-------|
| Algebra | $G(4, 0\text{b}1000)$ (Gunn/Dorst model) |
| Dimension | 4 |
| Signature | 0b1000 (one negative square for embedding) |
| Num blades | $2^4 = 16$ |
| Model | Plane‑based (lines are grade‑1 vectors) |

## Null Vector Embedding

`BasisPGA2` uses the Gunn/Dorst null vector convention:

$$e_0 = e_p + e_m, \quad e_0^2 = 0$$
$$e_0^{\text{inv}} = \tfrac{1}{2}e_p - \tfrac{1}{2}e_m, \quad \langle e_0 \cdot e_0^{\text{inv}} \rangle_0 = 1$$

The names `einf` and `eo` (which belong to the N2 conformal model) are
**not** exposed on this class. Use `e0` and `e0_inv` instead.

Background: [pga\_null\_embedding.md](pga_null_embedding.md).

## Named Blades

| Attribute | Blade | Description |
|-----------|-------|-------------|
| `e1`, `e2` | Euclidean basis vectors | $e_1$, $e_2$ |
| `e0` | $e_p + e_m$ | Gunn/Dorst null vector, $e_0^2 = 0$ |
| `e0_inv` | $0.5 \cdot e_p - 0.5 \cdot e_m$ | Inverse of $e_0$ |
| `ep` | $e_3$ ($e_p^2 = +1$) | Internal embedding (prefer `e0`) |
| `em` | $e_4$ ($e_m^2 = -1$) | Internal embedding (prefer `e0`) |

## Factory Methods

```python
p = pga2.point(3, 4)             # IPNS: x·e1 + y·e2 + e₀
                                   # OPNS: grade‑2 bivector (intersection of 2 lines)

d = pga2.direction(1, 0)         # IPNS: x·e1 + y·e2 (ideal point, no e₀ component)

ℓ = pga2.line(nx=1, ny=0, d=2)  # OPNS: nx·e1 + ny·e2 + d·e₀ (grade‑1 vector)
```

## Entity Grades (Gunn/Dorst Convention)

| Entity | OPNS Grade | IPNS Grade |
|--------|:----------:|:----------:|
| Line | 1 | 3 |
| Point | 2 | 2 (self‑dual) |
| Direction | 2 | 2 ($e_0 = 0$) |
| Space | 4 | 0 (scalar) |

## Example: Lines and Points

```python
from pytanga.basis import BasisPGA2

pga2 = BasisPGA2()

# A line: grade-1 vector in OPNS
line_x = pga2.line(nx=1, ny=0, d=0)    # line through origin along y-axis
line_y = pga2.line(nx=0, ny=1, d=0)    # line through origin along x-axis

# A point is the intersection (meet) of two lines
# OPNS: line_x ∨ line_y = bivector
origin = pga2.op(line_x, line_y)        # point at (0, 0)
pga2.show(origin, "origin (OPNS)")

# Point in IPNS from factory
p = pga2.point(2, 3)
pga2.show(p, "point (2,3) IPNS")        # e1·2 + e2·3 + e₀·1
```

## Display

`show()` prints in the $\{e_1, e_2, e_0\}$ display basis:

```python
pga2.show(mv, "label")       # print in display basis
pga2.show(mv, "label", ".6f")  # with format specifier
```

## Differences from BasisN2

Although both `BasisPGA2` and `BasisN2` are built on $G(4, 0\text{b}1000)$,
they are different models:

| Aspect | BasisPGA2 | BasisN2 |
|--------|-----------|---------|
| Model | Plane‑based (Gunn/Dorst) | Conformal |
| Null vector name | `e0` | `einf` / `eo` |
| Lines | Grade‑1 vectors (OPNS) | Grade‑3 blades |
| Points | Grade‑2 bivectors (OPNS) | Grade‑1 vectors (IPNS) |
| Sphere/Circle | Not available | Grade‑4 blade (IPNS) |
| Translations | Known limitation | Full support |

## Three Patterns for Accessing Blades

The same three patterns described in [Bases](bases.md#three-patterns-for-accessing-named-blades)
apply to `BasisPGA2`.