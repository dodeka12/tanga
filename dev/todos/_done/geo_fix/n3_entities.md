# N3 – Conformal 3D Space (Cl(4,1))

## Basis and Signature

Conformal Geometric Algebra (CGA) is built on the Minkowski space R^(4,1): 4 basis vectors squaring to +1, 1 squaring to -1.

### Null Basis

Instead of e₊ (square +1) and e₋ (square -1), use the null basis:

```
e∞ = e₋ + e₊
e₀ = ½(e₋ - e₊)
```

Properties:
```
e∞² = 0,   e₀² = 0,   e∞·e₀ = -1
```

### Algebra Basis of Cl(4,1) [Table in Thesis]

| Type | Count | Basis Elements |
|------|-------|---------------|
| Scalar | 1 | 1 |
| Vector | 5 | e₁, e₂, e₃, e∞, e₀ |
| 2-Vector | 10 | e₂₃, e₃₁, e₁₂, e₁₀, e₂₀, e₃₀, e_{1∞}, e_{2∞}, e_{3∞}, e_{∞₀} |
| 3-Vector | 10 | e_{23∞}, e_{31∞}, e_{12∞}, e_{23₀}, e_{31₀}, e_{12₀}, e_{1∞₀}, e_{2∞₀}, e_{3∞₀}, e₁₂₃ |
| 4-Vector | 5 | e_{123∞}, e_{123₀}, e_{23∞₀}, e_{31∞₀}, e_{12∞₀} |
| 5-Vector | 1 | e_{123∞₀} (pseudoscalar I) |

Total: 32 basis blades. Pseudoscalar I² = -1.

---

## Conformal Embedding

A Euclidean vector x ∈ R³ is embedded in conformal space via Cop:

```
Cop(x) = x + ½ x² e∞ + e₀
```

Key properties:
- **Null cone**: For all x ∈ R³, (Cop(x))² = 0. All scaled versions α·Cop(x) represent the same point.
- **Projection back**: For a null-vector X with X² = 0:
  ```
  Cop⁻¹(X) = rej_{e∞∧e₀}( X / (-X·e∞) )
  ```
  Dividing by -X·e∞ scales the vector so its e₀ component is 1 (projects onto the horosphere).

- Distance measure: For A = Cop(a), B = Cop(b):
  ```
  A·B = -½ ‖a - b‖²
  ```
  The inner product of two conformal points gives (half) the squared Euclidean distance.

---

## Geometric Entities

### GIPNS (Inner Product Null Space)

| Entity | Grade | Formula | Notes |
|--------|-------|---------|-------|
| Point | 1 | A = Cop(a) | On the null cone: A² = 0 |
| **Sphere** | 1 | **S = A - ½ ρ² e∞** | Center a, radius ρ; S² = ρ² |
| Imaginary Sphere | 1 | S = A + ½ ρ² e∞ | Center a, imaginary radius i·ρ |
| **Plane** | 1 | **P = â + α e∞** | Normal â (unit), distance α from origin |
| Circle | 2 | C = S₁ ∧ S₂ | Intersection of two spheres |
| **Line** | 2 | **L = P₁ ∧ P₂** | Intersection of two planes |
| Point Pair | 3 | PP = S₁ ∧ S₂ ∧ S₃ | Intersection of three spheres |
| Homog. Point | 3 | P₁ ∧ P₂ ∧ P₃ | Intersection of three planes |
| Point | 4 | S₁ ∧ S₂ ∧ S₃ ∧ S₄ | Intersection of four spheres |

**Critical convention**: A sphere in IPNS is **always** constructed as:
```
S = A - ½ ρ² e∞
```
where A = Cop(a) is the center point. The sign is **minus** ½ρ² e∞, not plus. (Plus gives an imaginary sphere.)

**Plane in IPNS**: A plane with unit normal â and orthogonal distance α from the origin:
```
P = â + α e∞
```
A plane can also be represented as the difference of two null-cone vectors: P = A - B (perpendicular bisector plane of segment AB).

### GOPNS (Outer Product Null Space)

| Entity | Grade | Formula | Notes |
|--------|-------|---------|-------|
| Point | 1 | A = Cop(a) | Same as IPNS since A² = 0 |
| Point Pair | 2 | A ∧ B | Two points a, b |
| Homogeneous Point | 2 | A ∧ e∞ | Point a plus point at infinity |
| **Line** | 3 | **A ∧ B ∧ e∞** | Line through a and b |
| Circle | 3 | A ∧ B ∧ C | Circle through a, b, c (or line if collinear) |
| **Plane** | 4 | **A ∧ B ∧ C ∧ e∞** | Plane through a, b, c |
| **Sphere** | 4 | **A ∧ B ∧ C ∧ D** | Sphere through a, b, c, d |

