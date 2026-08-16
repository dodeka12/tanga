# Basis Classes

pytanga provides eight **Basis** subclasses of `Algebra` that expose all
named basis blades as attributes: four for 3D geometry and four for 2D
geometry.  They are the recommended starting point for interactive work,
scripts, and notebooks.

See [`basis_usage.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/basis_usage.py) for three patterns
for working with named blades, and the per-algebra demo scripts listed below.

---

## 3D Basis Classes

### `BasisE3` — Euclidean 3D, $G(3, 0)$

Demo: [`base_e3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_e3_demo.py)

```python
from pytanga.basis import BasisE3

E3 = BasisE3()            # default dtype='float64'
```

**Named blades**

| Attribute | Blade | Bitmask |
|-----------|-------|---------|
| `e1` | $e_1$ | `0b001` |
| `e2` | $e_2$ | `0b010` |
| `e3` | $e_3$ | `0b100` |
| `e12` | $e_1 \wedge e_2$ | `0b011` |
| `e31` | $e_3 \wedge e_1$ | `0b101` |
| `e23` | $e_2 \wedge e_3$ | `0b110` |
| `I` | $e_1 \wedge e_2 \wedge e_3$ | `0b111` |

**Constructing multivectors** (string conversion)

```python
v = E3("e1 + 2 e2 + 3 e3")   # 1·e1 + 2·e2 + 3·e3
```

Geometric entities (points, lines, …) are created through the
[`geometry` submodule](../geometry/index.md), not on the basis classes.

**Display**

```python
E3.show(mv)               # print in grade order
E3.show(mv, "label")
E3.show(mv, "label", fmt=".6f")
```

---

### `BasisP3` — Projective 3D, $G(4, 0)$

Demo: [`base_p3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_p3_demo.py)

```python
from pytanga.basis import BasisP3

P3 = BasisP3()
```

**Named blades**: `e1`, `e2`, `e3`, `e4` (homogeneous direction), `I`.

**Constructing multivectors** (string conversion)

```python
p = P3("e1 + 2 e2 + 3 e3 + e4")    # homogeneous point (1, 2, 3)
```

Geometric entities (points, lines, …) are created through the
[`geometry` submodule](../geometry/index.md), not on the basis classes.

---

### `BasisN3` — Null/conformal 3D, $G(5, 0\text{b}10000)$

Demo: [`base_n3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_n3_demo.py)

`BasisN3` uses the null-vector embedding: `ep` ($e_4$, squares to $+1$) and
`em` ($e_5$, squares to $-1$) are combined into the conventional null vectors:

$$\text{einf} = e_p + e_m \qquad e_o = \tfrac{1}{2}e_m - \tfrac{1}{2}e_p$$

Background: [pga\_null\_embedding.md](pga_null_embedding.md).

```python
from pytanga.basis import BasisN3

N3 = BasisN3()
```

**Named blades**

| Attribute | Blade |
|-----------|-------|
| `e1`, `e2`, `e3` | Euclidean basis vectors |
| `ep` | $e_4$ ($e_p^2 = +1$) |
| `em` | $e_5$ ($e_m^2 = -1$) |
| `einf` | $e_p + e_m$ (point at infinity, alias `e0`) |
| `eo` | $\tfrac{1}{2}e_m - \tfrac{1}{2}e_p$ (origin point) |
| `I` | Pseudoscalar |

**Display**

`show()` prints in the `{e1, e2, e3, einf, eo}` display basis rather than
the raw `{e1, e2, e3, ep, em}` storage basis.

---

### `BasisPGA3` — PGA 3D

