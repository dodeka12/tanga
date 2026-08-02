# E3 – Euclidean 3D Space (Cl(3))

## Algebra Basis

| Type | Count | Basis Elements |
|------|-------|---------------|
| Scalar | 1 | 1 |
| 1-Vector | 3 | e₁, e₂, e₃ |
| 2-Vector | 3 | e₁₂, e₁₃, e₂₃ |
| 3-Vector | 1 | e₁₂₃ (= I, pseudoscalar) |

Total: 8 basis blades. Pseudoscalar I² = -1.

---

## Geometric Entities

In E3, **points cannot be represented**. Only lines and planes **through the origin** are representable, because all null spaces pass through the origin.

### GOPNS (Outer Product Null Space)

| Entity | Representation | Formula | Notes |
|--------|---------------|---------|-------|
| Line through origin | Grade 1 (vector) | NO_G(a) = { α a \| α ∈ R } | Direction given by a |
| Plane through origin | Grade 2 (bivector) | NO_G(a∧b) = { α a + β b \| α,β ∈ R } | Spanned by a and b |
| Whole space | Grade 3 (trivector) | NO_G(a∧b∧c) = { α a + β b + γ c } | a∧b∧c ∝ I |

Magnitude of a∧b = ‖a‖·‖b‖·sin(θ) = area of parallelogram.
Magnitude of a∧b∧c = volume of parallelepiped.

### GIPNS (Inner Product Null Space)

| Entity | Representation | Formula | Notes |
|--------|---------------|---------|-------|
| Plane | Grade 1 (vector) | NI_G(n) where n = dual(a∧b) | n = a × b (normal vector, right-handed) |
| Line | Grade 2 (bivector) | NI_G(n∧m) = NI_G(n) ∩ NI_G(m) | Intersection of two planes |
| Point (origin only) | Grade 3 (trivector) | NI_G(a∧b∧c) = {0} | Only the trivial solution (origin) |

The outer product in IPNS represents **intersection**: NI_G(n∧m) = NI_G(n) ∩ NI_G(m).

---

## Operators

All operators in E3 are about axes/lines/planes **through the origin**.

### Reflection

**Reflection of vector a on vector n** (line through origin):
```
n a n^(-1) = proj_ν(a) - rej_ν(a)
```
where ν = n/‖n‖. The component of a perpendicular to n is negated, the parallel component is unchanged.

**Reflection of a blade on a unit blade N_k**:
```
(-1)^(k+1) N_k a N_k^(-1) = proj_{N_k}(a) - rej_{N_k}(a)
```

**Reflection operator between vectors** (reflects x into y, including scaling):
```
refor(x, y) = sqrt(‖y‖/‖x‖) · (xu + yu) / ‖xu + yu‖
```
where xu = x/‖x‖, yu = y/‖y‖. This is the unit vector bisecting x and y.

### Rotation (Rotor)

Two consecutive reflections on unit vectors ν and μ produce a rotation by 2·∠(ν,μ) in the plane ν∧μ.

**Rotor definition** (rotation by angle θ in plane N₂ = (ν∧μ)/‖ν∧μ‖):
```
R(θ, N₂) = cos(θ/2) - sin(θ/2) · N₂
```

**Exponential form**:
```
R(θ, N₂) = exp(-(θ/2) · N₂)
```

**Rotation axis form (E3 only)** – using rotation axis r (normal to rotation plane):
```
R(θ, r)   with axis r = dual(N₂), N₂ = r·I
```

**Application**: R a R̃ rotates a by θ in plane N₂.

Rotor properties:
- R R̃ = 1 (unitary versor)
- Outermorphism: R (a₁∧a₂∧…∧a_k) R̃ = (R a₁ R̃) ∧ … ∧ (R a_k R̃)

### Mean Rotor

Given a set of N rotors {Rᵢ}, the approximate mean rotor is:
```
R_M = (Σ Rᵢ) / sqrt( (Σ R̃ᵢ)(Σ Rᵢ) )
```

---

## Geometric Interpretation of Inner Product

For x·(a∧b):
```
x·(a∧b) = (x·a)b - (x·b)a
```
The result is a vector perpendicular to x, lying in the plane a∧b. The inner product "subtracts" the subspace of x from the subspace of a∧b.

---

## Key Constraints

- **All entities pass through the origin** — no offset points, lines, or planes.
- **No point representation** — points require projective or conformal embedding.
- Transformations are limited to reflections and rotations about axes through the origin.