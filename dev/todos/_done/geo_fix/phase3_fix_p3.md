# P3 — Projective 3D Space — Fix Plan

Reference: `dev/todos/geo_fix/p3_entities.md`

## Design Principle

**If an entity or operator cannot be represented in a given space, raise a
`ValueError` with an explanation — do NOT silently map it to something else
or approximate it.**

In P3:
- Points, lines (anywhere), and planes (anywhere) ARE representable.
- Directions (ideal points at infinity) ARE representable.
- Spheres, circles, point pairs, homogeneous points require N3.
- Rotation about axes through origin is representable.
- Translation, dilation, inversion, motors require N3.

---

## 1. Entity Coverage Audit

### GOPNS (Outer Product Representation)

| Entity | Perwass | Code (`create_p3.py`) | Code (`analysis_p3.py`) | Required Behaviour |
|--------|---------|----------------------|------------------------|-------------------|
| Point | A = Hop(a) = a + e₄ | `create_point()` → `x·e1 + y·e2 + z·e3 + e4` | grade 1, e4 ≠ 0 → Point(x/w, y/w, z/w) | **OK** |
| Direction (ideal point) | N (e4 = 0) | `create_direction()` → `x·e1 + y·e2 + z·e3` | grade 1, e4 ≈ 0 → Direction | **OK** |
| Line | A∧B = Hop(a)∧Hop(b) | `create_line()` → `point.op(direction)` where direction has e4=0 | grade 2 → Line (factorised) | **FIX formula** — use `Hop(a)∧Hop(a+d)`. |
| Plane | A∧B∧C (3 points) | `create_plane()` → 3 points via normal | grade 3 → Plane (via dual) | **OK** functionally |
| Space | Pseudoscalar e₁₂₃₄ | `create_space()` | grade 4 → Space | **OK** |
| Sphere | ❌ Requires N3 | – | – | **RAISE** `ValueError` |
| Circle | ❌ Requires N3 | – | – | **RAISE** `ValueError` |
| PointPair | ❌ Requires N3 | – | – | **RAISE** `ValueError` |
| HPoint | ❌ Requires N3 (uses e∞) | – | – | **RAISE** `ValueError` |

### GIPNS (Inner Product Representation)

| Entity | Perwass | Code | Required Behaviour |
|--------|---------|------|-------------------|
| Plane | â - α·e₄ | via `sdual()` of OPNS | **ADD direct formula**: `P = â - α·e₄` when `opns=False`. |
| Line | P₁∧P₂ | via `sdual()` | **OK** via dual |
| Point | P₁∧P₂∧P₃ | via `sdual()` | **OK** via dual |

---

## 2. Operator Coverage Audit

### Reflection Operators in P3

Perwass §"Reflections in Projective Space" (GAPrjSpc.tex lines 270–348) analyzes how reflections behave with the homogeneous embedding Hop(a) = a + e₄.

Key results:

**Reflection on a line through origin (direction N):**
Using the pure vector N (a direction, so N·e₄ = 0) as versor produces the **wrong** result — the parallel component flips instead of the perpendicular one. Perwass shows the correct operator is the bivector **N∧e₄** (the composition of reflecting first on e₄, then on N):
```
(N e₄) A (e₄ N) = N(−a + e₄) N = −N a N − e₄
→ projects to: N a N + e₄ = (a∥_N − a⊥_N) + e₄   ✓ correct line reflection
```

**Reflection about the origin:**
Using e₄ as the versor reflects a → −a (negates all Euclidean components):
```
e₄ A e₄ = e₄(a + e₄)e₄ = −a e₄ e₄ + e₄ = −a + e₄
→ projects to: −a   ✓ origin reflection
```

**Reflection on a plane through origin (normal N):**
Since the reflection plane has normal N, its IPNS is the vector N (grade 1). Acting as a versor on A = a + e₄:
```
N A N = a⊥_N − a∥_N + e₄
→ projects to: a⊥_N − a∥_N   (in-plane stays, normal flips)
```
This IS the correct plane reflection. The vector N interpreted as IPNS plane acts correctly as a versor in P3.

**Trivector reflection (dual of vector):**
A trivector T (grade 3) is dual to a vector v = T·I⁻¹. The versor action of T is equivalent to that of v up to an irrelevant overall sign (scalar factor cancels in projective space).

