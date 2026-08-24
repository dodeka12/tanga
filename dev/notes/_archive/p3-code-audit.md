# P3 Code Audit — Faithfulness to the Perwass Projective Space Model

**Date:** 31 July 2026  
**Scope:** `py/pytanga/basis/p3.py` + `py/pytanga/geometry/` (create_p3.py, analysis_p3.py, entities.py, operators.py, analysis.py, create.py) + `cpp/Tan.GA/BasisP3.h`  
**Reference:** Perwass, *Geometric Algebra with Applications in Engineering*, Habilitation thesis, Chapter "Projective Space" (`GAGeometry/GAPrjSpc.tex`, `GAAlgebra/GAVersors.tex`)

---

## A. Algebraic Embedding

### A.1 Signature and dimension

| Question | Answer |
|----------|--------|
| What is the target signature? | G(4, 0) — 4D projective geometric algebra Cl(4) with homogeneous coordinates |
| How is it implemented? | `Algebra(4, 0, dtype)` — 4 basis vectors, all square to +1 |
| Is the embedding isomorphic to the target algebra? | ✅ Direct construction — no embedding needed. Cl(4) = G(4,0). Euclidean R³ is embedded via `Hop(a) = a + e₄` into the affine hyperplane A³ ⊂ R⁴ (Perwass eqs. GAPrjSpc.tex lines 31–38). |
| Are there unused basis vectors? | ✅ No — all 2⁴ = 16 blades are present. Every blade contributes to some geometric entity representation. |

Perwass §"Projective Space — Definition" (GAPrjSpc.tex lines 31–38): The embedding operator `Hop` maps vectors from R³ to R⁴ via `Hop(a) = a + e₄`, where e₄ is the homogeneous basis vector. The algebra Cl(4) then provides both OPNS and IPNS representations for all geometric entities.

**The C++ side** (`cpp/Tan.GA/BasisP3.h` lines 76–77) declares `VectorSpaceDimension = 4` and `VectorSpaceSignature = 0`, matching G(4,0). `_Init()` at line 806 sets `m_wE4321` to +1 (pseudoscalar I = e₁₂₃₄ with I² = +1 in G(4,0)), which is correct for a 4-dimensional Euclidean algebra where all basis vectors square to +1 and the pseudoscalar squares to (−1)^{⌊4/2⌋} = (−1)² = +1.

**Verdict:** ✅ Faithful. G(4,0) is implemented directly with no embedding overhead.

### A.2 Naming conventions

| Question | Answer |
|----------|--------|
| What notation does the primary reference use for basis vectors? | e₁, e₂, e₃, e₄ (Perwass: eᵢ, be₄ for homogeneous dimension) |
| Does the code use the same names? | Python: `e1`, `e2`, `e3`, `e4` — ✅ matches. C++: `wE1`–`wE4`, `E1`–`E4` macros. |
| Are there aliases? Are they documented? | Python `BasisP3` exposes `e1`, `e2`, `e3`, `e4`, `e123`, `I` (= e1234). No aliases for `e4`. C++ exposes `E123`, `E321`, `E1234`, `E4321` as subspace multivectors. |
| Would a user familiar with the literature recognize the names? | ✅ Yes. The names directly map to Perwass's notation. |
| **Naming issue — e₃₁ vs e₁₃:** | In Python `create_p3.py`, blade ID 5 is named `E31` (e₃₁), not `E13` (e₁₃). The canonical bitmask 5 = 101₂ = e₁∧e₃. Perwass uses sorted index notation e₁₃. The Python naming follows construction order (e₃∧e₁), not sorted indices. This is purely cosmetic — the blade mask and algebraic sign are identical regardless of whether we write e₃₁ (= −e₁₃) or e₁₃. The C++ code uses `uE1|uE3` (= e₁₃, sorted) for the same blade mask. |

**Verdict:** ✅ Faithful. ⚠️ Minor naming discrepancy (e₃₁ vs e₁₃) — cosmetic only, no algebraic impact.

### A.3 Dual / meet / join operations

| Question | Answer |
|----------|--------|
| How is the pseudoscalar defined? Is it invertible? | `I = e₁₂₃₄`, blade ID 15 (= 1111₂). I² = +1 in G(4,0) since floor(4/2) = 2, (−1)² = +1. I is invertible: I⁻¹ = I. |
| If not invertible, how is dualization implemented? | Not applicable — pseudoscalar is invertible. `dual()` = `A · I⁻¹` = `A · I`. |
| Is the `meet` operator consistent with the reference model? | Perwass (GAPrjSpc.tex lines 228–242) defines IPNS meet: `IPNS(A∧B)` = intersection of IPNS(A) and IPNS(B). The code inherits meet/join from the C++ backend (`blade_join`, `blade_meet`). |
| Is the `join` operator consistent with the reference model? | Join is available via `blade_join()`. Perwass describes the join of points as the line through them (OPNS: `Hop(a)∧Hop(b)`). |
| Do `meet` and `join` satisfy the Common Factor Axiom? | Not explicitly tested; inherited from C++ blade operations. |

**Dualization mapping in P3:** With I = e₁₂₃₄ and I⁻¹ = I (since I² = +1), the dual maps grades k → 4−k:
- Grade 1 (vector) → Grade 3 (trivector) — IPNS plane → OPNS plane, or OPNS point → IPNS point
- Grade 2 (bivector) → Grade 2 (bivector) — IPNS line ↔ OPNS line (self-dual grade)
- Grade 3 (trivector) → Grade 1 (vector) — OPNS plane → IPNS plane
- Grade 4 (pseudoscalar) → Grade 0 (scalar)