**Parametric form for line** (OPNS): L = A ∧ B ∧ e∞ represents the set
```
NO_G(L) = { λ(a - b) + b | λ ∈ R }
```

**Parametric form for plane** (OPNS): P = A ∧ B ∧ C ∧ e∞ represents the set
```
NO_G(P) = { α(a-c) + β(b-c) + c | α,β ∈ R }
```

---

## Duality Between IPNS and OPNS

OPNS and IPNS are related by the dual (multiplication by the pseudoscalar I⁻¹):

```
NO_G(X) = NI_G(dual(X))
NI_G(X) = NO_G(dual(X))
```

Example: The OPNS representation of a sphere (grade 4, A∧B∧C∧D) is the dual of the IPNS representation of a sphere (grade 1, S = A - ½ρ² e∞).

---

## Operators

All operators in CGA are **versors** — multivectors that can be written as geometric products of vectors. They preserve grades (outermorphism).

### Reflection

A plane P = â + α e∞ (IPNS) acts as a reflection operator:
```
P X P   reflects point X on plane P
```

This works for **any plane, not necessarily through the origin**. The reflection of a general blade is:
```
P B P   (outermorphism)
```

### Inversion

A sphere S = e₀ - ½ e∞ (= -e₊, the unit sphere centered at origin) acts as an inversion operator:
```
S X S   inverts X in the unit sphere centered at the origin
```

In general, any sphere in IPNS acts as an inversion operator (inversion in that sphere).

The inversion of e∞ (point at infinity) in the unit sphere gives e₀ (origin):
```
S e∞ S ∝ e₀
```
The inversion of a line L = A∧B∧e∞ in S gives a circle through the origin:
```
S L S ∝ (S A S) ∧ (S B S) ∧ e₀
```

### Translator

A translation by vector t is given by:
```
T = 1 - ½ t e∞
```

**Exponential form**:
```
T = exp(-½ t e∞)
```

Properties:
- T T̃ = 1 (unitary versor)
- T e₀ T̃ = t + ½ t² e∞ + e₀ = Cop(t)
- T e∞ T̃ = e∞ (point at infinity is invariant under translation)
- (t e∞)² = t e∞ t e∞ = -t² e∞ e∞ = 0 (nilpotent)

A translator is equivalent to two consecutive reflections on **parallel** planes.

### Rotor

A rotor for rotation by angle θ in the plane N₂ (unit bivector) is:
```
R = cos(θ/2) - sin(θ/2) N₂
```

**Exponential form**:
```
R = exp(-(θ/2) N₂)
```

Properties:
- R R̃ = 1 (unitary versor)
- N₂² = -1
- A rotor is equivalent to two consecutive reflections on **intersecting** planes.
- The intersection line of the reflection planes is the rotation axis.
- In conformal space, a rotor at the origin has the **same form** as in Euclidean space.

### General Rotor (Translated Rotor)

A rotation about an axis that does not pass through the origin:
```
G = T R T̃
```
where T translates the rotation axis from the origin to its actual position.

Applying G to a point X: First translate by -t, rotate, then translate back.

### Motor (Screw)

A general Euclidean transformation (rotation + translation along rotation axis):
```
M = T₂ T₁ R T̃₁
```
or equivalently:
```
M = T' R'
```

A motor has grades 0, 2, 4 (scalar, bivector, 4-vector parts).

### Dilator

A dilation (isotropic scaling) by factor d about the origin:
```
D = 1 + (1-d)/(1+d) e∞∧e₀
```

A dilation is two consecutive inversions in co-centric spheres of different radii.

A general dilator centered at point t:
```
D_t = T D T̃
```
where T = 1 - ½ t e∞.

---

## Operator Summary [Table from Thesis]

