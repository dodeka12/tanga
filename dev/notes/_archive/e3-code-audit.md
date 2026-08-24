# E3 Code Audit — Faithfulness to the Perwass Euclidean Space Model

**Date:** 31 July 2026  
**Scope:** `py/pytanga/basis/e3.py` + `py/pytanga/geometry/` (analysis_e3.py, create_e3.py, analysis.py, create.py)  
**Reference:** Perwass, *Geometric Algebra with Applications in Engineering*, Habilitation thesis, Chapter "Euclidean Space" (`GAEucSpc.tex`)

---

## A. Algebraic Embedding

### A.1 Signature and dimension

| Question | Answer |
|----------|--------|
| What is the target signature? | G(3, 0) — 3D Euclidean geometric algebra Cl(3) |
| How is it implemented? | `Algebra(3, 0, dtype)` — 3 basis vectors, all square to +1 |
| Is the embedding isomorphic to the target algebra? | ✅ Direct construction — no embedding needed. Cl(3) = G(3,0) |
| Are there unused basis vectors that could leak? | ✅ No — all 2³ = 8 blades of the algebra are used |

Perwass §"Euclidean Space" (eqn. GAGeo:E3:OPLine1): The algebra basis of Cl(3) is given in Table GAGeo:G3AlgBasis:
- Scalar (1), 1-vectors (e₁, e₂, e₃), 2-vectors (e₁₂, e₁₃, e₂₃), 3-vector (e₁₂₃)

**Verdict:** ✅ Faithful. The code constructs G(3,0) directly with no embedding overhead.

### A.2 Naming conventions

| Question | Answer |
|----------|--------|
| What notation does the primary reference use for basis vectors? | e₁, e₂, e₃, e₁₂, e₁₃, e₂₃, e₁₂₃ (Table GAGeo:G3AlgBasis) |
| Does the code use the same names? | e1, e2, e3, e12, e31, e23, I (= e123) |
| Are there aliases? Are they documented? | No aliases. `I` is the pseudoscalar attribute (`e123`). |
| Would a user familiar with the literature recognize the names? | Mostly. **One discrepancy:** Perwass uses `e₁₃`; the code uses `e₃₁`. |

**Naming note — e₃₁ vs e₁₃:** The code defines `self.e31 = self.op(self.e3, self.e1)` (line 25 of `basis/e3.py`), producing e₃∧e₁ = −e₁∧e₃ = −e₁₃. The blade ID is 5 (bitmask 101 = e₁∧e₃ in canonical bit ordering), but the displayed name is "e31" due to the construction order. The geometric algebra is unaffected (sign flips are consistent throughout), but users referencing the Perwass text may expect `e13` as the blade name. The display basis (`_display_basis`) generates names based on factor order, not strictly sorted indices.

**Verdict:** ✅ Functionally correct. ⚠️ Minor naming discrepancy (e₃₁ vs e₁₃) — cosmetic only, no algebraic impact.

### A.3 Dual / meet / join operations

| Question | Answer |
|----------|--------|
| How is the pseudoscalar defined? Is it invertible? | `I = e₁₂₃`, blade ID 7. I² = −1 in Cl(3) (Perwass confirms: pseudoscalar squares to −1). I is invertible: I⁻¹ = −I. |
| If not invertible, how is dualization implemented? | Not applicable — pseudoscalar is invertible. |
| Is the `meet` operator consistent with the reference model? | The Perwass text eqn. (GAGeo:E3:PlaneMeet1) defines meet of two planes as (a₁∧a₂) ∨ (b₁∧b₂) = −dual(n∧m) where n, m are plane normals. The code inherits meet from the Algebra base class (C++ backend), not overridden in E3. |
| Is the `join` operator consistent with the reference model? | Join is available via `blade_join()`; Perwass notes the join of two non-parallel planes through origin is the whole space I. |
| Do `meet` and `join` satisfy the Common Factor Axiom? | Not explicitly tested; inherited from C++ blade operations. |

