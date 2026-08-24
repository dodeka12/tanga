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
$$e_0^{\text{recip}} = \tfrac{1}{2}e_p - \tfrac{1}{2}e_m, \quad \langle e_0 \cdot e_0^{\text{recip}} \rangle_0 = 1$$

The names `einf` and `eo` (which belong to the N2 conformal model) are
**not** exposed on this class. Use `e0` and `e0_recip` instead.

Background: [pga\_null\_embedding.md](pga_null_embedding.md).

## Named Blades

| Attribute | Blade | Description |
|-----------|-------|-------------|
| `e1`, `e2` | Euclidean basis vectors | $e_1$, $e_2$ |
| `e0` | $e_p + e_m$ | Gunn/Dorst null vector, $e_0^2 = 0$ |
| `e0_recip` | $0.5 \cdot e_p - 0.5 \cdot e_m$ | Reciprocal of $e_0$ |
| `ep` | $e_3$ ($e_p^2 = +1$) | Internal embedding (prefer `e0`) |
| `em` | $e_4$ ($e_m^2 = -1$) | Internal embedding (prefer `e0`) |

## Constructing Multivectors

```python
p = pga2("3 e1 + 4 e2 + e0")     # IPNS point
d = pga2("e1")                   # ideal point / direction (no e0 component)
ℓ = pga2("e1 + 2 e0")            # line: nx·e1 + ny·e2 + d·e0 (grade‑1 vector)
```

Geometric entities are also available through the
[`geometry` submodule](../geometry/index.md), e.g.
`create_entity(pga2, Point(3, 4, 0))`.

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
line_x = pga2("e1")                     # line through origin along y-axis
line_y = pga2("e2")                     # line through origin along x-axis

# A point is the intersection (meet) of two lines
# OPNS: line_x ∨ line_y = bivector
origin = pga2.op(line_x, line_y)        # point at (0, 0)
pga2.show(origin, "origin (OPNS)")

# Point in IPNS (string conversion)
p = pga2("2 e1 + 3 e2 + e0")
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

## Meet / Join Convention (Gunn/Dorst)

For `BasisPGA2`/`BasisPGA3` the user-facing `MV.meet`/`MV.join` follow the
Gunn/Dorst convention, which is the opposite of the Hestenes/DFM07 convention
used by the other algebras (E2/E3/P2/P3/N2/N3):

| Operation | PGA2/3 (Gunn/Dorst) | Other algebras |
|---|---|---|
| `meet` | intersection (progressive/outer product `∧`) | regressive (largest blade contained in both) |
| `join` | union/span (regressive product `∨`) | progressive (smallest blade containing both) |

The outer (`^`/`op`) and inner (`|`/`ip`) products are **unchanged**; only the
`meet`/`join` names swap for the PGA models.

```python
from pytanga.basis import BasisPGA2
from pytanga.geometry import Geometry, Point, Line, Direction

pga2 = BasisPGA2()
geo = Geometry(pga2)
a = geo(Point(1, 0, 0))
b = geo(Point(0, 1, 0))

line = a.join(b)        # the connecting line (grade 1) — the *join* of two points

# meet of two lines is their intersection point
l1 = geo(Line(Point(0, 0, 0), Direction(1, 0, 0)))
l2 = geo(Line(Point(0, 0, 0), Direction(0, 1, 0)))
l1.meet(l2)             # grade-2 point (the origin)
```

## Incidence

Incidence in PGA is tested with the complement dual (J‑map / Hodge star `⋆`):
`⋆A ∧ ⋆B == 0`, equivalently `A.dual() ^ B.dual() == 0`. For example, a point
`P` lies on a line `L` iff:

```python
P.dual().op(L.dual()).is_zero   # True iff P is on L
```

This follows from the join identity `A ∨ B = ⋆(⋆A ∧ ⋆B)` (PGA4CS §9.2).

> **Note:** the metric-contraction form `A.dual() | B` is **not** valid in PGA:
> the PGA pseudoscalar `I₃ = e₀∧e₁∧e₂` is null (`I₃² = 0`), so dualization is a
> complement map, not the metric dual (PGA4CS §3.2, §9.1).

## Three Patterns for Accessing Blades

The same three patterns described in [Bases](bases.md#three-patterns-for-accessing-named-blades)
apply to `BasisPGA2`.