Demo: [`base_pga3_demo.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/base_pga3_demo.py)

`BasisPGA3` extends `Algebra` directly and implements the **Gunn/Dorst
plane‑based projective geometric algebra** (Gunn 2016, Dorst 2020).
It uses the Gunn/Dorst naming convention (``e₀`` for the null vector,
``e₀^{\text{inv}}`` for its inverse).  The names ``einf`` and ``eo``
(which belong to the N3 conformal model) are **not** exposed on this class.

A detailed description is in [`basis_pga3.md`](basis_pga3.md).

```python
from pytanga.basis import BasisPGA3

pga = BasisPGA3()
```

**Named blades**

| Attribute | Blade | Description |
|---|---|---|
| `e1`, `e2`, `e3` | Euclidean basis vectors | $e_1$, $e_2$, $e_3$ |
| `e0` | $e_p + e_m$ | Gunn/Dorst null vector, $e₀² = 0$ |
| `e0_inv` | $0.5·e_p - 0.5·e_m$ | Inverse of $e₀$, $⟨e₀·e₀^{\text{inv}}⟩₀ = 1$ |
| `ep` | $e_4$ ($e_p² = +1$) | Internal embedding (prefer `e0`) |
| `em` | $e_5$ ($e_m² = -1$) | Internal embedding (prefer `e0`) |

**Finite point** (IPNS / dual form):

$$p = x \cdot e_1 + y \cdot e_2 + z \cdot e_3 + e₀$$

The OPNS form is a grade‑3 trivector (intersection of three planes).

**Constructing multivectors** (string conversion)

```python
p = pga("e1 + 2 e2 + 3 e3 + e0")   # IPNS point (finite)
d = pga("e1 + 2 e2 + 3 e3")        # ideal point / direction
π = pga("e3 + e0")                 # plane z = 1 (normal +z, offset 1)
```

Geometric entities (points, lines, …) are created through the
[`geometry` submodule](../geometry/index.md), not on the basis classes.

**Entity grades (Gunn/Dorst convention):**

| Entity | OPNS Grade | IPNS Grade |
|---|---|---|
| Plane | 1 | 3 |
| Line | 2 | 2 (self‑dual) |
| Point | 3 | 1 |
| Direction | 3 | 1 ($e₀ = 0$) |
| Space | 4 | 0 (scalar) |

See also: [`geometry/pga3_entities.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/geometry/pga3_entities.py)
for a didactic introduction.


---

## 2D Basis Classes

### `BasisE2` — Euclidean 2D, $G(2, 0)$

```python
from pytanga.basis import BasisE2

E2 = BasisE2()
```

**Named blades:** `e1`, `e2`, `e12` (pseudoscalar `I`).

**Constructing multivectors** (string conversion)

```python
v = E2("3 e1 + 4 e2")              # 3·e1 + 4·e2
```

Rotors are created through the [`geometry` submodule](../geometry/index.md).

!!! note "No points in E2"
    E2 can only represent directions and rotors. For points, use P2, N2, or PGA2.

Detailed documentation: [basis\_e2.md](basis_e2.md).

---

### `BasisP2` — Projective 2D, $G(3, 0)$

```python
from pytanga.basis import BasisP2

P2 = BasisP2()
```

**Named blades:** `e1`, `e2`, `e3` (homogeneous direction), `I`.

**Constructing multivectors** (string conversion)

```python
p = P2("e1 + 2 e2 + e3")         # homogeneous point (1, 2)
d = P2("e1 + 2 e2")              # ideal point: x·e1 + y·e2 (no e3)
```

Geometric entities (points, lines, …) are created through the
[`geometry` submodule](../geometry/index.md), not on the basis classes.

Detailed documentation: [basis\_p2.md](basis_p2.md).

---

### `BasisN2` — Null/conformal 2D, $G(4, 0\text{b}1000)$

`BasisN2` uses the null-vector embedding: `ep` ($e_3$, squares to $+1$) and
`em` ($e_4$, squares to $-1$) are combined into the conventional null vectors:

$$\text{einf} = e_p + e_m \qquad e_o = -\tfrac{1}{2}e_p + \tfrac{1}{2}e_m$$

Background: [pga\_null\_embedding.md](pga_null_embedding.md).