The code does not reimplement meet/join — it relies on the C++ backend's `blade_join()` and the general `dual()`/`complement()` infrastructure. The signed dual `dual()` (formerly `sdual()`) computes ★A = A · I⁻¹, which correctly matches Perwass's definition (e.g., dual of vector = bivector, dual of bivector = vector). The bitwise `complement()` is not used for geometric dualization — it would give the wrong sign on the e₂ component (e₁₃ → e₂ instead of −e₂ in G(3,0)).

**Verdict:** ✅ Faithful. Dualization via `dual()` = A · I⁻¹ matches Perwass eqn. (GAGeo:E3:IPLinePlane1).

---

## B. Geometric Entities

### B.1 Entity grades and forms

Perwass §"Outer Product Representations" (GAGeo:E3:OPRep):

| Entity | OPNS grade | IPNS grade | Reference |
|--------|-----------|-----------|-----------|
| Line through origin | 1 (vector = direction) | 2 (bivector = intersection of two planes) | Eqn. (GAGeo:E3:OPLine1), §"Line" |
| Plane through origin | 2 (bivector = span of two vectors) | 1 (vector = normal) | Eqn. (GAGeo:E3:OPPlane1), §"Plane" |
| Space (whole ℝ³) | 3 (pseudoscalar) | 0 (scalar) | Eqn. (GAGeo:E3:OPSpace1), §"Point" |
| Point | Not representable in E3 | Grade 3 IPNS → trivial origin only | §"Point" (p. 279–300) |

Code implementation in `analysis_e3.py`:

| OPNS grade | Returns | IPNS grade | Returns |
|-----------|---------|-----------|---------|
| 1 | `Direction` | 1 | `Plane` (normal = vector) |
| 2 | `Plane` (through origin) | 2 | `Line` (through origin) |
| 3 | `Space` | 3 | raises `ValueError` ("trivial origin") |

**Verdict:** ✅ Matches Perwass exactly.

### B.2 Coordinate correspondence

#### B.2.1 Direction / Line through origin (OPNS grade-1)

**Perwass eqn. (GAGeo:E3:OPLine1):** NO_G(a) = {x ∈ Cl¹(3) : x∧a = 0} = {α·a : α ∈ ℝ}, a line through origin with orientation a.

**Code (`create_direction`):** Returns a grade-1 vector `{E1: x, E2: y, E3: z}` — correct.

**Code (`_direction_from_factor`):** Reads components directly from the grade-1 part — correct.