| Operator | Grades | Count | Basis Elements |
|----------|--------|-------|---------------|
| Reflection | 1 | 4 | e₁, e₂, e₃, e∞ |
| Inversion | 1 | 5 | e₁, e₂, e₃, e∞, e₀ |
| Rotor R | 0,2 | 4 | 1, e₂₃, e₃₁, e₁₂ |
| Translator T | 0,2 | 4 | 1, e_{1∞}, e_{2∞}, e_{3∞} |
| Dilator D | 0,2 | 2 | 1, e_{∞₀} |
| Gen. Dilator T D T̃ | 0,2 | 5 | 1, e_{1∞}, e_{2∞}, e_{3∞}, e_{∞₀} |
| Motor R T | 0,2,4 | 8 | 1, e₂₃, e₃₁, e₁₂, e_{1∞}, e_{2∞}, e_{3∞}, e_{123∞} |
| Gen. Rotor T R T̃ | 0,2 | 7 | 1, e₂₃, e₃₁, e₁₂, e_{1∞}, e_{2∞}, e_{3∞} |

---

## Analysis of Blades (Extracting Parameters)

How to extract geometric parameters from given blade representations.

### Plane (OPNS, Grade 4)

Given P ∈ Cl[4](4,1) (OPNS plane), its dual is:
```
dual(P) = α (â + d e∞)
```
Extract:
```
â = proj_{e₁₂₃}(dual(P))    -- normal vector (E3 part)
α = ‖â‖                       -- scale
d = -dual(P)·e₀ / α          -- orthogonal distance from origin
```

### Sphere (OPNS, Grade 4)

Given S ∈ Cl[4](4,1) (OPNS sphere), its dual is the IPNS sphere:
```
dual(S) = α (A - ½ r² e∞)    where A = Cop(a)
```
Extract:
```
r² = (dual(S))² / (dual(S)·e∞)²        -- squared radius
a  = proj_{e₁₂₃}(dual(S)) / (-dual(S)·e∞)   -- center
```

For an IPNS sphere S itself:
```
S² = r²                    (after normalization)
r² = (S / (-S·e∞))²       (for arbitrarily scaled S)
```

### Line (OPNS, Grade 3)

Given L = A ∧ B ∧ e∞:
```
d = L · (e∞∧e₀)           -- direction vector (b - a)
X = d · L                 -- homogeneous point on line closest to origin
                           -- (X ≃ proj_L(e∞∧e₀))
```

The line direction is d, and X is the point on L closest to the origin (in homogeneous form).

### Point Pair (OPNS, Grade 2)

Given Q = A ∧ B (point pair a, b):
```
L = Q ∧ e∞                                -- line through the two points
Pd = Q · e∞                               -- dual of plane bisecting point pair
X = Pd · L                                -- midpoint (homogeneous point)
Sd = Q · L⁻¹                              -- normalized IPNS sphere with center X,
                                           --   radius = half the point separation
d = 2 √(Sd·Sd) = 2 √((Q·Q)/(L·L))        -- distance between points
```

### Circle (OPNS, Grade 3)

Given C = A ∧ B ∧ C (circle through a, b, c):
```
P = C ∧ e∞                                -- plane of the circle
Cd = dual(C)                               -- IPNS representation (grade 2)
L = Cd ∧ e∞                               -- line through centers of two spheres
                                           --   whose intersection is the circle
U = P meet L = dual(P) · L               -- center of circle (homogeneous point)
Sd = C · P⁻¹                              -- normalized IPNS sphere with circle's radius
r = √(Sd·Sd) = √((C·C)/(P·P))            -- radius of circle (may be imaginary!)
```

---

## Stratification of Spaces

Conformal space unifies Euclidean and projective space:

- **Projective-type entities**: Add ∧e∞ to an OPNS blade → same entity but in homogeneous/projective form.
  - Point: A → A ∧ e∞ (homogeneous point)
  - Line: A ∧ B → A ∧ B ∧ e∞ (line in OPNS)
  - Plane: A ∧ B ∧ C → A ∧ B ∧ C ∧ e∞ (plane in OPNS)

- **Euclidean-type entities**: Add ∧e∞∧e₀ to an OPNS blade:
  - A ∧ e∞∧e₀ = a ∧ e∞∧e₀ → line through origin with direction a
  - A ∧ B ∧ e∞∧e₀ → plane through origin

---

## Key Conventions and Potential Pitfalls

1. **Sphere IPNS sign**: S = A - ½ ρ² e∞ (minus, not plus). A plus sign gives an imaginary sphere.
2. **e∞·e₀ = -1**, not +1.
3. **Null cone**: Only vectors with X² = 0 represent actual points in R³.
4. **All operators are versors**: They act via sandwich product V X Ṽ.
5. **Homogeneous scaling**: Multiplying an IPNS or OPNS representation by a non-zero scalar does not change the represented entity.
6. **The radial extraction formula uses sign**: r² = (S/(−S·e∞))² — note the minus sign in the denominator.