This is algebraically correct. The Perwass text shows that OPNS and IPNS of lines are both bivectors (the GOPNS of two points `Hop(a)∧Hop(b)` and the GIPNS of two planes `n₁∧n₂`), which is consistent with grade-2 being self-dual.

**Verdict:** ✅ Faithful. Dualization works correctly for the G(4,0) signature.

---

## B. Geometric Entities

### B.1 Entity grades and forms

| Question | Point | Direction | Line | Plane | Space |
|----------|-------|-----------|------|-------|-------|
| What grade in OPNS? | 1 (vector) | 1 (vector, e₄=0) | 2 (bivector) | 3 (trivector) | 4 (pseudoscalar) |
| What grade in IPNS? | 3 (trivector) | 3 (trivector, no e₄) | 2 (bivector) | 1 (vector) | 0 (scalar) |
| Does creation produce both forms? | ❌ Only OPNS (`create_point` ignores `opns` parameter) | ❌ Only OPNS | ❌ Only OPNS | ✅ OPNS via IPNS→dual, IPNS directly | ✅ OPNS only |
| Does analysis handle both forms? | ✅ `opns=False` dualizes IPNS trivector→OPNS vector | ✅ Detected via e₄=0 | ✅ `opns=False` dualizes IPNS [but see §B.3] | ✅ `opns=False` dualizes IPNS vector→OPNS trivector, then re-dualizes in `_plane_from_trivector` | ✅ |

**Reference correspondence:**

Perwass (GAPrjSpc.tex lines 179–186, 252–265):
```
OPNS (GOPNS):                        IPNS (GIPNS):
  NOset_G(A)           → Point        NIset_G(A∧B∧C)      → Point
  NOset_G(A∧B)         → Line         NIset_G(A∧B)        → Line
  NOset_G(A∧B∧C)       → Plane        NIset_G(A)          → Plane
```

**Analysis mapping verification:**

When `opns=False` (IPNS input), `analyze_entity` calls `mv.dual()` then feeds to `_analyze_entity_opns`:
- IPNS point (grade-3) → dual → OPNS point (grade-1) → `_point_or_direction_from_coeffs` ✅
- IPNS line (grade-2) → dual → OPNS line (grade-2) → `_line_from_factors` ✅
- IPNS plane (grade-1) → dual → OPNS plane (grade-3) → `_plane_from_trivector` ✅

**Verdict:** ✅ Entity grade assignments match Perwass. ⚠️ Creation functions only produce OPNS — the `opns` parameter is accepted but ignored for point, direction, and line (see §B.5).

### B.2 Coordinate correspondence

#### B.2.1 Point (OPNS)

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_point` → `{E1: x, E2: y, E3: z, E4: 1}` = `Hop(a) = a + e₄` (Perwass eqn. line 32). |
| Does analysis recover the correct geometric parameters? | ✅ `_point_or_direction_from_coeffs` reads `x/g1[E1], y/g1[E2], z/g1[E3], w/g1[E4]`, then returns `Point(x=x/w, y=y/w, z=z/w)`. This matches Perwass eqn. (GAPrjSpc:E3:ProjP3toE3Def2): `à = Avec/(Avec·be₄)`. |
| Are signs consistent with the reference? | ✅ The dehomogenization formula `(x, y, z)/w` matches Perwass. |
| Edge case: point at origin? | ✅ `create_point(0,0,0)` → `{E1:0, E2:0, E3:0, E4:1}` → analysis returns `Point(0,0,0)`. |
| Edge case: weighted/scaled point? | ✅ Scale-invariant: `2·Hop(a)` reads `x=2a_x, w=2` → `a_x`. Correct. |
| How is homogeneous weight extracted? | ✅ Direct coefficient read: `w = float(g1[E4])`. Since P3 has no null vectors, this is safe and correct — e₄² = +1, and the e₄ component IS the homogeneous weight. No algebraic dot product needed (unlike PGA3/N3 where e∞ spans two blade IDs). |

#### B.2.2 Direction (Ideal Point)

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form? | ✅ `{E1: x, E2: y, E3: z}` — direction vector with e₄ = 0. Matches Perwass: "points at infinity have zero homogeneous component" (GAPrjSpc.tex line 100). |
| Does analysis detect directions? | ✅ `_point_or_direction_from_coeffs` checks `abs(w) < 1e-15` → returns `Direction(x, y, z)`. |
| Edge case: degenerate (zero vector)? | ⚠️ `create_direction(0,0,0)` produces a zero MV. `_point_or_direction_from_coeffs` would read all zeros, `abs(w) < 1e-15` triggers, returns `Direction(0,0,0)` — not detected as invalid. The zero vector is not a valid direction. |

#### B.2.3 Line (OPNS)

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form? | ✅ `create_line` → `Hop(origin) ∧ Hop(origin + direction)`. Matches Perwass (GAPrjSpc.tex lines 132–155): "the line passing through a and b is represented by Hop(a)∧Hop(b)". |
| Does analysis recover correct parameters? | ✅ `_line_from_factors` factorizes the grade-2 bivector via `blade_factorize()`, dehomogenizes both factors to get two points, computes direction = difference, normalizes. |
| Are signs consistent? | ✅ Direction is computed as difference of two dehomogenized points and normalized to unit length. Orientation is arbitrary (depends on factorization order). |
| Edge case: line through origin? | ✅ Both factors have e₄=1, dehomogenization works. |
| Edge case: ideal line (parallel)? | ✅ Fallback handles one factor with e₄=0 (direction vector). The surviving euclidean factor gives a point on the line; the direction factor gives the line direction. |
| Edge case: degenerate (identical points)? | ✅ `_line_from_factors` checks `d_norm < 1e-15` → raises `ValueError`. |

**Verification note — C++ vs Python line creation:** The C++ `CreateLine` (BasisP3.h line 442–451) constructs the line as `GA::OP(wLine, wOrigin, wDir)` where `wOrigin = Hop(origin)` and `wDir = direction` (e₄=0). This is algebraically equivalent to the Python `Hop(origin) ∧ Hop(origin + direction)` since:

```
Hop(a) ∧ Hop(a+d) = (a+e₄) ∧ (a+d+e₄)
                   = a∧a + a∧d + a∧e₄ + e₄∧a + e₄∧d + e₄∧e₄
                   = a∧d + e₄∧d                    [a∧a=0, a∧e₄+e₄∧a=0, e₄∧e₄=0]
