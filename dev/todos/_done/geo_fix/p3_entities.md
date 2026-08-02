# P3 – Projective 3D Space (Cl(4))

## Embedding

Euclidean vectors x ∈ R³ are embedded in R⁴ (projective/homogeneous space) via:

```
Hop: x ∈ R³ → A = x + e₄ ∈ R⁴
```

where e₄ is the homogeneous dimension. The homogenized vector is denoted A = Hop(x). Capital letters denote homogeneous vectors.

**Projection back to R³** (for vectors with non-zero e₄ component):
```
Aop: A → A / (A·e₄)
```
Then a = Hop⁻¹(A) = A/(A·e₄) - e₄.

Scaling a homogeneous vector has no effect on the represented entity:
```
NO_G(α·Hop(a)) = a   for α ≠ 0
```

Points at infinity (direction vectors) have zero homogeneous component.

---

## Geometric Entities

### GOPNS (Outer Product Representation)

| Entity | Representation | Formula |
|--------|---------------|---------|
| Point a | A = Hop(a) (Grade 1) | NO_G(A) = {a} |
| Line through a, b | A∧B (Grade 2) | NO_G(A∧B) = { λ(a-b) + b \| λ ∈ R } |
| Plane through a, b, c | A∧B∧C (Grade 3) | NO_G(A∧B∧C) = plane through a, b, c |

where A = Hop(a), B = Hop(b), C = Hop(c).

### GIPNS (Inner Product Representation)

| Entity | Representation | Formula |
|--------|---------------|---------|
| Plane | A = â - α·e₄ (Grade 1) | Plane with normal â (unit) and distance α from origin |
| Line | A∧B (Grade 2) | NI_G(A∧B) = NI_G(A) ∩ NI_G(B) — intersection of two planes |
| Point | A∧B∧C (Grade 3) | NI_G(A∧B∧C) = NI_G(A) ∩ NI_G(B) ∩ NI_G(C) — intersection of three planes |

**Plane in IPNS**: Given A = â - α·e₄ with ‖â‖ = 1, then NI_G(A) is the plane with normal â and orthogonal distance α from the origin. Proof: For X = x + e₄, X·A = 0 ⇔ x·â = α ⇔ the component of x parallel to â equals α.

Again, the outer product of IPNS representations gives the **intersection**: NI_G(A∧B) = NI_G(A) ∩ NI_G(B).

---

## Operators

### Reflection in Projective Space

A reflection about the homogeneous dimension e₄ (where e₄ is the additional dimension in P3, n=3 so e_{n+1}=e₄):
```
e₄ A e₄ = -a + e₄  ⇒  NO_G(e₄ A e₄) = -a   (reflection about origin in R³)
```

For a reflection on a direction vector N (point at infinity, N·e₄ = 0, ‖N‖ = 1):
```
N A N = (a^⊥ - a^∥) + e₄
```
This reflects the component of a that is **parallel** to N. To get the standard reflection (negating the perpendicular component), the operator N·e₄ must be used:
```
(N·e₄) A (e₄·N) = N (-a + e₄) N = -N a N - e₄
⇒ Aop(…) = N a N + e₄
```
This is the **reflection of a on the line with direction N** passing through the origin.

### Rotation (Rotor) in Projective Space

A rotation from two successive reflections on direction vectors N and M:
```
R = (M·e₄)·(N·e₄) = -M·N   (since e₄² = 1)
```
In projective space the rotor is:
```
R = -M·N
```
Since an overall scalar factor has no effect on homogeneous vectors, this is equivalent to the Euclidean rotor M·N. So **the same rotor representation can be used in Euclidean and projective space**.

---

## Key Insights

- **Points can now be represented** (as 1-dimensional subspaces in R⁴).
- Points at infinity (zero homogeneous component) are representable as **direction vectors**.
- Scaling a homogeneous vector does **not** change the entity it represents.
- The outer product of mixed-grade entities is valid — the homogeneous dimension (e₄) has e₄² = +1.
- Projective space uses the standard Euclidean metric (no negative-signature dimensions).