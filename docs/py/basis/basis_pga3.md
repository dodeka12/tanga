# BasisPGA3 — Projective Geometric Algebra in 3D

This document describes the mathematical foundation of the ``BasisPGA3`` class
and its implementation of the **Gunn/Dorst plane‑based PGA** model within
TANGA's 5D null‑vector embedding.

**Related reading:**
- [pga_null_embedding.md](pga_null_embedding.md) — the general null‑vector
  embedding technique
- [bases.md](bases.md) — brief overview of all four basis classes

---

## 1. The Gunn/Dorst 4D PGA Model

``BasisPGA3`` implements the **plane‑based projective geometric algebra**
(PGA) described by Charles Gunn and Leo Dorst. In this model:

- **Planes** are grade‑1 vectors: a plane with unit normal ``n`` and signed
  distance ``d`` from the origin is ``n + d·e₀``.
- **Lines** are grade‑2 bivectors: the intersection of two planes.
- **Points** are grade‑3 trivectors: the intersection of three planes.
  The dual of a point trivector is a grade‑1 vector
  ``x·e₁ + y·e₂ + z·e₃ + e₀``.

| Model | Dim | Point | Plane | Line | Null vector |
|---|---|---|---|---|---|
| **Gunn/Dorst PGA** | 4 | Grade 3 (or dual grade 1) | Grade 1 | Grade 2 | ``e₀`` (true null, ``e₀² = 0``) |

The algebra is **G(3, 0, 1)** — three basis vectors squaring to +1, and one
null basis vector ``e₀`` with ``e₀² = 0``.

### 1.1 Key References

- **Charles Gunn** — *Geometric algebras for Euclidean geometry*
  (arXiv:1411.6502, 2016). The definitive modern treatment of 4D PGA
  (also called "rigid geometric algebra" or RGA).
- **Leo Dorst** — *A Guided Tour to the Plane‑Based Geometric Algebra PGA*
  (bivector.net/PGA4CS.html, 2020). An accessible tutorial for CS
  practitioners.

---

## 2. Our Implementation — 5D Null‑Vector Embedding

TANGA's Clifford algebra only supports metric signatures where every basis
vector squares to ±1. A true null vector (squaring to 0) cannot be
represented natively. We therefore **embed** the 4D PGA into a 5D algebra
via the null‑vector embedding:

$$
e₀ → e_p + e_m \qquad e_p² = +1,\; e_m² = -1
$$

The pair ``(e_p, e_m)`` generates the 5‑dimensional algebra
**G(5, 0b10000)**. The subspace ``{e₁, e₂, e₃, e₀}`` where
``e₀ = e_p + e_m`` is algebraically isomorphic to the Gunn/Dorst 4D PGA.

The inverse of the null vector is:

$$
e₀^{\text{inv}} = \tfrac{1}{2}\,e_p - \tfrac{1}{2}\,e_m
\qquad
\langle e₀ \cdot e₀^{\text{inv}} \rangle_0 = 1
$$

This embedding technique is fully documented in
[pga_null_embedding.md](pga_null_embedding.md).

### 2.1 Class Hierarchy

``BasisPGA3`` extends ``Algebra`` **directly** (not ``BasisN3``). It is
a standalone algebra class that does **not** inherit the N3 conformal
model. The names ``einf`` and ``eo`` (which belong to N3) are **not
exposed** on ``BasisPGA3``.

```python
from pytanga.basis import BasisPGA3
pga = BasisPGA3()

# Basis vectors
pga.e1      # e₁, blade ID 1
pga.e2      # e₂, blade ID 2
pga.e3      # e₃, blade ID 4
pga.e0      # e₀ = ep + em, the Gunn/Dorst null vector
pga.e0_inv  # inverse of e₀ = 0.5·ep − 0.5·em

# Internal embedding vectors (private; prefer e0)
pga.ep      # e₄, blade ID 8, ep² = +1
pga.em      # e₅, blade ID 16, em² = -1
```

### 2.2 Point Representation

A finite point at position ``(x, y, z)`` is represented in **IPNS (dual)
form** as a grade‑1 vector:

$$
P_{\text{IPNS}} = x \cdot e₁ + y \cdot e₂ + z \cdot e₃ + e₀
$$

which in raw blade terms is:

$$
P_{\text{IPNS}} = x \cdot e₁ + y \cdot e₂ + z \cdot e₃
    + e_p + e_m
$$