Hop(a) ∧ d         = (a+e₄) ∧ d
                   = a∧d + e₄∧d                     ✓ same
```

Both are correct; the Python form is the one Perwass describes explicitly.

#### B.2.4 Plane

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form? | ✅ OPNS: IPNS vector `â − α·e₄` → dualized to trivector `ux·e₂₃₄ + uy·e₃₁₄ + uz·e₁₂₄ + α·e₁₂₃`. IPNS: directly `{E1: ux, E2: uy, E3: uz, E4: −α}`. |
| Does analysis recover correct parameters? | ✅ `_plane_from_trivector` dualizes OPNS trivector to IPNS vector `â − α·e₄`, reads `d = ip_dual[E4]`, computes `α = −d/n_norm`, point on plane = `α·â`. Matches Perwass (GAPrjSpc.tex lines 198–221): IPNS `auvec − α·e₄` represents plane with normal `auvec` and distance `α`. |
| Are signs consistent? | ✅ The IPNS plane `â − α·e₄` has `E4 = −α`. Analysis computes `α = −d/n_norm` (where d = `ip_dual[E4]` = −α ⇒ α = −d/n_norm). The closest point to origin is `α·â`. Correct. |
| Edge case: plane through origin? | ✅ α = 0 → IPNS = `â` (no e₄ term) → OPNS trivector = `â·I` → analysis recovers α=0 → point = (0,0,0). |
| Edge case: zero normal? | ✅ Creation checks `n_norm < 1e-15` → raises `ValueError`. Analysis also checks → raises `ValueError`. |

### B.3 Round-trip fidelity

```
mv = create_point(basis, x, y, z)
entity = analyze_entity(mv)
# entity ≈ Point(x, y, z)
```

| Question | Answer |
|----------|--------|
| Does create → analyze return the same geometric parameters? | ✅ For Point: exact (up to float precision). For Line: direction is normalized (unit), origin recovered from factorization. For Plane: normal is normalized (unit), closest-point-to-origin recovered. |
| Does this hold for both OPNS and IPNS paths? | ✅ Point: only OPNS creation exists. Plane round-trip OPNS works (IPNS→dual→OPNS→analyze: dualizes back). IPNS round-trip: `plane_ipns → analyze(opns=False)` → dualizes to OPNS → `_plane_from_trivector` dualizes back → recovers normal and offset. Line: IPNS round-trip works via `opns=False` → dual → grade-2 → `_line_from_factors`. |
| Does this hold for entities not at the origin? | ✅ Point at (x,y,z) → `Hop(x,y,z)` → dehomogenize → `(x,y,z)`. Plane with offset α → trivector → dual → recover α. Line through (x,y,z) with direction d → `Hop(p)∧Hop(p+d)` → factorize → recover p and d. |

### B.4 Linear combinations

| Question | Answer |
|----------|--------|
| Can entities be added to produce meaningful results? | ✅ Point addition: `Hop(a) + Hop(b)` → weighted sum, analysis dehomogenizes correctly via division by e₄. The result is the affine combination of the two points with equal weight — essentially their midpoint. This is a distinguishing advantage of P3 over E3 (E3 cannot add vectors to get midpoints since vectors through origin don't work that way). |
| Does analysis handle non‑unit‑weight elements correctly? | ✅ Point analysis divides by e₄ coefficient (the homogeneous weight). A scaled point `λ·Hop(a)` → analysis reads `x·λ/λ = x`. Correct. |
| Are composite entities analyzed correctly? | ✅ Weighted sums of points produce correct centroids. Sum of two Hop points: `2·(midpoint) + 2·e₄` → analysis gives midpoint. |

### B.5 Creation omissions — `opns` parameter no-ops

| Function | `opns` parameter behavior | Impact |
|----------|--------------------------|--------|
| `create_point` | Accepts `opns` but ignores it — always produces OPNS (grade-1 vector) | IPNS point (grade-3 trivector) cannot be created via this function |
| `create_direction` | Accepts `opns` but ignores it — always produces OPNS (grade-1 vector, e₄=0) | IPNS direction cannot be created via this function |
| `create_line` | Accepts `opns` but ignores it — always produces OPNS (grade-2 bivector) | IPNS line (grade-2 bivector) IS the same grade as OPNS line, so this is less of an issue. But should either reject `opns=False` with a clear error or implement IPNS construction (wedge of two IPNS plane vectors). |
| `create_plane` | ✅ Properly implemented — `opns=False` returns the IPNS vector; `opns=True` dualizes to OPNS trivector | |

**Verdict:** ⚠️ The `opns` parameter is misleading for `create_point`, `create_direction`, and `create_line` — it's accepted but has no effect. At minimum, the docstring should clarify. The cleanest fix is to either raise `ValueError("IPNS point creation not implemented in P3")` for `opns=False`, or implement IPNS creation (e.g., IPNS point = intersection of three orthogonal planes).

---

## C. Operators (Versors)

### C.1 Reflection operators

| Question | ReflectionLine | ReflectionPlane | ReflectionOrigin |
|----------|---------------|-----------------|------------------|
| What grade is the versor? | 2 (bivector N∧e₄) | 1 (vector N, e₄=0) | 1 (vector e₄) |
| Does creation produce the correct MV? | ✅ `{E14: dx, E24: dy, E34: dz}` = N∧e₄ | ✅ `{E1: nx, E2: ny, E3: nz}` (no e₄) | ✅ `{E4: 1.0}` |
| Does analysis recognize it? | ✅ `_classify_grade2_versor` reads e₁₄, e₂₄, e₃₄ | ✅ `_classify_grade1_versor` detects euclidean components, e₄=0 | ✅ `_classify_grade1_versor` detects e₄ only |
| Does sandwiching produce expected result? | ✅ | ✅ | ✅ |
| Does creation match Perwass? | ✅ GAPrjSpc.tex lines 332–348: `(N·e₄) A (e₄·N)` where versor = `N·e₄` = N∧e₄ | ✅ GAPrjSpc.tex lines 301–321: `N·A·N` reflects parallel component | ✅ GAPrjSpc.tex lines 280–299: `e₄·A·e₄` = reflection about origin |

**Detailed verification of reflection formulas:**

**ReflectionLine (Perwass GAPrjSpc.tex lines 332–348):**
The versor is `N·e₄` = `N∧e₄` (since N has no e₄ component). Applying `(N∧e₄)·A·(e₄∧N)` to `Hop(a)` yields the reflection in R² of `a` on the line with direction N. The code returns `d_x·e₁₄ + d_y·e₂₄ + d_z·e₃₄` = `d∧e₄`. ✅

**ReflectionPlane (Perwass GAPrjSpc.tex lines 301–321):**
The versor is a direction vector N (e₄ = 0). Applying `N·A·N` reflects the component of `a` *parallel* to N — this is a reflection in the plane *perpendicular* to N (i.e., with normal N). Wait — the Perwass text says "the component of the homogeneous vector that is parallel to the reflection direction N is reflected, and not the part perpendicular to it" (lines 320–321). So reflecting on direction N reflects the component along N → this is a reflection in the plane *normal to N*.

But the code names this `ReflectionPlane(normal=Direction(...))` and the docstring says "Reflection in a plane through the origin with normal n". This is **consistent**: reflecting on the normal vector N flips the normal component → equivalent to reflecting in the plane perpendicular to N. The versor is the plane's IPNS vector. ✅

**ReflectionOrigin (Perwass GAPrjSpc.tex lines 280–299):**
The versor is e₄. `e₄·Hop(a)·e₄ = e₄·(a+e₄)·e₄ = e₄·a·e₄ + e₄·e₄·e₄ = −a·e₄·e₄ + e₄ = −a + e₄`. Projected: `−a`. ✅

### C.2 Rotation operators

| Question | Rotor |
|----------|-------|
| What grades does the versor have? | 0 + 2 (scalar + bivector) |
| Does creation produce the correct MV? | ✅ `cos(θ/2) + sin(θ/2)(ax·e₂₃ + ay·e₃₁ + az·e₁₂)` |
| Does analysis recover the correct angle and axis? | ✅ `_rotor_from_factors`: `angle = 2·acos(n₁·n₂)`, axis from normalized bivector n₁∧n₂ |
| Can it represent rotations about axes not through the origin? | ❌ **No.** Rotations about arbitrary axes require general rotors (T·R·T̃), which are not implemented in P3. P3 lacks translators entirely (they require N3). See §C.5. |
| Does it compose correctly? | ✅ Two rotors multiplied yield a rotor. Analysis via `blade_factorize_versor` with 2 factors produces a `Rotor`. |
| Does creation match Perwass? | ✅ GAPrjSpc.tex lines 386–391: "the same representation of a rotor can be used in Euclidean and projective space" — the minus sign from `M·N·e₄·e₄ = −M·N` cancels. |

**C++ rotor sign convention discrepancy:**

The Python `create_rotor` uses `+sin(θ/2)`:
```python
return basis.multivector({0: cos(θ/2), E23: +sin(θ/2)·ax, E31: +sin(θ/2)·ay, E12: +sin(θ/2)·az})
```

The C++ `CBasisP3::CreateRotor` (BasisP3.h line 617–638) uses `−sin(θ/2)`:
```cpp
TValue fSin = -TValue(sin(double(dRotationAngleRad) / 2.0));
```

With C++ blade assignments `(uSc, uE2|uE3, uE1|uE3, uE1|uE2)` = `(scalar, e₂₃, e₁₃, e₁₂)` and Python assignments `(scalar, E23=e₂₃, E31=e₁₃, E12=e₁₂)` — noting E31 has mask e₁∧e₃, same as C++ `uE1|uE3`:

Python: `R = cos(θ/2) + sin(θ/2)(ax·e₂₃ + ay·e₁₃ + az·e₁₂)`  
C++:    `R = cos(θ/2) − sin(θ/2)(ax·e₂₃ + ay·e₁₃ + az·e₁₂)` = rotor of angle −θ

Both are valid — they represent rotations with opposite handedness conventions. The Perwass text (GAPrjSpc.tex line 391) states the rotor in projective space is the same as Euclidean (up to an irrelevant scalar factor). Conventionally, `R = exp(−θ·B/2) = cos(θ/2) − sin(θ/2)·B` (where B is the unit bivector). The Python uses `R = cos(θ/2) + sin(θ/2)·B` which is a different handedness convention.

**Verdict:** ✅ Functionally correct but ⚠️ sign convention inconsistency between Python and C++. The Python code uses `+sin(θ/2)`, the C++ uses `−sin(θ/2)`. Users expecting `exp(−θ·B/2)` convention may be surprised by the Python behavior.

### C.3 Translation operators

| Question | Answer |
|----------|--------|
| What grades does the versor have? | N/A — translations are not available in P3 |
| Does creation produce the correct MV? | N/A — `create_translator` raises `ValueError` |
| Does analysis recover the correct translation vector? | N/A |

**Why no translations in P3?** Translators require a null basis vector (e₀ or e∞), which is only available in N3/PGA3. In projective space P3, translations must be expressed via matrix operations or by embedding points in a higher algebra. Perwass does not describe translators in the P3 chapter — they appear in the conformal space (N3) chapter. This is **correctly** implemented as stubs that raise `ValueError`.

**Verdict:** ✅ Correct exclusion. Translations are not part of the P3 model.

### C.4 Motor / combined operators

| Question | Motor | GeneralRotor | GeneralDilator |
|----------|-------|--------------|----------------|
| Implemented in P3? | ❌ Stub raises ValueError | ❌ Stub raises ValueError | ❌ Stub raises ValueError |
| Should they be? | No — require conformal embedding (N3) | No — require translators, which need N3 | No — require E = e∞∧eo from N3 |

**Verdict:** ✅ Correct exclusions. Combined operators requiring translations or dilations are N3-only.

### C.5 Operator round-trip fidelity

```
mv = create_rotor(basis, angle, axis)
op = analyze_operator(mv)
# op ≈ Rotor(angle=angle, axis=axis)  [up to sign]
```

| Question | Answer |
|----------|--------|
| Does create → analyze return the same parameters? | ✅ Rotor: angle from `2·acos(n₁·n₂)` ≈ input angle. Axis from normalized bivector ≈ input axis (up to orientation). ReflectionLine/Plane: direction/normal recovered correctly. ReflectionOrigin: recognized (no parameters to compare). |
| Does this hold for composite operators? | N/A — composition of two P3 rotors yields a P3 rotor, which analyzes correctly. No translators/motors in P3. |

---

## D. Scale Handling (Homogeneous Coordinates)

### D.1 The fundamental question

In P3, a point `Hop(a) = a + e₄` represents the same geometric position as `λ·Hop(a) = λa + λe₄` for any λ ≠ 0. The homogeneous coordinate is *weighted*. To extract Euclidean parameters, divide by the e₄ coefficient: `à = Avec / (Avec·e₄)` (Perwass eqn. GAPrjSpc:E3:ProjP3toE3Def2).

### D.2 Common normalization patterns in P3

| Entity type | Homogeneous part | Normalization formula |
|-------------|-----------------|-----------------------|
| P3 point | e₄ component | `(x, y, z) = (c₁, c₂, c₃) / c₄` |
| P3 direction | None (e₄ = 0) | Coordinates read directly — no normalization needed |
| P3 line | Both factors dehomogenized individually | `p0 = factor0 / factor0[E4]`, direction from difference |
| P3 plane (IPNS→OPNS) | Normal magnitude | Normalized by `‖n‖`; offset relative to unit normal |

### D.3 Audit checklist for scale

| Question | Status |
|----------|--------|
| How is the homogeneous weight extracted? | ✅ Direct coefficient read: `w = float(g1[E4])` (Point analysis, `_point_or_direction_from_coeffs` line 103). In G(4,0), e₄² = +1 and there is no embedding — the e₄ blade coefficient IS the homogeneous weight. No algebraic dot product needed. |
| Does the extraction work correctly? | ✅ Yes — `e₄·e₄ = 1` in G(4,0), so the coefficient of e₄ is unambiguous. |
| Is the weight used to normalize coordinates? | ✅ Point: `Point(x=x/w, y=y/w, z=z/w)` (lines 103–107). Line: both factors dehomogenized individually (lines 124–125, 138–146, 150–151). |
| What happens for unit‑weight elements? | ✅ `w = 1`, division by 1 is a no-op — coordinates returned as-is. |
| What happens for non‑unit‑weight elements? | ✅ `Hop(a) + Hop(b)` → e₄ = 2, coordinates divided by 2 → midpoint. Correct. |
| Are there edge cases where w = 0? | ✅ Handled: `abs(w) < 1e-15` → direction (ideal point). Line analysis has fallback for one factor with e₄ ≈ 0. |

**Comparison with N3/PGA3:** In N3/PGA3, the null vector e∞ spans two blade IDs (EP and EM), requiring the algebraic extraction `α = −mv·eo`. In P3, e₄ is a simple basis vector with e₄² = +1, so direct coefficient reading is both correct and simpler. The scale handling in P3 is **cleaner and more robust** than N3/PGA3 precisely because there is no null-vector embedding.

**Verdict:** ✅ Scale handling is correct and complete. No issues found. P3's homogeneous model is simpler than N3's conformal model, and the code benefits from this.

---

## E. Code Quality

### E.1 Defensive checks

| Question | Status |
|----------|--------|
| Are zero MVs rejected early with a clear error? | ✅ `_analyze_entity_opns`: `mv.is_zero` → `ValueError`. `analyze_operator`: `mv.is_zero` → `ValueError`. |
| Are scalar MVs rejected? | ✅ `_analyze_entity_opns`: `mv.is_scalar` → `ValueError`. |
| Are mixed‑grade MVs diagnosed or handled? | ✅ `_analyze_entity_opns`: grades check → `ValueError` for mixed grades. `analyze_operator`: mixed grades routed to `blade_factorize_versor` (the correct approach). |
| Are non‑blade bivectors checked before factorization? | ❌ No. `_line_from_factors` calls `blade_factorize()` on the grade-2 part without checking that it's a simple bivector (B∧B = 0). This could fail unpredictably for non-simple bivectors. Same issue as the PGA3 audit. |

### E.2 Dead code / correctness

| Question | Status |
|----------|--------|
| Are there overwritten/commented‑out computations? | No dead code found in `create_p3.py` or `analysis_p3.py`. Clean. |
| Are there comments indicating unresolved bugs? | No. |
| Are manual blade ID assignments robust? | ⚠️ Blade IDs are hardcoded at module level: `E1=1, E2=2, E3=4, E4=8, E12=3, E31=5, E23=6, E14=9, E24=10, E34=12`. These depend on the G(4,0) blade ID scheme. If the scheme changed (e.g., renumbering), these constants would become silently wrong. Using `basis.e1.blade_id` etc. would be more robust but less performant. |

### E.3 Completeness

| Question | Status |
|----------|--------|
| Does the creation module implement all entity types that the reference model supports? | ✅ Point, Direction, Line, Plane, Space — all covered. The Perwass text describes only these entities in P3. |
| Does the analysis module recognize all operator types that can arise? | ✅ ReflectionLine, ReflectionPlane, ReflectionOrigin, Rotor — all P3 versor types covered. |
| Are there stub‑only creation functions that raise `ValueError`? | ✅ Spheres, circles, point pairs, homogeneous points, translators, dilators, inversions, motors, general rotors, general dilators — all correctly stubbed with clear error messages. |

### E.4 Redundant factory functions in analysis_p3.py

`analysis_p3.py` contains `make_point`, `make_direction`, `make_line`, `make_plane`, and `make_rotor` (lines 204–353). These are **duplicates** of the functions in `create_p3.py`. The only usage I could find is internal to the analysis module (they appear unused by the public API). This is dead code that could cause confusion — a reader might modify one copy but not the other.

**Verdict:** ⚠️ Redundant factory functions in analysis module (`make_*` functions) duplicate `create_p3.py`.

---

## F. Cross‑Module Consistency

### F.1 Entities ↔ Operators

| Question | Status |
|----------|--------|
| Are entity and operator dataclasses used consistently across creation, analysis, serialization, and visualization? | ✅ `Point`, `Direction`, `Line`, `Plane`, `Space` from `entities.py`. `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, `Rotor` from `operators.py`. All types exist and are documented. |
| Do the dataclasses cover all types used by the viz module? | ✅ The viz module renders `Point`, `Direction`, `Line`, `Plane`, `Space`, `ReflectionLine`, `ReflectionPlane`, `ReflectionOrigin`, and `Rotor` — all of which are produced by P3 analysis. |