```python
from pytanga.basis import BasisN2

N2 = BasisN2()
```

**Named blades**

| Attribute | Blade |
|-----------|-------|
| `e1`, `e2` | Euclidean basis vectors |
| `ep` | $e_3$ ($e_p^2 = +1$) |
| `em` | $e_4$ ($e_m^2 = -1$) |
| `einf` | $e_p + e_m$ (point at infinity) |
| `eo` | $-\tfrac{1}{2}e_p + \tfrac{1}{2}e_m$ (origin point) |
| `I` | Pseudoscalar |

**Display**

`show()` prints in the $\{e_1, e_2, \text{einf}, e_o\}$ display basis.

!!! note "Sphere = Circle in 2D"
    In N2, a "sphere" is a circle — the conformal model uses 3 points to
    define a sphere, which in 2D results in a circle.

Detailed documentation: [basis\_n2.md](basis_n2.md).

---

### `BasisPGA2` — PGA 2D

`BasisPGA2` extends `Algebra` directly and implements the **Gunn/Dorst
plane‑based projective geometric algebra** (Gunn 2016, Dorst 2020) for 2D
Euclidean geometry.  It uses the Gunn/Dorst naming convention (``e₀`` for
the null vector, ``e₀^{\text{inv}}`` for its inverse).  The names ``einf``
and ``eo`` (which belong to the N2 conformal model) are **not** exposed
on this class.

In plane‑based PGA, lines are the fundamental primitives (grade‑1 vectors),
and points are formed by intersecting two lines (grade‑2 bivectors).

A detailed description is in [`basis_pga2.md`](basis_pga2.md).

```python
from pytanga.basis import BasisPGA2

pga2 = BasisPGA2()
```

**Named blades**

| Attribute | Blade | Description |
|-----------|-------|-------------|
| `e1`, `e2` | Euclidean basis vectors | $e_1$, $e_2$ |
| `e0` | $e_p + e_m$ | Gunn/Dorst null vector, $e_0^2 = 0$ |
| `e0_inv` | $0.5 \cdot e_p - 0.5 \cdot e_m$ | Inverse of $e_0$ |
| `ep` | $e_3$ ($e_p^2 = +1$) | Internal embedding (prefer `e0`) |
| `em` | $e_4$ ($e_m^2 = -1$) | Internal embedding (prefer `e0`) |

**Constructing multivectors** (string conversion)

```python
p = pga2("e1 + 2 e2 + e0")        # IPNS point (finite)
d = pga2("e1 + 2 e2")             # ideal point / direction
ℓ = pga2("e1 + e0")               # line x = 1 (grade‑1 vector)
```

Geometric entities (points, lines, …) are created through the
[`geometry` submodule](../geometry/index.md), not on the basis classes.

**Entity grades (Gunn/Dorst convention):**

| Entity | OPNS Grade | IPNS Grade |
|--------|:----------:|:----------:|
| Line | 1 | 3 |
| Point | 2 | 2 (self‑dual) |
| Direction | 2 | 2 ($e_0 = 0$) |
| Space | 4 | 0 (scalar) |

---

### Three patterns for accessing named blades

[`basis_usage.py`](https://github.com/dodeka12/tanga/blob/main/py/examples/basis_usage.py) describes three patterns
in detail:

**Pattern 1 — Explicit assignment block (recommended)**

```python
E3 = BasisE3()
e1:  MV = E3.e1    # full type annotation, works with linters
e2:  MV = E3.e2
e3:  MV = E3.e3
I:   MV = E3.I
```

**Pattern 2 — Attribute access**

```python
E3 = BasisE3()
v = E3("e1 + 2 e2 + 3 e3")
print(E3.e1 * E3.e2)    # always works, no linter issues
```

**Pattern 3 — `globals().update(b.blades())`**

```python
E3 = BasisE3()
globals().update(E3.blades())   # injects e1, e2, … into module namespace
```

Note: pattern 3 is invisible to linters and type-checkers.
