# Phase 5 — Add Missing N3 Entities and Operators

Reference: `dev/todos/geo_fix/n3_entities.md`

## Scope

Implement entities and operators described by Perwass in the N3 (conformal)
space that are **not yet implemented** in `py/pytanga/geometry/`. Phase 4 fixes
existing broken implementations; Phase 5 adds genuinely new ones.

---

## 1. Missing Entities

### 1.1 Imaginary Sphere (IPNS)

**Perwass**: `S = A + ½ρ² e∞` where A = Cop(a).

A sphere with center a and **imaginary** radius iρ. Geometrically: vectors inside the null cone (S² = −ρ²).

Unlike a real sphere (S² = ρ² > 0), the imag sphere has no real points satisfying `S·X = 0`. It represents an entity that only has a solution in complex Euclidean space.

| What | Details |
|------|---------|
| Dataclass | `ImagSphere(center: Point, radius: float)` |
| Creation | `create_imag_sphere(basis, center, radius)` → grade-1 vector `Cop(center) + ½·radius²·e∞` |
| Analysis | Dualize the OPNS (grade 4) → IPNS (grade 1) imag sphere. Extract center and radius via Perwass: `r² = −S²/(S·e∞)²` (negative), `a = proj_e123(S)/(−S·e∞)`. |
| OPNS | 4 points → grade 4 → dualize → imag sphere. (OPNS creation is the same as real sphere; it's the IPNS form that differs.) |

### 1.2 Imaginary Point Pair (OPNS / IPNS)

**Perwass**: The dual of a real circle `C̃ = dual(C)` is an outer product representation of an **imag point pair** — a point pair on line L with center X and **imaginary** separation 2·i·r (where r is the original circle's radius). Conversely, a real point pair Q = A∧B has dual `Q̃` which is an **imag circle** (see §1.3).

An imag point pair has no real points — the condition `X·PP = 0` has no real solution, just as an imag sphere has no real points.

| What | Details |
|------|---------|
| Dataclass | `ImagPointPair(center: Point, direction: Direction, separation: float)` — separation is the magnitude of the imaginary separation (i.e. the real number s where separation = i·s). Or simply reuse PointPair with an `is_imaginary: bool` flag. |
| Creation (OPNS) | Create two conformal points A, B for the center ± half the real separation along the direction, then dualize the resulting point pair. Or: dualize a real circle. |
| Creation (IPNS) | `S₁ ∧ S₂ ∧ S₃` where at least one of the spheres is imaginary, or the three real spheres do not intersect in real points. |
| Analysis | For a grade-3 blade P (OPNS): check the squared norm. If P·P < 0 → imag point pair (no real intersection). Extract line, center, and separation via Perwass formulas (same as real point pair, but separation will come out imaginary). |
| Relationship | `ImagPointPair = dual(Circle)`, `Circle = dual(ImagPointPair)`. Real circle ↔ imag point pair (and vice versa) via duality. |

### 1.3 Imaginary Circle (OPNS / IPNS)

**Perwass**: The dual of a real point pair `Q̃ = dual(Q)` is an outer product representation of an **imag circle** — a circle in plane P centered on X with **imaginary** radius i·d/2 (where d is the original point pair's separation). Conversely, a real circle C has dual `C̃` which is an **imag point pair** (see §1.2).

An imag circle has no real points — there is no real Euclidean point x whose conformal embedding satisfies `Cop(x) ∧ IC = 0`.

| What | Details |
|------|---------|
| Dataclass | `ImagCircle(center: Point, normal: Direction, radius: float)` — radius is the magnitude of the imaginary radius (i.e. the real number r where radius = i·r). Or reuse Circle with an `is_imaginary: bool` flag. |
| Creation (OPNS) | Dualize a real point pair. Or: create an IPNS representation `S₁ ∧ S₂` where at least one S is an imag sphere, then dualize. |
| Creation (IPNS) | `S₁_ip ∧ S₂_ip` where at least one sphere is imaginary, or two real spheres with no real intersection. |
| Analysis | For a grade-2 blade (IPNS circle): check `C·C`. If C·C < 0 → imag circle (Perwass: the radius `r = √(C·C)/(P·P)` may be imaginary). Extract center, normal, and imaginary radius via Perwass formulas. |
| Relationship | `ImagCircle = dual(PointPair)`, `PointPair = dual(ImagCircle)`. Real point pair ↔ imag circle (and vice versa) via duality. |

### 1.4 Circle with Arbitrary Normal (OPNS)

**Perwass**: `C = A ∧ B ∧ C` for three points on the circle.

The current `create_circle()` only works in the xy-plane.

| What | Details |
|------|---------|
| Fix | Accept a `normal: Direction` parameter. Construct 3 points on a circle centered at `center`, with given `radius`, lying in the plane perpendicular to `normal`. |
| Approach | Create two orthogonal unit vectors u, v in the plane (normal ⟂ u, normal ⟂ v, u ⟂ v). Then the 3 points are: `center + radius·u`, `center + radius·cos(2π/3)·u + radius·sin(2π/3)·v`, etc. |
| Analysis | Already partially done via circumcenter computation. Add Perwass formula path: `P = C∧e∞`, `C̃ = dual(C)`, `L = C̃∧e∞`, `U = dual(P)·L`, `r² = (C·C)/(P·P)`. |

### 1.5 Reflector (Reflection Operator Between Vectors)

**Perwass** (E3 section): `refor(x, y) = √(‖y‖/‖x‖) · (xu + yu) / ‖xu + yu‖`

A versor that reflects vector x into vector y (including possible scaling). This is the unit vector that bisects angle(x, y).

| What | Details |
|------|---------|
| Applies to | E3, P3, N3 (works with Euclidean vectors directly) |
| Dataclass | `Reflector(source: Direction, target: Direction)` |
| Creation | Compute unit vectors xu = x/‖x‖, yu = y/‖y‖. Return `√(‖y‖/‖x‖) · (xu + yu)` normalized to unit length. Grade 1 vector. |
| Analysis | Extract direction from grade-1 vector components. |

---

## 2. Missing Operators

### 2.1 General Rotor (Translated Rotor)

**Perwass**: `G = T·R·T̃`

A rotor (rotation) that is **translated** by t. Applying G to a point X: first translate by −t (bring rotation axis to origin), rotate with R, then translate back by t. This represents a rotation about an axis that does NOT pass through the origin.

Geometrically equivalent to a motor but constrained to a pure rotation (no screw component along the axis).

| What | Details |
|------|---------|
| Dataclass | `GeneralRotor(rotor: Rotor, translator: Translator)` (already exists in `operators.py`) |
| Creation | `create_general_rotor(basis, rotor: Rotor, translator: Translator)` → `T·R·T̃` = even-grade MV (scalar + 6 bivectors, no 4-vector). |
| Formula | Given angle θ, axis a, translation vector t: compute R = `cos(θ/2) − sin(θ/2)·(a·I)`, T = `1 − ½ t e∞`. Then G = T·R·T̃. |
| Analysis | From versor: extract rotor part (scalar + 3 Euclidean bivectors = e₂₃, e₃₁, e₁₂) and translator part (3 mixed bivectors = e₁∞, e₂∞, e₃∞). The original rotor is extracted from the Euclidean bivector part; the translation t is recovered from the mixed bivectors after factoring out the rotor. |
| Basis blades | Scalar(1) + e₂₃, e₃₁, e₁₂ + e₁∞, e₂∞, e₃∞ (7 components). No e₁₂₃∞ (4-vector) — that's the distinguishing feature vs. Motor. |

### 2.2 General Dilator (Translated Dilator)

**Perwass**: `D_t = T·D·T̃`

A dilation (isotropic scaling) about an arbitrary point t.

| What | Details |
|------|---------|
| Dataclass | `GeneralDilator(factor: float, translator: Translator)` (already exists, but `translator` is Optional and unused) |
| Creation | `create_general_dilator(basis, factor: float, center: Point)` → `D_t = T·D·T̃` where T = `1 − ½ t e∞` and D = `1 + (1-d)/(1+d)·e∞∧e₀`. |
| Analysis | From versor: scalar + e₁∞, e₂∞, e₃∞, e∞₀ blades. Extract translation from eᵢ∞ blades, factor from e∞₀ blade using Perwass formula. |
| Basis blades | Scalar(1) + e₁∞, e₂∞, e₃∞ + e∞₀ (5 components). |

### 2.3 Motor from Parameters

**Perwass**: `M = T·R` or `M = T₂·T₁·R·T̃₁`

A general Euclidean transformation: rotation + translation along the rotation axis (screw motion).

The current `create_motor()` requires pre-created Rotor and Translator objects. Add a convenience factory.

| What | Details |
|------|---------|
| Creation | `create_motor(basis, angle: float, axis: Direction, translation: Direction)` → M = T·R. First create R from angle/axis, T from translation, then multiply. |
| Analysis | Extract rotor (scalar + 3 Euclidean bivectors) and translator (3 mixed bivectors + 1 four-vector e₁₂₃∞). The screw decomposition is: translator parallel to rotation axis is the screw component; translator perpendicular is the offset of the rotation axis. |

---

## 3. Summary Table

| # | Entity / Operator | Type | Perwass Section | Status |
|---|-------------------|------|-----------------|--------|
| 1 | Imaginary Sphere | Entity (IPNS) | GAConfSpc_Rep §"Imaginary Spheres" | **New** |
| 2 | Imaginary Point Pair | Entity (OPNS/IPNS) | GAConfSpc_Ana | **New** — dual of real circle |
| 3 | Imaginary Circle | Entity (OPNS/IPNS) | GAConfSpc_Ana | **New** — dual of real point pair |
| 4 | Circle (arbitrary normal) | Entity (OPNS) | GAConfSpc_Rep §"Circle" | **Fix** (moved from Phase 4 mid-priority) |
| 5 | Reflector | Operator | GAEucSpc §"Reflection" (E3) | **New** — works across E3/P3/N3 |
| 6 | General Rotor | Operator | GAConfSpc_Op §"Rotations" | **New** (was `NotImplementedError`) |
| 7 | General Dilator | Operator | GAConfSpc_Op §"Dilations" | **New** (was `NotImplementedError`) |
| 8 | Motor from params | Operator | GAConfSpc_Op §"Rotations" | **New** convenience |

**Note**: `create_motor` already exists but only takes Rotor+Translator objects. Adding a parameter-based constructor is a convenience, not a new operator type.

---

## 4. Implementation Checklist

### entities.py / operators.py

- [ ] **Add `ImagSphere` dataclass**: `ImagSphere(center: Point, radius: float)`.
- [ ] **Add `ImagPointPair` dataclass**: `ImagPointPair(center: Point, direction: Direction, separation: float)`. Or add `is_imaginary: bool` flag to existing `PointPair`.
- [ ] **Add `ImagCircle` dataclass**: `ImagCircle(center: Point, normal: Direction, radius: float)`. Or add `is_imaginary: bool` flag to existing `Circle`.
- [ ] **Update `Entity` union type** to include `ImagSphere`, `ImagPointPair`, `ImagCircle`.
- [ ] **Verify `GeneralRotor` dataclass**: Already exists with `rotor: Rotor, translator: Translator`.
- [ ] **Verify `GeneralDilator` dataclass**: Already exists with `factor: float, translator: Optional[Translator]`.
- [ ] **Add `Reflector` dataclass**: `Reflector(source: Direction, target: Direction)`.
- [ ] **Update `Operator` union type** to include `Reflector`.

### create_n3.py — New Functions

- [ ] **Add/update file header reference**: Ensure `create_n3.py` has comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Conformal Space".`

- [ ] **`create_imag_sphere(basis, center: Point, radius: float)`**: Return IPNS sphere `Cop(center) + ½·radius²·e∞` (grade-1 vector). For `opns=True`, construct 4 OPNS points + dualize.
- [ ] **`create_imag_point_pair(basis, center, direction, separation, *, opns)`**: Return OPNS grade-3 blade representing an imag point pair. Can construct by dualizing a real circle, or by factoring two imag spheres. For `opns=False`, return IPNS form `S₁_ip ∧ S₂_ip ∧ S₃_ip`.
- [ ] **`create_imag_circle(basis, center, normal, radius, *, opns)`**: Grade check — in N3: OPNS PointPair = grade 2 (A∧B), dual of grade 2 = grade 3 → ImagCircle OPNS = grade 3. OPNS Circle = grade 3 (A∧B∧C), dual of grade 3 = grade 2 → ImagPointPair OPNS = grade 2. Construct by dualizing a real point pair. For `opns=False`, return IPNS form `S₁_ip ∧ S₂_ip`.
- [ ] **`create_circle(basis, center, normal, radius, *, opns)`**: Fix to accept `normal`. Construct 3 points on circle in plane ⟂ normal. (Moved from Phase 4 mid-priority.)
- [ ] **`create_general_rotor(basis, rotor: Rotor, translator: Translator)`**: Compute T = translator MV, R = rotor MV, return `T·R·T̃`. Verify result is even-grade with 7 components (no e₁₂₃∞).
- [ ] **`create_general_dilator(basis, factor: float, center: Point)`**: Compute T = translator to `center`, D = dilator with `factor`, return `T·D·T̃`.
- [ ] **`create_motor(basis, angle: float, axis: Direction, translation: Direction)`**: Convenience factory. Create R from angle/axis, T from translation, return `T·R`.

### create_e3.py / create_p3.py — Reflector

- [ ] **`create_reflector(basis, source: Direction, target: Direction)`**: Unit vector bisecting source and target, scaled by `√(‖target‖/‖source‖)`. Works in E3, P3, N3.

### analysis_n3.py — New Detection Paths

- [ ] **Add/update file header reference**: Ensure `analysis_n3.py` has comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Conformal Space".`

- [ ] **Imaginary Sphere detection**: In `_plane_or_sphere_n3()`, after dualizing to IPNS, check if `S̃² < 0` (imag sphere) vs `S̃² > 0` (real sphere). Extract center and radius.
- [ ] **Imaginary Point Pair detection**: For grade-3 OPNS blade, check if `P·P < 0` (imaginary) vs `P·P > 0` (real point pair or line/circle). Distinguish from line/circle by checking for e₁₂₃ component (line lacks it, circle has it). Use Perwass formulas; separation will be imaginary.
- [ ] **Imaginary Circle detection**: For grade-2 IPNS blade, check if `C·C < 0` (imag circle). Perwass: the radius formula `r = √((C·C)/(P·P))` may be imaginary. Also: the dual of a real PointPair is an imag circle — dual analysis path.
- [ ] **General Rotor detection**: In `_classify_quad_reflector()`, check if the versor has grade 4 component `e₁₂₃∞` (→ Motor) or not (→ GeneralRotor). Extract rotor from Euclidean bivectors, translator from mixed bivectors.
- [ ] **General Dilator detection**: In `_classify_double_reflector()`, when both e∞ and e₀ are present, check for eᵢ∞ components (→ GeneralDilator) vs only e∞₀ (→ Dilator). Extract factor from e∞₀, translation from eᵢ∞.

### create.py (dispatcher)

- [ ] Route `ImagSphere` → `create_n3.create_imag_sphere()`.
- [ ] Route `ImagPointPair` → `create_n3.create_imag_point_pair()`.
- [ ] Route `ImagCircle` → `create_n3.create_imag_circle()`.
- [ ] Route `Reflector` → algebra-specific `create_reflector()`.
- [ ] Route `GeneralRotor` → `create_n3.create_general_rotor()` (was `NotImplementedError`).
- [ ] Route `GeneralDilator` → `create_n3.create_general_dilator()` (was `NotImplementedError`).

### Tests — Imaginary Sphere

- [ ] **Test: `create_imag_sphere` IPNS**: `create_entity(basis_n3, ImagSphere(center=Point(1,2,3), radius=2), opns=False)` → grade-1 vector. Verify `S² = −4` (negative!).
- [ ] **Test: `create_imag_sphere` round-trip**: create IPNS → analyze `opns=False` → `ImagSphere(center≈(1,2,3), radius≈2)`.
- [ ] **Test: `create_imag_sphere` no real points**: S·X = 0 has no solution for any real point X. Verify: `S·Cop(x) ≠ 0` for several x.
- [ ] **Test: `create_imag_sphere` OPNS**: 4 points → dualize → still has S² < 0 → classified as imag sphere.

### Tests — Imaginary Point Pair

- [ ] **Test: `create_imag_point_pair` OPNS**: Dualize a real circle (grade 3) → grade-2 blade with P·P < 0.
- [ ] **Test: `create_imag_point_pair` round-trip**: create → analyze → `ImagPointPair` with correct center, direction, separation.
- [ ] **Test: `create_imag_point_pair` no real points**: The IPNS condition has no real solution.
- [ ] **Test: duality round-trip**: `dual(Circle) ≈ ImagPointPair`, `dual(ImagPointPair) ≈ Circle`. Real circle and imag point pair are duals.

### Tests — Imaginary Circle

- [ ] **Test: `create_imag_circle` OPNS**: Dualize a real point pair (grade 2) → grade-3 blade with C·C < 0.
- [ ] **Test: `create_imag_circle` round-trip**: create → analyze → `ImagCircle` with correct center, normal, imaginary radius.
- [ ] **Test: `create_imag_circle` no real points**: No real Euclidean point lies on it.
- [ ] **Test: duality round-trip**: `dual(PointPair) ≈ ImagCircle`, `dual(ImagCircle) ≈ PointPair`. Real point pair and imag circle are duals.

### Tests — Circle (Fixed)

- [ ] **Test: circle with normal (0,0,1)**: `create_circle(center=(0,0,0), normal=(0,0,1), radius=2)` → 3 points all have z=0.
- [ ] **Test: circle with normal (1,0,0)**: `create_circle(center=(0,0,0), normal=(1,0,0), radius=2)` → 3 points all have x=0.
- [ ] **Test: circle round-trip with arbitrary normal**: create → analyze → same center, normal, radius.

### Tests — Reflector

- [ ] **Test: reflector between parallel vectors**: `create_reflector(basis, Direction(1,0,0), Direction(2,0,0))` → unit vector (1,0,0) scaled by √2. Apply to (1,0,0) → (2,0,0).
- [ ] **Test: reflector between perpendicular vectors**: `create_reflector(basis, Direction(1,0,0), Direction(0,1,0))` → bisecting vector (1/√2, 1/√2, 0). Apply to (1,0,0) → (0,1,0).
- [ ] **Test: reflector round-trip**: create → analyze → Reflector with correct source and target.

### Tests — General Rotor

- [ ] **Test: `create_general_rotor` composition**: R = rotation by π/2 about z, T = translation (10,0,0). G = T·R·T̃. Apply G to point (0,0,0) → first translate (−10,0,0), rotate → (0,−10,0), translate back → (10,−10,0). Verify.
- [ ] **Test: `create_general_rotor` round-trip**: create → analyze → GeneralRotor with matching rotor and translator.
- [ ] **Test: `create_general_rotor` has 7 components**: Scalar + e₂₃, e₃₁, e₁₂ + e₁∞, e₂∞, e₃∞. No e₁₂₃∞.
- [ ] **Test: GeneralRotor vs Motor**: Motor = T·R has e₁₂₃∞ component (4-vector). GeneralRotor = T·R·T̃ has no 4-vector. Verify distinction in analysis.

### Tests — General Dilator

- [ ] **Test: `create_general_dilator` application**: Factor d=2, center=(1,0,0). Apply to point (2,0,0) → distance from center is 1, scaled to 2 → result (3,0,0).
- [ ] **Test: `create_general_dilator` round-trip**: create(factor=2, center=(1,0,0)) → analyze → GeneralDilator(factor≈2, translator=(1,0,0)).
- [ ] **Test: `create_general_dilator` has 5 components**: Scalar + e₁∞, e₂∞, e₃∞ + e∞₀.

### Tests — Motor Convenience

- [ ] **Test: `create_motor` from params**: `create_motor(basis, angle=π/2, axis=Direction(0,0,1), translation=Direction(10,0,0))` → analyze → Motor with matching rotor and translator.
- [ ] **Test: motor screw decomposition**: Apply motor (rotation + translation along axis) to point → verify both rotation and translation occur.