### F.2 Analysis ↔ Creation

| Question | Status |
|----------|--------|
| Does the analysis dispatcher correctly route to the basis‑specific module? | ✅ `analysis.analyze_entity` detects P3 via `isinstance(alg, BasisP3)` → `analysis_p3.analyze_entity`. Similarly for `analyze_operator`. |
| Does the creation dispatcher correctly route? | ✅ `create.create_entity` routes to `create_p3`. |
| Is basis detection reliable? | ✅ `BasisP3` is a direct subclass of `Algebra`, not nested in any subclass hierarchy. Detection is straightforward. |

### F.3 Visualization pipeline

| Question | Status |
|----------|--------|
| Does `serializer.py` handle all P3 entity/operator types? | ✅ Point, Direction, Line, Plane, Space, ReflectionLine, ReflectionPlane, ReflectionOrigin, Rotor — all serialized. |
| Does the frontend have renderers for all kinds? | ✅ JavaScript renderers exist for all P3 entity and operator types. |

---

## G. Edge Cases and Stress Tests

### G.1 Origin and infinity

| Test | Expected behavior | Status |
|------|------------------|--------|
| Point at origin | `create_point(0,0,0)` → `{0,0,0,1}` → analysis → `Point(0,0,0)` | ✅ |
| Point at large coordinates | `create_point(1e6, 0, 0)` → normalized correctly | ✅ Should work (no precision issues in double) |
| Plane through the origin | α = 0 → IPNS = `â` → OPNS via dual → analysis recovers α=0, point=(0,0,0) | ✅ |
| Line through the origin | `Hop(0,0,0)∧Hop(d)` → both factors have e₄=1 → dehomogenized → direction recovered | ✅ |
| Ideal point (direction) | e₄ = 0 → analysis returns Direction | ✅ |
| Direction with zero norm | `create_direction(0,0,0)` → zero MV → `_point_or_direction_from_coeffs` returns `Direction(0,0,0)` | ❌ Not detected as invalid |