| Operator | Perwass | Code | Required Behaviour |
|----------|---------|------|-------------------|
| **Reflection on line** through origin | N∧e₄ (bivector) | (old `create_reflection()` was a vector — ambiguous) | **ADD `create_reflection_line(d)`** → bivector `d.x·e₁₄ + d.y·e₂₄ + d.z·e₃₄`. |
| **Reflection on plane** through origin | N (grade-1 vector, plane IPNS) | (old `create_reflection()` happened to produce this) | **ADD `create_reflection_plane(n)`** → grade-1 **vector** `n.x·e₁ + n.y·e₂ + n.z·e₃`. e₄ = 0. |
| **Reflection about origin** | e₄ (vector) | **MISSING** | **ADD `create_reflection_origin()`** → grade-1 vector with only e₄ component. |
| Rotor (rotation about axis through origin) | Same as E3: R = M·N | `create_rotor()` → same as E3 | **OK** (verify sign as in E3). |
| Translator | ❌ Requires N3 | – | **RAISE** `ValueError`. |
| Dilator | ❌ Requires N3 | – | **RAISE** `ValueError`. |
| Inversion | ❌ Requires N3 | – | **RAISE** `ValueError`. |
| Motor | ❌ Requires N3 | – | **RAISE** `ValueError`. |
| GeneralRotor | ❌ Requires N3 | – | **RAISE** `ValueError`. |
| GeneralDilator | ❌ Requires N3 | – | **RAISE** `ValueError`. |

### Why three separate reflection functions

The original `create_reflection()` produced a pure Euclidean vector with e₄ = 0. This is actually correct for a **plane** reflection in P3 (the vector N is the IPNS of the plane). But:

1. **Line reflection** requires the bivector N∧e₄ (composing with origin reflection to fix the sign).
2. **Plane reflection** via vector N works naturally in P3 because N as IPNS plane correctly flips the normal component and keeps the in-plane component.
3. **Origin reflection** is a separate operation using e₄ alone.

The three functions make the geometric semantics explicit and match Perwass's analysis.

---

## 3. Specific Fixes

### create_p3.py

| Function | Fix |
|----------|-----|
| `create_point()` | No change. |
| `create_direction()` | No change. |
| `create_line()` | Change to `Hop(origin) ∧ Hop(origin + direction)`. Both factors have e4=1. |
| `create_plane()` | Keep OPNS path. **ADD**: when `opns=False`, construct directly: `normal.x·e1 + normal.y·e2 + normal.z·e3 − signed_distance·e4`. |
| `create_space()` | No change. |
| `create_reflection()` | **REMOVE**. Replace with three functions below. |
| **`create_reflection_line(d)`** | Return bivector N∧e₄ = d.x·e₁₄ + d.y·e₂₄ + d.z·e₃₄ (grade 2). Use blade IDs E14, E24, E34. |
| **`create_reflection_plane(n)`** | Return grade-1 vector n.x·e₁ + n.y·e₂ + n.z·e₃ (e₄ = 0). IPNS of plane through origin. |
| **`create_reflection_origin()`** | Return e₄ (grade-1 vector with only component at blade E4). |
| `create_rotor()` | Verify sign convention (same as E3). |
| N3-only stubs | Raise `ValueError` for all 10 N3-only types. |

### analysis_p3.py

| Function | Fix |
|----------|-----|
| `_point_or_direction_from_coeffs()` | No change. |
| `_line_from_factors()` | Adapt to two homogeneous point factors (both e4≈1). |
| `_plane_from_trivector()` | Verify offset sign. |
| `_reflection_from_factor()` | **REPLACE** with three detectors: grade-2 bivector with e₄ factors → `ReflectionLine`; grade-1 vector e₄=0 → `ReflectionPlane`; grade-1 vector with only e₄ → `ReflectionOrigin`. |
| `_rotor_from_factors()` | No change. |

### operators.py

| Dataclass | Fix |
|-----------|-----|
| `Reflection` | **SPLIT** into `ReflectionLine(direction: Direction)`, `ReflectionPlane(normal: Direction)`, `ReflectionOrigin`. |

### create.py (dispatcher)

| Route | Fix |
|-------|-----|
| `create_operator(basis, ReflectionLine(...))` | Routes to `create_p3.create_reflection_line()`. |
| `create_operator(basis, ReflectionPlane(...))` | Routes to `create_p3.create_reflection_plane()`. |
| `create_operator(basis, ReflectionOrigin(...))` | Routes to `create_p3.create_reflection_origin()`. |

---

## 4. Implementation Checklist

### operators.py

- [ ] **Split `Reflection` into `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`**: Add dataclasses, update union type.

### Creation Functions (create_p3.py)
- [ ] **Add file header reference**: At top of `create_p3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Projective Space".`

- [ ] **`create_point()`**: No change.
- [ ] **`create_direction()`**: No change.
- [ ] **`create_line()`**: Change to `Hop(origin) ∧ Hop(origin + direction)`.
- [ ] **`create_plane(opns=True)`**: Keep 3-point construction.
- [ ] **`create_plane(opns=False)`**: Add direct IPNS: `P = â − α·e₄`.
- [ ] **`create_space()`**: No change.
- [ ] **`create_rotor()`**: Verify sign convention.
- [ ] **`create_reflection_line(d)`**: Return bivector d.x·e₁₄ + d.y·e₂₄ + d.z·e₃₄.
- [ ] **`create_reflection_plane(n)`**: Return grade-1 vector n.x·e₁ + n.y·e₂ + n.z·e₃.
- [ ] **`create_reflection_origin()`**: Return e₄ (blade E4).
- [ ] **Exception stubs (entities)**: `create_sphere`, `create_circle`, `create_point_pair`, `create_homogeneous_point` → raise `ValueError`.
- [ ] **Exception stubs (operators)**: `create_translator`, `create_dilator`, `create_inversion`, `create_motor`, `create_general_rotor`, `create_general_dilator` → raise `ValueError`.