**Issue — Entity mismatch:** `create_line(basis, origin=(0,0,0), direction=d)` delegates to `create_direction`, producing a grade-1 vector. But `analyze_entity` on a grade-1 vector (OPNS) returns a `Direction`, not a `Line`. So the round-trip is:
```
Line → create → grade-1 MV → analyze → Direction
```
The entity type **changes**. This is because in E3, a "line through the origin" as an OPNS entity is syntactically indistinguishable from a direction vector. The `Line` dataclass has `origin` and `direction` fields, but the E3 analysis has no way to reconstruct the origin field (it's always implicitly (0,0,0)). This is a fundamental limitation of E3 — Perwass explicitly states "points cannot be represented through null spaces in Cl(3)" (eqn. GAGeo:E3:OPPlane1 paragraph).

**Verdict:** ✅ Correct coordinates. ⚠️ Entity type mismatch in round-trip (Line → Direction) — inherent to the E3 model, not a code bug. The `Direction` dataclass docstring says "Supported algebras: P3, N3/PGA3 (not E3)" but E3 **does** use it — the docstring is inaccurate.

#### B.2.2 Plane through origin (OPNS grade-2)

**Perwass eqn. (GAGeo:E3:OPPlane1):** NO_G(a∧b) = {α·a + β·b : (α,β) ∈ ℝ²}, the plane spanned by a and b.

**Code (`create_plane`, OPNS):** Creates IPNS vector (normal), then `dual()` (signed dual ★A = A · I⁻¹) to bivector. Expected bivector components: n_x·e₂₃ + n_y·e₃₁ + n_z·e₁₂. The test `test_create_plane_through_origin_opns` confirms this for normal (0,0,1): e23=0, e31=0, e12=±1 ✓.

**Code (`_plane_from_bivector`):** Reads (e23, e31, e12), normalizes, returns Plane through origin — correct.

**Verdict:** ✅ Faithful.

#### B.2.3 Plane through origin (IPNS grade-1)

**Perwass §"Plane":** A plane is represented by the IPNS of a vector normal to the plane: NI_G(n) where n = ★(a∧b) is the dual of the OPNS bivector.

**Code (`_plane_from_ipns_vector`):** Reads (e1, e2, e3), normalizes, returns Plane with normal = normalized vector — correct.

**Verdict:** ✅ Faithful.

#### B.2.4 Line through origin (IPNS grade-2)

**Perwass §"Line":** NO_G(a) = NI_G(★a). The IPNS of a bivector n∧m represents the intersection of two planes: NI_G(n∧m) = NI_G(n) ∩ NI_G(m).

**Code (`_line_from_ipns_bivector`):** Takes `dual()` (signed dual ★A = A · I⁻¹) of the IPNS bivector to get the direction vector, returns Line(origin=(0,0,0), direction=...). Matches eqn. (GAGeo:E3:IPLinePlane1): NI_G(n∧m) represents the intersection line.

**Verdict:** ✅ Faithful.

#### B.2.5 Space (OPNS grade-3)

**Perwass eqn. (GAGeo:E3:OPSpace1):** NO_G(a∧b∧c) is the whole space ℝ³, with a∧b∧c ∝ I.

**Code (`create_space`, `_analyze_entity_opns` grade 3):** Uses `blade_factorize_versor` to extract the scale. Correct.

**Verdict:** ✅ Faithful.

#### B.2.6 Point (not representable)

**Perwass:** "Points cannot be represented through null spaces in Cl(3)" (p. 60). The IPNS of a grade-3 trivector yields only the trivial origin solution.

**Code:** `create_point` raises `ValueError`. `_analyze_entity_ipns` grade 3 raises `ValueError` ("trivial origin"). Correct.

**Verdict:** ✅ Faithful.

### B.3 Round-trip fidelity

| Test | Result |
|------|--------|
| Direction OPNS create → analyze | ✅ Direction ratios preserved; length not preserved (no normalization) |
| Plane OPNS create → analyze | ✅ Normal is normalized; point=(0,0,0) preserved |
| Plane IPNS create → analyze | ✅ Normal is normalized; point=(0,0,0) preserved |
| Line IPNS create → analyze | ✅ Direction and origin (0,0,0) preserved |
| Space OPNS create → analyze | ✅ Scale preserved |

**Non-unit-length Direction:** `_direction_from_factor` reads raw coefficients without normalization. The Perwass reference uses an unnormalized vector a to define the line orientation — the geometric object is the 1D subspace, which is scale-invariant. The code preserves the raw length, which is useful information (the weight/orientation magnitude) but means round-trip may not reproduce the exact numeric values. The tests correctly verify direction ratios, not absolute values.

**Verdict:** ✅ Round-trip works correctly for the geometric meaning. ⚠️ Direction length is not normalized — design choice, not a bug.

### B.4 Linear combinations

**Centroids / weighted sums:** Not applicable in E3 since points cannot be represented. Only vectors (directions) and bivectors (planes) can be summed, giving new vectors/bivectors.

`Direction(1,0,0) + Direction(2,0,0) = Direction(3,0,0)` — analyzed correctly as a direction with length 3. This is geometrically meaningful (a line with stronger weight).

**Verdict:** ✅ Linear combinations are meaningful for E3 entities.

---

## C. Operators (Versors)

### C.1 Reflection operators

Perwass §"Reflection" defines two fundamental reflections:

1. **Reflection on a line (vector):** n a n⁻¹ = a^∥ − a^⊥ (eqn. GAGeo:Versor:Reflect3)
2. **Reflection in a plane (bivector):** (−1)^(k+1) B a B̃ = a^∥ − a^⊥ (eqn. GAGeo:E3:GenRefBlade), where k is the blade grade.

| Question | Reflection on Line | Reflection in Plane |
|----------|-------------------|---------------------|
| What grade is the versor? | 1 (vector) | 2 (bivector) |
| Does creation produce the correct MV? | ✅ `{E1: dx, E2: dy, E3: dz}` — correct | ✅ `{E23: nx, E31: ny, E12: nz}` — correct |
| Does analysis recognize it? | ✅ `ReflectionLine` | ✅ `ReflectionPlane` |
| Does sandwiching produce the expected result? | ✅ Tests confirm (e3 reflects x,y; z unchanged) | ✅ Tests confirm using −B v B̃ |

**Reflection on bivector sign:** Perwass eqn. (GAGeo:E3:GenRefBlade): (−1)^(k+1) B a B̃. For k=2 (bivector): (−1)³ = −1, giving −B a B̃. The code test (`test_reflection_plane_e3_application`) correctly applies `-rp_mv * v * rp_mv.rev()`.

**Reflection on line formula:** Perwass uses n a n⁻¹. The code uses `d * v * d.rev()`. Since n is a unit vector, n⁻¹ = n/||n||². The code's `rv.rev()` is the reverse; for a vector, rev(n) = n. The test `test_reflection_line_e3_application` confirms: `rl_mv * v * rl_mv.rev()` with d=(0,0,1) on v=(1,2,3) gives (-1,-2,3) ✓.

**Verdict:** ✅ Faithful. Both reflection types match Perwass exactly.

### C.2 Rotation operators

Perwass Lemma (GAGeo:E3:RotorDef1): A rotor rotating by angle θ in the plane spanned by unit vectors ν, μ is:
```
R(θ, ν∧μ) = cos(θ/2) − sin(θ/2) · (ν∧μ)/||ν∧μ||
```

The code (`create_rotor`) uses the **axis** form:
```
R = cos(θ/2) + sin(θ/2) · (ax·e₂₃ + ay·e₃₁ + az·e₁₂)
```

**Sign convention check:** Perwass uses −sin(θ/2)·N₂. The code uses +sin(θ/2)·axis_bivector. The docstring in `create_e3.py` (lines 147–155) explains: "Because I² = −1 and I = −Ĩ in Cl(3), the sign flips, giving +sin(θ/2)·axis_bivector." The conversion is:
- Perwass plane bivector N₂ = ν∧μ
- Code axis bivector = n·I⁻¹ where n is the rotation axis
- n·I⁻¹ = ★n = dual of n, which in Cl(3) gives a bivector orthogonal to n
- The relationship N₂ = −n·I⁻¹ (sign depends on handedness convention)

The tests confirm:
- +π/2 about z-axis rotates e₁ → −e₂ (clockwise looking from +z, consistent with a right-handed system) ✓
- +π/2 about z-axis rotates e₂ → e₁ ✓

Perwass's proof (Lemma GAGeo:E3:RotorDef1): R x R̃ = cosθ·x^∥ − sinθ·(x^∥ × r̂) + x^⊥, which is a right-handed rotation about axis r̂ by angle θ. The code tests confirm this convention.

**Round-trip:** `test_rotor_round_trip` checks that create → analyze returns the same angle and axis direction (up to sign flip from factor order in blade_factorize_versor) ✓.

| Question | Rotor |
|----------|-------|
| What grades does the versor have? | 0 + 2 (scalar + bivector) |
| Does creation produce the correct MV? | ✅ Correct |
| Does analysis recover the correct angle and axis? | ✅ Yes (angle via 2·acos(n₁·n₂), axis via n₁∧n₂) |
| Can it represent rotations about axes not through origin? | ❌ Not in E3 — only rotations about axes through origin. This matches Perwass: "In Euclidean space this confines the set of transformations to reflections and rotations about axes that pass through the origin" (p. 421) |
| Does it compose correctly? | ✅ Product of two rotors yields a rotor |

**Verdict:** ✅ Faithful. The sign convention is correctly documented and tested.

### C.3 Translation operators

Perwass explicitly states (p. 421): "To extend the set of available transformations, Euclidean space has to be embedded in other spaces." Translations are **not available in E3** — they require projective (P3) or conformal (N3) embedding.

**Code:** `create_translator` raises `ValueError` with message "Translators require conformal embedding (N3); not available in E3." ✓

**Verdict:** ✅ Correct constraint — matches Perwass.

### C.4 Motor / combined operators

Not available in E3. The code correctly raises `ValueError` for:
- `create_motor` → "Motors require conformal embedding"
- `create_general_rotor` → "General rotors require conformal embedding"
- `create_dilator` / `create_general_dilator` → "Dilators require conformal embedding"
- `create_inversion` → "Inversions require conformal embedding"
- `create_reflection_origin` → "Reflection about the origin requires projective (P3) embedding"

**Verdict:** ✅ Correct constraints.

### C.5 Operator round-trip fidelity

| Operator | create → analyze |
|----------|-----------------|
| ReflectionLine | ✅ Direction preserved |
| ReflectionPlane | ✅ Normal preserved (normalized) |
| Rotor | ✅ Angle and axis direction preserved (axis sign may flip from factor ordering) |

**Verdict:** ✅ Round-trip works for all supported E3 operators.

---

## D. Scale Handling (Homogeneous Coordinates)

### D.1 The fundamental question

In E3 there are **no homogeneous coordinates** — it is a purely Euclidean algebra G(3,0) with no projective or conformal embedding. Points are not representable, and entities are pure blades whose geometric meaning is invariant under uniform scaling of the form X → λX.

### D.2 Scale handling per entity type

| Entity type | Scale behavior | Code handling |
|-------------|---------------|---------------|
| Direction (grade-1) | λ·a represents the same line; length encodes weight/orientation | Raw coefficients preserved — no normalization |
| Plane OPNS (grade-2) | λ·(nₓe₂₃ + n_y·e₃₁ + n_z·e₁₂) is the same plane | Normal is normalized in analysis: n̂ = (bₓ, b_y, b_z) / ||b|| |
| Plane IPNS (grade-1) | λ·n is the same plane; only the normal direction matters | Normal is normalized in analysis |
| Line IPNS (grade-2) | λ·(n∧m) is the same intersection line | Direction from dual(), implicitly scale-invariant |
| Space (grade-3) | λ·I: scale represents signed volume | Scale extracted via blade_factorize_versor |
| Rotor | Must be unit: R·R̃ = 1 | Creation produces proper unit rotor; analysis recovers angle from normalized factors |
| ReflectionLine | λ·d: scale irrelevant (geometric effect via direction only) | Direction read directly |
| ReflectionPlane | λ·B: scale irrelevant (geometric effect via plane orientation only) | Normal normalized in analysis |

### D.3 Audit checklist for scale

| Question | Status |
|----------|--------|
| How is the homogeneous weight extracted? | Not applicable — E3 has no homogeneous dimension |
| Does the extraction work correctly in the presence of embedding? | Not applicable |
| Is the weight used to normalize coordinates? | Plane normals are normalized; Direction preserves raw length |
| What happens for unit-weight elements? | Works correctly |
| What happens for non-unit-weight elements? | Direction preserves raw components; Plane normalizes; Rotor analysis uses normalized factors |
| Does the rotor divide by the scalar part? | Not needed — factors are normalized by blade_factorize_versor |
| Are there edge cases where the weight is zero? | Zero vectors/bivectors are rejected with clear error messages |

**Verdict:** ✅ Scale handling is correct for the E3 model. No homogeneous coordinates issues exist.

---

## E. Code Quality

### E.1 Defensive checks

| Question | Status |
|----------|--------|
| Are zero MVs rejected early with a clear error? | ✅ `mv.is_zero` → "Zero MV does not represent a geometric entity" |
| Are scalar MVs rejected? | ✅ `mv.is_scalar` → "Scalar MV does not represent a geometric entity" |
| Are mixed-grade MVs diagnosed or handled? | ✅ `len(grades) > 1` → raises ValueError with grades listed |
| Are non-blade bivectors checked before factorization? | ⚠️ Not checked. The `_line_from_ipns_bivector` calls `mv.dual()` directly without verifying the IPNS bivector is a simple blade. However, since it comes from the outer product of two IPNS plane vectors (n∧m), it is always simple by construction. The IPNS analysis only accepts pure-grade MVs (mixed grades are rejected), so a non-simple bivector cannot reach this code path. |
| Are zero-length normals handled? | ✅ `_plane_from_bivector`: "Zero bivector – not a valid plane"; `_plane_from_ipns_vector`: "Zero vector – not a valid IPNS plane"; `_reflection_plane_from_bivector`: "Zero bivector – not a valid reflection plane" |

### E.2 Dead code / correctness

| Question | Status |
|----------|--------|
| Are there overwritten/commented-out computations? | ✅ No dead code found |
| Are there comments indicating unresolved bugs? | ✅ No |
| Are manual blade ID assignments robust? | ✅ Blade IDs are declared as module-level constants (E1=1, E2=2, E3=4, E12=3, E31=5, E23=6, E123=7) — clear and consistent |

### E.3 Completeness

| Question | Status |
|----------|--------|
| Does creation implement all entity types the reference supports? | ✅ Direction, Line (through origin), Plane (through origin), Space. Point raises ValueError (correct). |
| Does analysis recognize all operator types that can arise? | ✅ ReflectionLine, ReflectionPlane, Rotor |
| Are there stub-only creation functions that raise ValueError for supported entities? | ✅ N3-only stubs exist for: Sphere, Circle, PointPair, HPoint, Translator, Dilator, Inversion, Motor, GeneralRotor, ReflectionOrigin, GeneralDilator — all raise clear ValueError |

### E.4 Inaccurate docstring

The `Direction` dataclass docstring in `entities.py` (line 53) states:
> "Supported algebras: P3, N3/PGA3 (not E3)"

This is **incorrect**. In E3, `Direction` is used as the OPNS representation of a line through the origin (grade-1 vector). The `analysis_e3.py` module returns `Direction` from `_direction_from_factor`. The docstring should list E3 as a supported algebra.

**Verdict:** ⚠️ `Direction` docstring incorrectly excludes E3.

---

## F. Cross-Module Consistency

### F.1 Entities ↔ Operators

| Question | Status |
|----------|--------|
| Are entity and operator dataclasses used consistently? | ✅ `Direction`, `Plane`, `Line`, `Space`, `ReflectionLine`, `ReflectionPlane`, `Rotor` all used in creation and analysis |
| Do the dataclasses cover all types used by the viz module? | ✅ E3 only produces a subset of the full types — viz handles all |

### F.2 Analysis ↔ Creation

| Question | Status |
|----------|--------|
| Does the analysis dispatcher correctly route to E3? | ✅ `_detect()` returns `'e3'` for `BasisE3` instances → `analysis_e3.analyze_entity` / `analyze_operator` |
| Does the creation dispatcher correctly route to E3? | ✅ Same `_detect()` logic → `create_e3` module |
| Is basis detection reliable (subclass checks in correct order)? | ✅ `BasisPGA3` checked before `BasisN3`; `BasisP3` before `BasisE3` — correct order |

### F.3 Visualization pipeline

The E3 module produces only a subset of entity/operator types. All types it produces are handled:
- `Direction` → `renderers/direction.js`
- `Plane` → `renderers/plane.js`
- `Line` → `renderers/line.js`
- `Space` → `renderers/space.js`
- `ReflectionLine` → `renderers/operators/reflection_line.js`
- `ReflectionPlane` → `renderers/operators/reflection_plane.js`
- `Rotor` → `renderers/operators/rotor.js`

**Verdict:** ✅ All E3 entity/operator types have corresponding renderers.

---

## G. Edge Cases and Stress Tests

### G.1 Origin and infinity

| Test | Expected behavior | Code behavior |
|------|------------------|---------------|
| Line not through origin | ValueError | ✅ "only lines through the origin can be represented" |
| Plane not through origin | ValueError | ✅ "only planes through the origin can be represented" |
| Point at origin | Not representable in E3 | ✅ `create_point` raises ValueError |
| Direction at large coordinates | Should work | ✅ No issues (raw float components) |
| Zero vector | Zero MV error | ✅ "Zero MV does not represent a geometric entity" |
| Zero bivector | Zero MV error | ✅ "Zero bivector – not a valid plane" |

### G.2 Degenerate configurations

| Test | Expected behavior | Code behavior |
|------|------------------|---------------|
| Two parallel planes wedged → ideal line | Not representable in E3 (all planes through origin) | All non-identical planes through origin intersect in a line through origin — no "parallel" case exists |
| Non-simple bivector analyzed as line | Should be rejected by mixed-grade check | Mixed grades are rejected; pure grade-2 must be simple in Cl(3) (all bivectors in 3D are simple) |

**Note:** In Cl(3), all bivectors are simple (any bivector in 3D is a 2-blade). This is a special property of 3D, noted by Perwass. So the "non-simple bivector" edge case cannot occur in E3.

### G.3 Composition

| Test | Expected behavior | Code behavior |
|------|------------------|---------------|
| Direction + Direction → weighted sum | Analysis preserves raw length | ✅ Correct |
| R₁ · R₂ → composite rotor | Analysis recognizes as Rotor | ✅ Correct (factorization produces 2 factor vectors) |
| ReflectionLine · ReflectionLine → Rotor | Two line reflections compose to a rotation | ✅ `analyze_operator` with 2 factors → `_rotor_from_factors` |

### G.4 Rotor composition

Two reflection lines (grade-1 vectors) applied sequentially:
```python
# Perwass: μ a μ · ν a ν = (μν) a (νμ) = R a R̃
R = create_reflection_line(d2) * create_reflection_line(d1)
```
This produces a rotor (scalar + bivector). `analyze_operator` → `_rotor_from_factors` ✓.

**Verdict:** ✅ Composition works correctly.

---

## H. Summary of Findings

### ✅ Passing — Faithful to Perwass

| # | Item | Details |
|---|------|---------|
| 1 | Algebraic signature | G(3,0) = Cl(3) — direct construction, no embedding |
| 2 | Basis blade structure | 8 blades: scalar, 3× vector, 3× bivector, 1× trivector |
| 3 | OPNS entity grades | Grade 1 = line, Grade 2 = plane, Grade 3 = space — matches Perwass |
| 4 | IPNS entity grades | Grade 1 = plane, Grade 2 = line, Grade 3 = trivial origin — matches Perwass |
| 5 | Point non-representability | Correctly raises ValueError — matches Perwass statement |
| 6 | Plane creation/analysis | Normal vector ⇔ bivector via dual() — correct |
| 7 | Line IPNS creation/analysis | n∧m → intersection of two planes — correct |
| 8 | Space creation/analysis | Pseudoscalar with scale — correct |
| 9 | Rotor creation | cos(θ/2) + sin(θ/2)·axis_bivector — sign convention documented and tested |
| 10 | Rotor analysis | 2·acos(n₁·n₂), axis from n₁∧n₂ — correct |
| 11 | Reflection on line | Grade-1 vector: d v d.rev() — matches Perwass eqn. |
| 12 | Reflection in plane | Grade-2 bivector: −B v B̃ — matches Perwass (−1)^(k+1) convention |
| 13 | Translation not available | Correctly raises ValueError — matches Perwass |
| 14 | All N3 stubs raise ValueError | Clear error messages for unsupported operations |
| 15 | Defensive checks | Zero MV, scalar MV, mixed grades all rejected with clear errors |
| 16 | Cross-module consistency | Dispatchers, dataclasses, and renderers all aligned |
| 17 | Dual operation | dual() = ★A = A · I⁻¹ with I² = −1 — matches Perwass |
| 18 | Test coverage | Comprehensive tests for all entity and operator types |

### ⚠️ Minor Issues (Cosmetic / Documentation)

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 1 | Blade name e₃₁ vs e₁₃ | `basis/e3.py:25` | Cosmetic — Perwass uses e₁₃; code uses e₃₁ (sign flip only) |
| 2 | `Direction` docstring excludes E3 | `entities.py:53` | Documentation bug — E3 uses Direction for lines through origin |
| 3 | Entity type mismatch in round-trip | `create_e3.py` + `analysis_e3.py` | Line → create → Direction — inherent to E3 model, but confusing |
| 4 | `BasisE3.rotor` duplicate | `basis/e3.py:46-50` | Duplicates functionality in `create_e3.py:create_rotor` — two implementations of the same formula |

### 🔴 No Critical Issues Found

The E3 implementation is faithfully aligned with the Perwass reference text. All entity types, operator types, sign conventions, and model limitations match the definitions in GAEucSpc.tex. The code correctly restricts operations to those physically meaningful in Euclidean space (reflections and rotations about axes through the origin only) and provides clear error messages for unsupported operations.

---

## I. Answers to Specific Questions

### Q1: How is the scale in homogeneous coordinates accounted for?

**Answer:** There are no homogeneous coordinates in E3. E3 = G(3,0) is a purely Euclidean algebra with no null or projective basis vectors. All geometric entities are pure blades, and their geometric meaning (line direction, plane orientation) is invariant under uniform scaling X → λX. The code handles this by:
- Normalizing plane normals in analysis (geometric meaning is the direction, not the magnitude)
- Preserving raw lengths for Direction vectors (the magnitude carries weight/orientation information)
- Using normalized factors in rotor analysis (angle and axis are scale-invariant)

This is simpler than P3, N3, or PGA3 where the homogeneous weight must be extracted algebraically.

### Q2: Can we represent rotations about any axis in space, also those not passing through the origin?

**Answer:** No, and this is correct for E3. Perwass explicitly states (GAEucSpc.tex, p. 421):
> "In Euclidean space this confines the set of transformations to reflections and rotations about axes that pass through the origin. To extend the set of available transformations, Euclidean space has to be embedded in other spaces."

The code correctly limits rotations to axes through the origin. Rotations about arbitrary axes require P3 or N3 embedding (general rotors or motors).

---

## J. Recommendations

1. **Fix `Direction` docstring** in `entities.py` line 53: Add E3 to the supported algebras list.

2. **Consider harmonizing blade naming**: The e₃₁ vs e₁₃ difference is cosmetic, but switching to sorted-index naming (e₁₃) would match the Perwass reference. This affects the display basis, not the algebra.

3. **Consider consolidating rotor creation**: The `BasisE3.rotor()` method (line 46-50) duplicates `create_e3.py:create_rotor()`. The basis method uses `I | axis` (inner product with pseudoscalar), while create_e3 uses manual blade ID assignment. One should delegate to the other to avoid divergence.

4. **Document the Line → Direction round-trip**: The fact that `create_entity(Line(origin=0,0,0, dir=d))` → `analyze_entity()` → `Direction` is confusing. Consider either:
   - Documenting this as a known E3 limitation
   - Having `analyze_entity` return `Line` for grade-1 OPNS (with origin=(0,0,0) implicit)
   - Accepting that the `Line` dataclass is not intended for round-trip use in E3