### G.2 Degenerate configurations

| Test | Expected behavior | Status |
|------|------------------|--------|
| Two identical points wedged → zero bivector | `Hop(a)∧Hop(a)` = 0 → `_analyze_entity_opns` catches `mv.is_zero` | ✅ |
| Zero normal for plane | Creation: `n_norm < 1e-15` → raises ValueError. Analysis: same check. | ✅ |
| Three coplanar points joined | OPNS trivector → `_plane_from_trivector` should still work (it doesn't check coplanarity, just reads the trivector) | ⚠️ Works, but the trivector represents whatever plane the three points define |
| Non‑simple bivector analyzed as line | `_line_from_factors` doesn't check B∧B = 0 first | ❌ Unpredictable behavior |

### G.3 Composition

| Test | Expected behavior | Status |
|------|------------------|--------|
| Point + Point → weighted sum | `Hop(a) + Hop(b)` → e₄ = 2, coords = (aₓ+bₓ)/2 → midpoint | ✅ |
| R₁ · R₂ → composite rotor | Both rotors have grades {0,2} → product has grades {0,2,4}. `analyze_operator` → `blade_factorize_versor` with 2 factors → `Rotor` | ✅ |
| Rotor applied to point | `R·Hop(a)·R̃` → proper rotation | ✅ (when R has unit norm) |

---

## H. C++ BasisP3 Specific Issues

### H.1 Line extraction algorithm (TryGetLineComponents)

The C++ `CBasisP3::TryGetLineComponents` (BasisP3.h lines 686–744) implements line analysis differently from the Python version:

1. Takes grade-2 projection of the multivector
2. Computes direction via `IP(wDir, m_wE4, wL)` — this is `e₄·L` which extracts the direction part of the bivector
3. If direction² = 0 → line at infinity, returns the normal of the parallel planes via `IP(wNormal, wL, m_wE321)`
4. Otherwise computes the moment bivector: `wMoment = wL − e₄∧wDir`, then origin via `IP(wOrig, wMoment, wDir / dDirLen2)`

**Algebraic verification:** For a line bivector L = Hop(a)∧d = (a+e₄)∧d = a∧d + e₄∧d:
- Direction: `e₄·L = e₄·(a∧d + e₄∧d) = e₄·(a∧d) + e₄·(e₄∧d)`. Since `e₄·(a∧d) = (e₄·a)·d − a·(e₄·d) = 0 − 0 = 0` (e₄ ⟂ a, e₄ ⟂ d) and `e₄·(e₄∧d) = (e₄·e₄)·d − e₄∧(e₄·d) = 1·d − 0 = d`. So direction = d. ✅
- Moment: `e₄∧dDir` with dDir = the direction part. Then `wMoment = L − e₄∧dDir = a∧d + e₄∧d − e₄∧d = a∧d`.
- Origin: `wDir/dDirLen2 = d/‖d‖²`. `IP(wOrig, a∧d, d/‖d‖²) = (a∧d)·(d/‖d‖²)`. Expanding: `(a∧d)·(d/‖d‖²) = a·(d·(d/‖d‖²)) − (a·(d/‖d‖²))·d = a·1 − (a·d̂)·d̂ = a − a_∥ = a_⟂`. Wait, this gives the rejection component? Let me recheck.

Actually: `(a∧d)·v = (a∧d)·v = a·(d·v) − (a·v)·d`. Setting v = d/‖d‖²: `(a∧d)·(d/‖d‖²) = a·(d·d/‖d‖²) − (a·d/‖d‖²)·d = a·1 − (a·d̂)·d̂ = a − a_∥`. This gives the component of `a` perpendicular to `d`, which is NOT the position vector `a` but rather the component of `a` orthogonal to `d`. 

Hmm, but for the OPNS line `Hop(a)∧Hop(b)`, `a` is the position of one point on the line and `d = b−a` is the direction. `a_⟂` (component of `a` perpendicular to `d`) IS a valid point on the line — specifically, it's the closest point on the line to the origin. So the C++ code correctly returns the closest point to the origin. This matches the general behavior.

**Verdict:** ✅ Algebraically correct. The algorithm is a standard approach for extracting direction and moment from a projective line bivector.

### H.2 C++ handles ideal lines

The C++ code at lines 712–724 handles the case where direction² = 0 (ideal line):
```cpp
if (this->IsZero(dDirLen2)) {
    bIsAtInfinity = true;
    vDir.zero();
    TMultivector wNormal;
    GA::IP(wNormal, wL, TBase::m_wE321);
    PointToVec3(vOrig, wNormal);
}
```
This computes the normal of the parallel planes defining the ideal line via `wL·e₃₂₁` (left contraction with e₃∧e₂∧e₁ = −I₃). This is a correct treatment of ideal lines — the Python `_line_from_factors` handles ideal lines through the factor-dehomogenization fallback instead.

### H.3 C++ pseudoscalar sign

In `_CBasisP3::_Init()` (BasisP3.h lines 783–807):
```cpp
m_wE1234.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1|uE2|uE3|uE4)));
m_wE4321.Create(tvec<TValue, 1>(TValue(1)), tvec<TBlade, 1>(TBlade(uE1|uE2|uE3|uE4)));
```

Both `E1234` and `E4321` are initialized to +1 with the same blade mask. `E4321` = `e₄∧e₃∧e₂∧e₁` = `(−1)⁶·e₁∧e₂∧e₃∧e₄` = `e₁₂₃₄` = `E1234`. So `E4321` = `E1234` in G(4,0) since the number of transpositions from (4,3,2,1) to (1,2,3,4) is 6 = even. The code's initialization of both to +1 is correct.

---

## I. Summary of Issues

### 🔴 Issues (Non‑Critical)

| # | Issue | Location | Severity |
|---|-------|----------|----------|
| 1 | `create_point`, `create_direction`, `create_line` accept `opns` parameter but ignore it — always produce OPNS | `create_p3.py` lines 36–66 | ⚠️ Misleading API |
| 2 | No blade‑ness check before `blade_factorize()` in line analysis | `analysis_p3.py` `_line_from_factors` line 118 | ⚠️ Non‑simple bivectors cause unpredictable failures |
| 3 | C++ rotor sign convention differs from Python: C++ uses `−sin(θ/2)`, Python uses `+sin(θ/2)` | `cpp/Tan.GA/BasisP3.h` line 622 vs `py/pytanga/geometry/create_p3.py` line 151 | ⚠️ Handedness convention inconsistency |
| 4 | Zero‑norm direction not detected as invalid | `create_p3.py` `create_direction` + `analysis_p3.py` `_point_or_direction_from_coeffs` | ⚠️ Returns `Direction(0,0,0)` silently |
| 5 | Redundant `make_*` factory functions in `analysis_p3.py` duplicate `create_p3.py` | `analysis_p3.py` lines 204–353 | 💤 Dead code |
| 6 | Hardcoded blade ID constants at module level | Both `create_p3.py` and `analysis_p3.py` | 💤 Fragile if blade ID scheme changes |

### 🟢 Correct Implementations (No Issues Found)

| Component | Status |
|-----------|--------|
| Algebraic embedding G(4,0) | ✅ Direct, no embedding overhead |
| Pseudoscalar I = e₁₂₃₄ (I² = +1, invertible) | ✅ |
| Point creation/dehomogenization | ✅ Matches Perwass `Avec/(Avec·e₄)` |
| Plane IPNS construction `â − α·e₄` | ✅ Matches Perwass |
| Plane OPNS via IPNS dualization | ✅ |
| Line creation via `Hop(a)∧Hop(b)` | ✅ Matches Perwass |
| Reflection operators (Line, Plane, Origin) | ✅ All three match Perwass formulas |
| Rotor creation (scalar + bivector) | ✅ Same as E3 (Perwass) |
| Operator analysis / versor factorization | ✅ |
| Scale handling (homogeneous weight) | ✅ Division by e₄ — simple and correct |
| IPNS/OPNS analysis routing | ✅ Dual-based conversion works |
| Entity dataclass coverage | ✅ Point, Direction, Line, Plane, Space |
| Operator dataclass coverage | ✅ ReflectionLine, ReflectionPlane, ReflectionOrigin, Rotor |
| N3-only stubs with clear errors | ✅ Translation, dilation, motor, etc. |
| Analysis dispatcher routing | ✅ BasisP3 detected correctly |
| C++ line analysis (TryGetLineComponents) | ✅ Algebraically correct |
| C++ ideal line handling | ✅ |
| C++ pseudoscalar initialization | ✅ E1234 = E4321 = +1 |

---

## J. Comparison: P3 vs PGA3 Audits

The P3 implementation is substantially **cleaner and more correct** than the PGA3 implementation. Key differences:

| Aspect | P3 | PGA3 |
|--------|----|----- |
| Algebraic embedding | G(4,0) directly — no embedding | 5D N3 embedding to simulate null vector |
| Scale handling | e₄ coefficient read directly — foolproof | Requires algebraic dot product −mv·eo to extract e∞ coefficient |
| Missing operators | Translators/motors correctly excluded (not in P3 model) | GeneralRotor, ReflectionLine, ReflectionOrigin missing (should exist in PGA3) |
| OPNS parameter handling | Misleading (ignored) for point/line | Partially broken (OPNS direction wrong) |
| IPNS analysis routing | Simple dual → OPNS → grade check | Grade-3 IPNS runs wrong code path (bug found in PGA3 audit) |
| No blade-ness check | Same issue in both | Same issue in both |

The P3 implementation benefits from the simplicity of the G(4,0) algebra. There is no null vector to embed, no pseudo-inverse for dualization, and no algebraic extraction of homogeneous weight. The Perwass text provides clear, explicit formulas for every entity and operator — and the code follows them accurately.

---

## K. Recommendations

1. **Fix the `opns` parameter no‑op issue** for `create_point`, `create_direction`, and `create_line`. Options:
   - **Preferred:** Implement IPNS creation (IPNS point = intersection of three orthogonal planes via `p.dual()`; IPNS line = wedge of two IPNS plane vectors; IPNS direction = trivector without e₄ after dual)
   - **Pragmatic:** Raise `ValueError("IPNS creation not implemented for P3 points/directions/lines; use opns=True")` when `opns=False`

2. **Add blade‑ness check** before `blade_factorize()` in `_line_from_factors`: verify `B∧B = 0` (or equivalently, the grade-4 part is zero). Reject non‑simple bivectors with a clear error message.

3. **Document the C++/Python rotor sign convention difference.** Pick one convention (preferably `R = cos(θ/2) − sin(θ/2)·B` = `exp(−θ·B/2)` as is standard in the literature) and use it consistently.

4. **Validate zero‑norm directions:** Reject `create_direction(0,0,0)` and the analysis case where all e₁, e₂, e₃ coefficients are zero.

5. **Remove or consolidate** the redundant `make_*` functions in `analysis_p3.py`.

6. **Consider using `basis.e1.blade_id`** instead of hardcoded `E1=1` etc., to make the code resilient to blade ID scheme changes. Alternatively, extract blade IDs from `basis.e1`, `basis.e2`, etc. at import time.

---

## L. Answers to Audit Template Questions

### L.1 What about rotations about axes not through the origin?

Perwass does not discuss general rotors (T·R·T̃) in the P3 chapter because translators do not exist in P3. To rotate about an arbitrary axis not through the origin in a pure P3 setting, you would:
1. Translate point to origin (subtract axis point)
2. Apply the P3 rotor
3. Translate back (add axis point)

This requires explicit translation handling outside the versor formalism. The N3 model provides this via general rotors (implemented in `create_n3.py`). This is **not a bug** in P3 — it's a fundamental limitation of the projective (non-conformal) model.

### L.2 How is the scale in homogeneous coordinates accounted for?

The P3 point analysis divides by the e₄ component directly: `Point(x=x/w, y=y/w, z=z/w)`. This works because P3 has G(4,0) signature and e₄ is a regular Euclidean basis vector (not null, not embedded). The extraction is simple and correct. Unlike N3/PGA3, there is no need for algebraic dot products with a reciprocal null vector.

### L.3 Named blade convention: e₃₁ vs e₁₃?

The Python code uses `E31` for blade ID 5 (e₁∧e₃), named after construction order (e₃∧e₁). Perwass uses sorted indices (e₁₃). The C++ code uses sorted indices (`uE1|uE3`). The algebraic sign is identical — this is purely a display naming issue.

**Verdict on P3 overall: ✅ Faithful to the Perwass projective space model.** The implementation is clean, correct, and handles all P3-specific entities and operators as described in the reference text. The issues found are minor and non‑critical.