### Analysis Functions (analysis_p3.py)
- [ ] **Add file header reference**: At top of `analysis_p3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Projective Space".`

- [ ] **`_point_or_direction_from_coeffs()`**: Verify. e4≈0 → Direction, e4≠0 → Point(x/w, y/w, z/w).
- [ ] **`_line_from_factors()`**: Adapt for two homogeneous point factors.
- [ ] **`_plane_from_trivector()`**: Verify offset sign.
- [ ] **Reflection detection**:
  - [ ] Grade-1 vector, e₄=0, Euclidean components present → `ReflectionPlane`.
  - [ ] Grade-1 vector, only e₄ component → `ReflectionOrigin`.
  - [ ] Grade-2 bivector with e₄ components (E14, E24, E34) → `ReflectionLine`.
- [ ] **`_rotor_from_factors()`**: No change. Verify.

### Dispatcher (create.py)

- [ ] Route `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin` to correct P3 functions.
- [ ] Verify N3-only stubs raise correctly.

### Tests

#### Entity Tests

- [ ] **Test: `create_point` round-trip**: `create_entity(basis_p3, Point(1,2,3))` → analyze → `Point(1,2,3)`.
- [ ] **Test: `create_direction` round-trip**: `create_entity(basis_p3, Direction(1,0,0))` → analyze → `Direction(1,0,0)`.
- [ ] **Test: `create_line` through origin**: `Line(origin=(0,0,0), direction=(1,0,0))` → analyze → Line through origin, direction (1,0,0).
- [ ] **Test: `create_line` offset**: `Line(origin=(1,2,3), direction=(1,0,0))` → analyze → pass-through point on line.
- [ ] **Test: `create_plane` OPNS round-trip**: `Plane(point=(1,0,0), normal=(0,0,1))` → analyze → same normal, point on plane.
- [ ] **Test: `create_plane` IPNS round-trip**: `Plane(point=(0,0,4), normal=(0,0,1)), opns=False` → analyze `opns=False` → Plane with z≈4.
- [ ] **Test: `create_space` round-trip**: `create_space(basis_p3, scale=2)` → analyze → `Space(scale=2)`.
- [ ] **Test: N3 entities raise**: Sphere, Circle, PointPair, HPoint → `ValueError`.
- [ ] **Test: N3 operators raise**: Translator, Dilator, Inversion, Motor, GeneralRotor, GeneralDilator → `ValueError`.

#### Reflection Line Tests

- [ ] **Test: `create_reflection_line` produces bivector**: Grade 2, components in E14, E24, E34.
- [ ] **Test: `create_reflection_line` round-trip**: create → analyze → `ReflectionLine(direction=(1,0,0))`.
- [ ] **Test: `create_reflection_line` application**: Apply N∧e₄ with N = (1,0,0) to Hop((1,2,3)) → project → (1, −2, −3). (Line along x: x stays, y,z flip.)

#### Reflection Plane Tests

- [ ] **Test: `create_reflection_plane` produces grade-1 vector**: e₄ = 0, Euclidean components = normal.
- [ ] **Test: `create_reflection_plane` round-trip**: create → analyze → `ReflectionPlane(normal=(0,0,1))`.
- [ ] **Test: `create_reflection_plane` application**: Apply N = (0,0,1) as versor to Hop((1,2,3)) → project → (1, 2, −3). (Plane normal z: xy stays, z flips.)

#### Reflection Origin Tests

- [ ] **Test: `create_reflection_origin` produces e₄**: Grade 1, only component at E4.
- [ ] **Test: `create_reflection_origin` application**: Apply to Hop(a) → project → −a.

#### Orthogonality Tests

- [ ] **Test: line vs plane reflection**: `create_reflection_line(e₃)` negates xy (keeps z). `create_reflection_plane(e₃)` negates z (keeps xy). Complementary.
- [ ] **Test: origin reflection**: `create_reflection_origin()` negates all three components. Composition of line and plane reflection on same axis? Origin = line(eₓ)∘line(e_y) or plane(⊥x)∘plane(⊥y) etc.

#### Rotor

- [ ] **Test: `create_rotor` round-trip**: `create_operator(basis_p3, Rotor(angle, axis))` → analyze → `Rotor(angle≈angle, axis≈axis)`.