The **OPNS form** (grade‑3 trivector) is obtained by dualizing:

$$
P_{\text{OPNS}} = \text{dual}(P_{\text{IPNS}})
    = (e₁ - x·e₀) \wedge (e₂ - y·e₀) \wedge (e₃ - z·e₀)
$$

```python
p = pga.point(3, 4, 5)
# IPNS:  {e1:3, e2:4, e3:5, ep:1.0, em:1.0}
# OPNS:  dual → grade-3 trivector
```

An ideal point (direction at infinity) has **no e₀ component**:

$$
D_{\text{IPNS}} = x \cdot e₁ + y \cdot e₂ + z \cdot e₃
$$

```python
d = pga.direction(1, 0, 0)  # {e1:1}
```

### 2.3 Plane Representation

A plane with unit normal ``n = (n_x, n_y, n_z)`` and signed distance ``d``
from the origin is a grade‑1 vector:

$$
\Pi = n_x \cdot e₁ + n_y \cdot e₂ + n_z \cdot e₃ + d \cdot e₀
$$

```python
# Plane at z = 3, normal pointing in +z direction
plane = pga.plane(0, 0, 1, 3)
```

---

## 3. Entity Representations (Gunn/Dorst OPNS Grades)

| Entity | Grade | OPNS Representation | Description |
|---|---|---|---|
| Plane | 1 | ``n + d·e₀`` | Direct plane vector |
| Line | 2 | Intersection of 2 planes | Bivector: ``Π₁ ∧ Π₂`` |
| Point | 3 | Intersection of 3 planes | Trivector: ``Π₁ ∧ Π₂ ∧ Π₃`` |
| Direction | 3 | Dual has no e₀ component | Ideal point at infinity |
| Space | 4 | ``e₁ ∧ e₂ ∧ e₃ ∧ e₀`` | 4D pseudoscalar ``I₄`` |

### 3.1 IPNS Interpretation

In IPNS (dual) form, the grades are swapped:

| Entity | IPNS Grade | Description |
|---|---|---|
| Point | 1 | ``x·e₁ + y·e₂ + z·e₃ + e₀`` |
| Direction | 1 | ``x·e₁ + y·e₂ + z·e₃`` (no e₀) |
| Line | 2 | Grade-2 bivector (self‑dual in 4D sense) |
| Plane | 3 | Grade-3 trivector, dual of a plane vector |
| Space | 5 | Pseudoscalar ``I₅`` |

---

## 4. Operator Representations (Versors)

| Operator | Factor Count | Structure | Description |
|---|---|---|---|
| Reflection | 1 | ``R = n`` | Single reflector (plane normal), no null |
| Rotor | 2 | ``R = n₁·n₂`` | Two Euclidean reflectors → 3D rotation |
| Translator | 2 | ``T = 1 − ½∑ d_i·(e_i∧e₀)`` | Two null reflectors → translation |
| GeneralRotor | 2 | ``G = T·R·T̃`` | Rotation about displaced axis (``angle``, ``axis``, ``origin``), grades {0, 2} |
| Motor | 4 | ``M = T·R`` | Rotation + translation (rigid body motion) |
| ReflectionLine | 2 | ``d∧e₀`` | Reflection about a line through origin |
| ReflectionPoint | 3 | ``e₁∧e₂∧e₃`` | Reflection about the origin |

### 4.1 Rotor

Same Euclidean bivector basis as in E3/P3:

$$
R = \cos\frac{\theta}{2}
    + \sin\frac{\theta}{2}
      \big( a_x·e_{23} + a_y·e_{31} + a_z·e_{12} \big)
$$

**Blade basis:** ``{1, e23(6), e31(5), e12(3)}`` — 4 blades, grades 0 and 2.

### 4.2 Translator

$$
T = 1 - \frac{1}{2} \big(
       d_x·(e_1∧e₀)
     + d_y·(e_2∧e₀)
     + d_z·(e_3∧e₀) \big)
$$

where ``e_1∧e₀ = e_1∧e_p + e_1∧e_m`` (blades 9 and 17).

**Extraction:** ``d_x = -2·coeff[9]``, ``d_y = -2·coeff[10]``,
``d_z = -2·coeff[12]`` (read directly from bivector coefficients).

### 4.3 GeneralRotor

A general rotor applies a rotation about an axis that does **not** pass
through the origin. It is constructed from an ``angle``, ``axis``
(``Direction``), and ``origin`` (``Point`` on the axis):

```python
gr = GeneralRotor(
    angle=0.5,
    axis=Direction(0, 0, 1),
    origin=Point(1, 0, 0),
)
```

Internally, this is built by conjugating a Rotor with a Translator:
``G = T·R·T̃``. The result has grades {0, 2} (scalar + bivector),
distinguishing it from a Motor which also has a grade‑4 term.

**Analysis**: The Euclidean bivector part yields the rotation angle and axis;
the null bivector part encodes the axis displacement.

### 4.4 Motor

A motor is the geometric product of a translator and a rotor:

$$
M = T \cdot R
$$

In versor factorization, a motor produces 4 reflector factors
(2 Euclidean + 2 null). The analysis separates these into rotor (from
Euclidean factors) and translator (from versor coefficients).

---

## 5. Entity & Operator Coverage

| Entity | PGA3 | N3 | Note |
|---|---|---|---|
| Point | ✓ | ✓ | Gunn/Dorst grade 3 (OPNS) |
| Direction | ✓ | ✓ | Ideal point, no e₀ component |
| Line | ✓ | ✓ | Grade 2 (intersection of 2 planes) |
| Plane | ✓ | ✓ | Grade 1 vector |
| Space | ✓ | ✓ | Grade 4 pseudoscalar |
| PointPair | ✗ | ✓ | Requires full conformal structure |
| Circle | ✗ | ✓ | Requires full conformal structure |
| Sphere | ✗ | ✓ | Requires full conformal structure |

| Operator | PGA3 | N3 | Note |
|---|---|---|---|
| Reflection | ✓ | ✓ | |
| ReflectionLine | ✓ | ✓ | |
| ReflectionPoint | ✓ | ✓ | |
| Rotor | ✓ | ✓ | |
| Translator | ✓ | ✓ | |
| GeneralRotor | ✓ | ✓ | Rotation about displaced axis |
| Motor | ✓ | ✓ | |
| Inversion | ✗ | ✓ | Requires eo as independent element |
| Dilator | ✗ | ✓ | Requires ``E = e₀ ∧ e₀^{\text{inv}}`` |

---

## 6. Design Notes

### 6.1 Weight Normalization

Point extraction in analysis uses algebraic weight normalization. For a
grade‑1 IPNS point vector ``P = x·e₁ + y·e₂ + z·e₃ + α·e₀``, the
homogeneous weight ``α`` is extracted via:

$$
\alpha = \langle P \cdot e₀^{\text{inv}} \rangle_0
$$

The Euclidean coordinates are then ``(x/α, y/α, z/α)``. This handles
arbitrary scaling (centroids, interpolated points, versor‑transformed
points) correctly.

### 6.2 Blade‑ness Validation

Before factorizing a bivector as a line, the analysis checks that the
bivector is a simple blade (``B ∧ B = 0``). A non‑simple bivector
(a screw/motor bivector) raises ``ValueError`` with guidance to use
``analyze_operator`` instead.

### 6.3 Limitations

1. **5D embedding overhead.** The 4D Gunn/Dorst algebra is embedded in a 5D
   algebra, which means there are extra degrees of freedom (``ep`` and ``em``
   blades) that must be handled consistently.
2. **Motor decomposition** is non‑unique — the same motor can be factored
   in multiple ways.
3. **No native null vector.** A true G(3, 0, 1) implementation with a
   proper null basis vector may be considered in a future release.

---

## 7. References

### Gunn/Dorst 4D PGA (our implementation target)

| Publication | Authors | Year |
|---|---|---|
| *Geometric algebras for Euclidean geometry* | Charles Gunn | 2016 |
| *On the Homogeneous Model of Euclidean Geometry* (in *Guide to GA in Practice*) | Charles Gunn | 2011 |
| *A Guided Tour to the Plane‑Based Geometric Algebra PGA* | Leo Dorst | 2020 |

### Null‑vector embedding technique

| Publication | Authors | Year |
|---|---|---|
| *Geometric Algebra with Applications in Engineering* (esp. §4.2–4.3) | Christian Perwass | 2009 |
| [pga_null_embedding.md](pga_null_embedding.md) | — | — |

### General GA theory

| Publication | Authors | Year |
|---|---|---|
| *Geometric Algebra for Computer Science* | Dorst, Fontijne, Mann | 2007 |
| *Clifford algebras and spinors* (esp. §17.3) | Pertti Lounesto | 2001 |