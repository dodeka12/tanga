# N3 Code Audit — Conformal Geometric Algebra

**Date:** 31 July 2026
**Reference:** Perwass, *Geometric Algebra with Applications in Engineering*, Chapter "Conformal Space" (habilitation thesis, GAGeometry/GAConfSpc*.tex)
**Files audited:**
- `py/pytanga/basis/n3.py` — BasisN3
- `py/pytanga/geometry/create_n3.py` — entity/operator creation
- `py/pytanga/geometry/analysis_n3.py` — entity/operator analysis
- `py/pytanga/geometry/entities.py` — entity dataclasses
- `py/pytanga/geometry/operators.py` — operator dataclasses
- `py/pytanga/geometry/analysis.py` — top-level dispatch
- `py/pytanga/geometry/create.py` — top-level creation dispatch

---

## A. Algebraic Embedding

### A.1 Signature and dimension

| Question | Answer |
|----------|--------|
| What is the target signature? | G(4,1) — 5D algebra Cl₄,₁, matching Perwass §Conformal Space (Cl₄,₁). |
| How is it implemented? | `Algebra(5, 0b10000)` — dim=5, signature bit 4 set = negative for e₅ (=em). Basis vectors: e₁, e₂, e₃ square to +1; ep (=e₄) squares to +1; em (=e₅) squares to –1. |
| Is the embedding isomorphic to the target algebra? | ✅ Yes. The composed null basis `einf = ep+em`, `eo = ½·em − ½·ep` satisfies `einf² = eo² = 0` and `einf·eo = −1`, matching Perwass eqns in §Conformal Space exactly. |
| Are there unused basis vectors that could leak into computations? | `ep` and `em` are publicly accessible attributes (`basis.ep`, `basis.em`) but `create_n3.py` and `analysis_n3.py` never reference them directly — they always work through `einf`/`eo` or fall back to manual blade-ID construction. The `_einf()` / `_eo()` helpers use `hasattr(basis, "einf")` first, then fall back to `{8: 1.0, 16: 1.0}` / `{8: -0.5, 16: 0.5}`. Blade IDs 8 (=ep) and 16 (=em) are the raw components. No leakage threat in normal usage. |

### A.2 Naming conventions

| Question | Answer |
|----------|--------|
| What notation does the primary reference use for basis vectors? | Perwass uses **e∞** (e\_∞) for the point at infinity, **e₀** (e\_o) for the origin, and **e₁, e₂, e₃** for Euclidean basis. |
| Does the code use the same names? | Partially. The code uses `einf` (=e∞), `eo` (=e₀), `e1`, `e2`, `e3`. |
| Are there aliases? Are they documented? | `self.e0 = self.einf` (line 39 of `n3.py`). This is documented only by the comment `# conventional alias`. **⚠️ ISSUE A1:** `e0` as an alias for `einf` is semantically misleading. Perwass uses `e₀` (subscript "o" for origin) for the *origin* null vector, not the point at infinity. A user familiar with the literature would expect `e0` to mean `eo`, not `einf`. **Recommendation:** Remove `self.e0` entirely — it adds confusion with zero benefit. Code that needs the point at infinity should use `self.einf` directly. |
| Would a user familiar with the literature recognize the names? | `einf` and `eo` are clear. `e0` for `einf` would cause confusion. |

### A.3 Dual/meet/join operations

| Question | Answer |
|----------|--------|
| How is the pseudoscalar defined? Is it invertible? | `self.I = mv({self.pseudoscalar_id: 1})` where `pseudoscalar_id = 31` (all 5 bits set = e₁₂₃ₚₘ = e₁₂₃∞₀). Since the algebra has signature (4,1), I² = (−1)^(5·4/2) · det(η) = (−1)¹⁰ · (−1) = −1. Wait — let's verify: I² = e₁²e₂²e₃²·ep²·em² · (−1)^(5·4/2) = (+1)(+1)(+1)(+1)(−1) · (−1)¹⁰ = −1 · 1 = −1. So I² = −1, the pseudoscalar IS invertible (I⁻¹ = −I). ✅ |
| If not invertible, how is dualization implemented? | N/A — pseudoscalar is invertible. |
| Is the `meet` operator consistent with the reference model? | Not tested here (general MV operation). |
| Is the `join` operator consistent with the reference model? | Not tested here. |
| Do `meet` and `join` satisfy the Common Factor Axiom? | Not tested here. |

---

## B. Geometric Entities

### B.1 Entity grades and forms

| Question | Point | Direction | HPoint | PointPair | Line | Circle | Plane | Sphere | Space |
|----------|-------|-----------|--------|-----------|------|--------|-------|--------|-------|
| What grade is the entity in OPNS? | 1 | 1 | 2 | 2 | 3 | 3 | 4 | 4 | 5 |
| What grade is the entity in IPNS? | 4 (dual → point) | 4 | 3 | 3 | 2 | 2 | 1 | 1 | 0 |
| Does creation produce both forms? | ✅ `opns=True/False` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (IPNS via â+α·e∞, dualized to OPNS) | ✅ | ✅ |
| Does analysis handle both forms? | ✅ `analyze_entity(mv, opns=False)` dualizes first | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

All grades match Perwass Tables (GAConfSpc_Rep.tex, Tables for OPNS/IPNS representations). ✅

### B.2 Coordinate correspondence

#### Point

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_point` → `Cop(x) = x + ½·x²·e∞ + e₀` (Perwass eqn, GAConfSpc.tex). |
| Does analysis recover the correct geometric parameters? | ✅ `_point_or_direction_n3` normalizes by e₀ coefficient (= `−mv·e∞`), matching Perwass inverse formula: `Cop⁻¹(X) = rejection_{e∞∧e₀}(X / (−X·e∞))`. For Cop(x), `−X·e∞ = 1`, so division by f_eo correctly recovers x. |
| Are signs (orientation, distance direction) consistent with the reference convention? | ✅ |

#### Direction

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ⚠️ `create_direction` produces a pure Euclidean vector `{E1:x, E2:y, E3:z}` with no e∞/e₀ components. Perwass does not define an independent "Direction" entity in N3 — a pure Euclidean vector in Cl₄,₁ is not on the null cone (it squares to x²+y²+z² ≠ 0). It is arguably a valid GIPNS plane through the origin. The name "Direction" is pragmatic but doesn't correspond to a formal Perwass entity. |
| Does analysis recover the correct geometric parameters? | ✅ `_point_or_direction_n3` classifies by checking `eo_coeff ≈ 0` → Direction, reading Euclidean components directly. |
| Are there edge cases? | ⚠️ A point at the origin `Cop(0) = e₀` has e₀ coeff = 1 and Euclidean coeff = (0,0,0), correctly identified as Point(0,0,0). A direction with very large coordinates could falsely trigger the e₀ threshold if numerical precision degrades. |

#### Plane

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_plane` builds IPNS `P = â + α·e∞` (Perwass GAConfSpc_Rep.tex: "a plane with normal â and orthogonal distance α from the origin is represented by P = â + α·e∞"). Then dualizes to OPNS (grade 4). |
| Does analysis recover the correct geometric parameters? | ✅ `_plane_from_ipns` extracts normal from Euclidean coefficients, distance via `d = einf_c / n_norm` where `einf_c = −ipns·eo`. This matches Perwass GAConfSpc_Ana.tex §Plane: `a = proj_{e123}(*P)`, `d = −(*P·e₀)/‖a‖`. |
| Are signs consistent? | ✅ Normal is normalized to unit length. Distance sign follows the convention: positive = plane is offset in normal direction. The point on the plane is computed as `â·d`. |

#### Sphere

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_sphere` builds IPNS `S = Cop(c) − ½·r²·e∞` (Perwass eqn). Imaginary spheres use `+½·r²·e∞`. |
| Does analysis recover the correct geometric parameters? | ✅ `_sphere_from_ipns` uses the scale-invariant Perwass formulas (GAConfSpc_Ana.tex §Sphere): `r² = (S̃)²/(S̃·e∞)²`, `a = proj_{e123}(S̃)/(−S̃·e∞)`. Handles imaginary spheres via `r_sq < 0 → is_imaginary=True`. |
| Are signs consistent? | ✅ |

#### Line

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_line` → `Cop(a) ∧ Cop(b) ∧ e∞` (Perwass GAConfSpc_Rep.tex §Line OPNS). |
| Does analysis recover the correct geometric parameters? | ✅ `_decompose_line` uses Perwass formulas (GAConfSpc_Ana.tex §Line): `d = L·(e∞∧e₀)` for direction, `X = d·L` for the closest point to origin. |
| Are signs consistent? | ✅ Direction extracted from the inner product; the closest-point-to-origin is a meaningful geometric anchor. |

#### PointPair

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_point_pair` → `Cop(a) ∧ Cop(b)` (Perwass: grade-2 OPNS point pair). |
| Does analysis recover the correct geometric parameters? | ✅ `_decompose_grade2` implements the full Perwass pipeline (GAConfSpc_Ana.tex §PointPair): HPoint check (Q∧e∞ = 0), line L = Q∧e∞, bisector plane P* = Q·e∞, midpoint X = P*·L, direction from L·(e∞∧e₀), separation via S* = Q·L⁻¹ → d = 2·√|S*·S*|. Imaginary detection via S*·S* < 0. |

#### Circle

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_circle` → IPNS `S ∧ P` (sphere ∧ plane), dualized to OPNS grade 3. Matching Perwass §Circle: intersection of two spheres (or sphere + plane). |
| Does analysis recover the correct geometric parameters? | ✅ `_decompose_circle` implements Perwass GAConfSpc_Ana.tex §Circle: P = C∧e∞ (plane), C* = dual(C) (IPNS), L = C*∧e∞ (line of centres), U = P*·L (centre), S* = C·P⁻¹ (sphere), r² = S*·S*, normal from P*. |

#### Circle (edge case)

| Question | Answer |
|----------|--------|
| Circle at large coordinates? | Circle center extracted via `P_star.ip(L)` → `_factor_to_point`. The grade-2 path in `_factor_to_point` uses `p = factor.ip(eo)` to get the Euclidean part, then `s = −p·e∞` as the scale. This is algebraically sound and avoids hard-coded blade IDs. ✅ |

#### HPoint (Homogeneous Point)

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_homogeneous_point` → `Cop(a) ∧ e∞` (Perwass: A∧e∞, grade 2). |
| Does analysis recover the correct geometric parameters? | ✅ `_decompose_grade2` detects via `mv.op(einf).is_zero` → HPoint. Point extraction via `_factor_to_point`. **⚠️ ISSUE B1:** The weight parameter from creation (default 1.0) is lost in analysis — `HPoint(point=..., weight=1.0)` always has weight=1.0. The weight should be reconstructed as the overall scale of the blade. |

#### Space

| Question | Answer |
|----------|--------|
| Does creation produce the coordinate form described in the reference? | ✅ `create_space` → `scale * I` (pseudoscalar). |
| Does analysis recover the correct geometric parameters? | ✅ `_analyze_entity_opns` extracts scale via `blade_factorize_versor()`. |

#### Imaginary entities

| Question | Answer |
|----------|--------|
| Does creation produce imaginary entities? | ✅ `create_imag_point_pair` (dual of circle), `create_imag_circle` (dual of point pair). |
| Does analysis recognize imaginary entities? | ✅ `_decompose_grade2` detects imaginary point pairs via `r_sq < 0`. `_decompose_circle` detects imaginary circles via `r_sq < 0`. |
| Are imaginary entities correctly round-tripped? | ⚠️ `create_imag_point_pair` creates via `circle_opns.dual()` but returns it as OPNS or IPNS with `opns` flag. Creating an imaginary point pair OPNS → analyzing it → re-creating should work, but the created entity is `PointPair(is_imaginary=True)`. The re-creation path should use `create_point_pair` when `not is_imaginary` and `create_imag_point_pair` when `is_imaginary=True`. However, `create_entity` in `create.py` dispatches `PointPair` to `create_point_pair` unconditionally (line 101), ignoring the `is_imaginary` flag. **⚠️ ISSUE B2:** Imaginary point pairs cannot be round-tripped through `create_entity` — they are created as real point pairs instead. Same issue for imaginary circles (line 106 dispatches to `create_circle`, ignoring `is_imaginary`). |

### B.3 Round-trip fidelity

| Question | Answer |
|----------|--------|
| Does create → analyze return the same geometric parameters (up to orientation sign)? | ✅ For points, directions, lines, planes, spheres, circles, point pairs, space. |
| Does this hold for both OPNS and IPNS paths? | ✅ Both `opns=True` and `opns=False` work correctly for entities that expose the flag. |
| Does this hold for entities not at the origin? | ✅ The formulas are translation-invariant. |
| Exceptions | ❌ Imaginary entities lost in `create_entity` (ISSUE B2). ❌ HPoint weight lost in analysis (ISSUE B1). |

### B.4 Linear combinations

| Question | Answer |
|----------|--------|
| Can entities be added to produce meaningful results? | Not verified — code supports `MV + MV` but no geometry-level operations on sums are implemented. |
| Does analysis handle non-unit-weight elements correctly? | ✅ Analysis normalizes by homogeneous weight (eo coefficient for points, einf·eo for spheres, etc.). |

---

## C. Operators (Versors)

### C.1 Reflection operators

| Question | ReflPlane | ReflLine | ReflOrigin | Inversion |
|----------|-----------|----------|------------|-----------|
| What grade is the versor? | 1 | 2 (d∧e∞) | 1 (eo) | 1 (sphere IPNS) |
| Does creation produce the correct MV? | ✅ `â·e₁+â·e₂+â·e₃` (plane through origin) | ⚠️ See ISSUE C1 | ✅ `eo` | ✅ `Cop(c)−½r²·e∞` |
| Does analysis recognize it? | ✅ Grade 1, no e₀ → ReflectionPlane | ⚠️ See ISSUE C1 | ✅ Grade 1, only e₀ → ReflectionOrigin | ✅ Grade 1, e₀ present → Inversion |
| Does sandwiching produce expected result? | Not tested | Not tested | Not tested | Not tested |

**⚠️ ISSUE C1 — ReflectionLine analysis is broken.** `create_reflection_line` creates a grade-2 blade `d.op(einf)` where `d = dx·e1 + dy·e2 + dz·e3`. This is a bivector of type `dx·e1∞ + dy·e2∞ + dz·e3∞`. The analysis in `_classify_single_grade_versor` (line 482–484) attempts to extract the direction via:
```python
return ReflectionLine(
    direction=Direction(float(mv[E1]), float(mv[E2]), float(mv[E3]))
)
```
But `mv[E1]` reads the coefficient of blade ID 1 (= e₁, a grade-1 blade) from a grade-2 MV. This will always return 0. The direction should be extracted from the `eᵢ∞` bivector components instead. The correct extraction would look at the coefficients of `e₁∞`, `e₂∞`, `e₃∞` — i.e., reading `mv[E1∞]`, `mv[E2∞]`, `mv[E3∞]` (blade IDs 9+17, 10+18, 12+20, or better yet, using algebraic extraction via `_einf_coeff` / `_eo_coeff`). **As written, `analyze_operator` on a ReflectionLine MV returns `ReflLine(d=Dir(0.00, 0.00, 0.00))` — always zero direction.**

### C.2 Rotation operators

| Question | Rotor | GeneralRotor |
|----------|-------|--------------|
| What grades does the versor have? | {0,2} | {0,2} |
| Does creation produce the correct MV? | ✅ `cos(θ/2) + sin(θ/2)·(ax·e₂₃+ay·e₃₁+az·e₁₂)` (Perwass §Rotations) | ✅ `T·R·T̃` (Perwass eqn: `G = T·R·T̃`) |
| Does analysis recover the correct angle and axis? | ✅ `_rotor_from_factors` computes angle via `acos(n1·n2)` and axis from the bivector `n1∧n2`. | ✅ (extracted through factorization) |
| Can it represent rotations about axes not through the origin? | N/A (rotor at origin only) | ✅ Through GeneralRotor |
| Does it compose correctly? | Not verified | Not verified |

### C.3 Translation operators

| Question | Answer |
|----------|--------|
| What grades does the versor have? | {0,2} |
| Does creation produce the correct MV? | ✅ `T = 1 − ½·t·e∞` (Perwass eqn, GAConfSpc_Op.tex) |
| Does analysis recover the correct translation vector? | ⚠️ See ISSUE C2 |
| Does sandwiching translate points by the expected amount? | Not verified |

**⚠️ ISSUE C2 — Translator analysis uses raw blade IDs and assumes symmetry between ep/em components.** `_translator_from_versor` computes:
```python
dx = -2.0 * float(mv[9]) / scal
dy = -2.0 * float(mv[10]) / scal
dz = -2.0 * float(mv[12]) / scal
```
where blade ID 9 = ep∧e₁, 10 = ep∧e₂, 12 = ep∧e₃. The coefficient of `e₁∧e∞` is actually `mv[9] + mv[17]` (since `e∞ = ep + em`, `e₁∧e∞ = e₁∧ep + e₁∧em`). The code only reads `mv[9]`, implicitly assuming `mv[9] = mv[17]` (which holds for a correctly constructed translator `T = 1 − ½·t·e∞`, but fails for scaled or hand-assembled translators). The fix: read `mv[9] + mv[17]` instead, or better yet, use the `_einf_coeff` / `_eo_coeff` algebraic extraction. See also Section D (Scale Handling).

**⚠️ ISSUE C3 — Motor analysis extracts translator from the full motor MV incorrectly.** `_classify_quad_reflector` calls `_translator_from_versor(mv)` where `mv` is the full motor `M = T·R`. But `_translator_from_versor` assumes `mv` is a pure translator (formula `dx = −2·mv[e₁ep]/scal`). For a motor, the scalar part `cos(θ/2)` and the bivector from the rotor mix with the translator components. The extracted translation will be incorrect for non-trivial rotations.

### C.4 Motor / combined operators

| Question | Motor | GeneralRotor |
|----------|-------|--------------|
| What grades does the versor have? | {0,2,4} | {0,2} |
| Does creation produce the correct MV? | ✅ `T·R` (Perwass: M = T'·R') | ✅ `T·R·T̃` |
| Does analysis recover the components? | ⚠️ ISSUE C3 — translator part extracted from full MV | ✅ (factorized to separate rotor and translator) |
| Is the grade-4 term correctly handled? | Motor includes `e₁₂₃∞` term (= e₁₂₃∧e∞) | GeneralRotor has no grade-4 term in Perwass table ✅ |

### C.5 Dilator operators

| Question | Dilator | GeneralDilator |
|----------|---------|----------------|
| What grades does the versor have? | {0,2} | {0,2} |
| Does creation produce the correct MV? | ✅ `D = 1 + (1−d)/(1+d)·E` where `E = e∞∧e₀` (Perwass eqn) | ✅ `T·D·T̃` |
| Does analysis recover the components? | ✅ `_dilator_from_versor`: `d = (a0−aE)/(a0+aE)` | ❌ **ISSUE C4 — GeneralDilator analysis is not implemented.** `_classify_double_reflector` raises `NotImplementedError` for the `has_E and has_t` case. |

### C.6 Operator round-trip fidelity

| Question | Answer |
|----------|--------|
| Does create → analyze return the same parameters? | ✅ For Rotor, Translator, Dilator, ReflectionPlane, ReflectionOrigin, Inversion (for pure, unscaled versions). ❌ For ReflectionLine (ISSUE C1). ❌ For Motor (ISSUE C3). ❌ For GeneralDilator (ISSUE C4). |
| Does this hold for composite operators? | Partially. GeneralRotor round-trips correctly. Motor has translation extraction issues. |

---

## D. Scale Handling (Homogeneous Coordinates)

### D.1 The fundamental question

| Entity type | Homogeneous part | Normalization formula |
|-------------|-----------------|-----------------------|
| N3 point | e₀ coefficient (via `−mv·e∞`) | `(x, y, z) = (c1, c2, c3) / (−mv·e∞)` |
| N3 direction | N/A (pure Euclidean, no e∞/e₀) | `(x, y, z) = (mv[E1], mv[E2], mv[E3])` — no normalization |
| Plane (IPNS) | Normal magnitude | `d = −(ipns·e₀) / ‖â‖` |
| Sphere (IPNS) | `−S̃·e∞` | Center: `proj_{e123}(S̃) / (−S̃·e∞)`, Radius²: `(S̃)² / (S̃·e∞)²` |
| Rotor | Scalar part (for angle) | `θ = 2·acos(s)`, axis normalized |
| Translator | Scalar part | `dx = −2·mv[e₁ep] / mv[0]` |
| Dilator | `a0 + aE` denominator | `d = (a0 − aE)/(a0 + aE)` |

### D.3 Audit checklist for scale

| Question | Status |
|----------|--------|
| How is the homogeneous weight extracted? | Via algebraic dot product (`−mv·e∞`, `−mv·e₀`). Correct and basis-invariant. ✅ |
| Does the extraction work correctly in the presence of the embedding? | ✅ The `_einf_coeff` and `_eo_coeff` helpers are robust. |
| Is the weight used to normalize the Euclidean coordinates? | ✅ For points, planes, spheres. |
| What happens for unit-weight elements (the common case)? | ✅ Works correctly (e₀ coeff = 1 for normalized conformal points). |
| What happens for non-unit-weight elements (sums, interpolations)? | ⚠️ Point extraction divides by e₀ coefficient, so a sum of conformal points with weights yields the weighted centroid. Sphere and plane extraction use scale-invariant formulas — should work. |
| Does the N3 translator divide by the scalar part? | ✅ `_translator_from_versor` divides by `mv[0]`. But see ISSUE C2 — only reads blade ID 9 instead of the combined e₁∧e∞ coefficient. **⚠️ ISSUE D1:** The translator formula `dx = −2·mv[9]/scal` is numerically correct only when `mv[9] = mv[17]`. For a properly constructed translator this holds, but it's fragile. Should use `dx = −2·(mv[9] + mv[17]) / scal` or an algebraic extraction via `−(mv·(e₁∧e₀)) / mv[0]`. |
| Are there edge cases where the weight is zero (ideal elements)? | ✅ Directions have e₀ coeff = 0 and are handled (returned as Direction instead of Point). | |

---

## E. Code Quality

### E.1 Defensive checks

| Question | Status |
|----------|--------|
| Are zero MVs rejected early with a clear error? | ✅ `_analyze_entity_opns`: `if mv.is_zero: raise ValueError("Zero MV is not a geometric entity")` |
| Are scalar MVs rejected? | ✅ `_analyze_entity_opns`: `if mv.is_scalar: raise ValueError("Scalar MV is not a geometric entity")` |
| Are mixed-grade MVs diagnosed or handled? | ✅ `_analyze_entity_opns`: raises `ValueError` with grade info. |
| Are non-blade bivectors checked before factorization? | ❌ No explicit blade check before `_decompose_grade2` or `_decompose_line`. A non-simple bivector (e.g., sum of two unrelated point pairs) could produce unexpected results in the decomposition pipeline. |
| Are degenerate cases (zero normal, zero direction) handled? | ✅ `_decompose_line`: checks `if d.is_zero: raise ValueError`. ✅ `_decompose_circle`: checks for zero plane, zero line, zero normal. |

### E.2 Dead code / correctness

| Question | Status |
|----------|--------|
| Are there overwritten/commented-out computations? | ✅ No commented-out code in `create_n3.py` or `analysis_n3.py`. |
| Are there comments indicating unresolved bugs? | ✅ No "TODO" or "FIXME" comments. |
| Are manual blade ID assignments robust against blade ID scheme changes? | ⚠️ **ISSUE E1:** `_translator_from_versor` uses raw blade IDs 9, 10, 12 (ep∧e₁, ep∧e₂, ep∧e₃). `_classify_double_reflector` uses IDs 9, 10, 12, 17, 18, 20, 24. These are fragile — if the blade ID scheme changes (e.g., reordering of basis vectors in Algebra), these break silently. Should use algebraic extraction methods. |
| Are there helper functions that duplicate logic? | ⚠️ `_get_einf` and `_get_eo` exist in both `create_n3.py` and `analysis_n3.py` with identical implementations. Should be refactored to a shared location. `_einf_coeff` and `_eo_coeff` in `analysis_n3.py` duplicate the internal attributes of BasisN3. |

### E.3 Completeness

| Question | Status |
|----------|--------|
| Does the creation module implement all entity types that the reference model supports? | ✅ Point, Direction, HPoint, PointPair, Line, Circle, Plane, Sphere, Space. Also supports imaginary variants: imag_point_pair, imag_circle. |
| Does the analysis module recognize all operator types that can arise? | ✅ Rotor, Translator, Dilator, Motor, GeneralRotor, ReflectionPlane, ReflectionOrigin, Inversion. ❌ GeneralDilator raises `NotImplementedError`. ❌ ReflectionLine has extraction bug (ISSUE C1). |
| Are there stub-only creation functions that raise `ValueError` for supported entities? | ✅ No stubs — all functions are implemented. |

---

## F. Cross-Module Consistency

### F.1 Entities ↔ Operators

| Question | Status |
|----------|--------|
| Are entity and operator dataclasses used consistently across creation, analysis, serialization, and visualization? | ✅ All functions in `create_n3.py` and `analysis_n3.py` use the dataclasses from `entities.py`/`operators.py`. |
| Do the dataclasses cover all types used by the viz module? | Not verified herein (requires checking `py/pytanga/viz/`). |

### F.2 Analysis ↔ Creation

| Question | Status |
|----------|--------|
| Does the analysis dispatcher correctly route to the basis-specific module? | ✅ `_detect` checks `BasisPGA3` first (subclass), then `BasisN3`. |
| Does the creation dispatcher correctly route to the basis-specific module? | ✅ Same `_detect` logic. |
| Is the basis detection reliable? | ✅ Subclass check order is correct. |
| **⚠️ ISSUE F1:** `create_entity` dispatches `PointPair` to `create_point_pair` regardless of `is_imaginary` flag (see ISSUE B2). Same for `Circle` (line 106 — always calls `create_circle`, ignoring `is_imaginary`). | |
| **⚠️ ISSUE F2:** `create_entity` dispatches `PointPair` to `create_point_pair` even for `is_imaginary=True`. There is no dispatch path that calls `create_imag_point_pair`. | |

### F.3 Visualization pipeline

| Question | Status |
|----------|--------|
| Does `serializer.py` handle all entity/operator types that analysis can produce? | Not verified herein. |
| Does the frontend have a renderer for every kind string? | Not verified herein. |

---

## G. Edge Cases and Stress Tests

### G.1 Origin and infinity

| Test | Expected behavior | Status |
|------|------------------|--------|
| Point at origin | Cop(0) = e₀; analysis returns Point(0,0,0) | ✅ |
| Point at large coordinates | Should not suffer from numerical issues | ⚠️ Not tested; large x² could overflow in `0.5 * r_sq` |
| Entity through the origin (plane, line) | Positional term should vanish | ✅ Plane through origin: α=0, P=â. Line through origin: closest point to origin is (0,0,0). |
| Ideal/direction entity | e₀ coefficient = 0, classified as Direction | ✅ |

### G.2 Degenerate configurations

| Test | Expected behavior | Status |
|------|------------------|--------|
| Two identical points as point pair | A∧A = 0 → Zero MV rejected | ✅ |
| Parallel planes wedged in IPNS | Ideal line (e∞ — no intersection in R³) | Not tested |
| Three coplanar points → plane (OPNS) | Should produce valid plane | ✅ (three points → A∧B∧C∧e∞) |
| Non-simple bivector analyzed as point pair | Should raise error or classify as something meaningful | ❌ No blade check; could produce garbage results |

### G.3 Composition

| Test | Expected behavior | Status |
|------|------------------|--------|
| Point + Point → weighted sum | Analysis should handle non-unit weight | ✅ (e₀ coefficient handles scaling) |
| R₁ · R₂ → composite rotor | Analysis should recognize as Rotor | ✅ (two Euclidean factors → Rotor) |
| T · R → motor | Analysis should recognize as Motor | ✅ (4 factors with 2 Euclidean → Motor) |
| T · R · T̃ → general rotor | Analysis should recognize as GeneralRotor | ✅ (4 factors with <2 Euclidean → GeneralRotor) |
| ReflectionLine round-trip | Should work | ❌ ISSUE C1 |
| GeneralDilator round-trip | Should work | ❌ ISSUE C4 |

---

## Summary of Findings

### Critical Issues

| ID | Severity | Description | Location |
|----|----------|-------------|----------|
| C1 | 🔴 HIGH | ReflectionLine analysis always returns zero direction — reads grade-1 blade IDs from a grade-2 MV | `analysis_n3.py:482-484` |
| C2 | 🟡 MEDIUM | Translator analysis uses raw blade IDs (9,10,12) and assumes ep/em symmetry — fragile and could silently produce wrong results for non-canonical translators | `analysis_n3.py:540-547` |
| C4 | 🟡 MEDIUM | GeneralDilator analysis raises NotImplementedError — no round-trip possible | `analysis_n3.py:508` |
| B2 | 🟡 MEDIUM | Imaginary entities lost in create_entity dispatch — create_point_pair/Circle ignore is_imaginary flag | `create.py:101,106` |
| A1 | 🟢 LOW | `e0` alias for `einf` is semantically confusing — Perwass uses e₀ for the origin. Should be removed entirely. | `basis/n3.py:39` |

### Non-Critical Findings

| ID | Severity | Description | Location |
|----|----------|-------------|----------|
| C3 | 🟡 MEDIUM | Motor analysis extracts translator from full MV, which includes rotor contributions — translation will be incorrect for non-trivial rotations | `analysis_n3.py:517` |
| D1 | 🟡 MEDIUM | Translator scale handling assumes mv[9]=mv[17]; should use combined e₁∧e∞ coefficient | `analysis_n3.py:540-547` |
| E1 | 🟢 LOW | Raw blade ID usage (9,10,12,17,18,20,24) is fragile against blade-ID scheme changes | `analysis_n3.py:496-498,540-547,553` |
| B1 | 🟢 LOW | HPoint weight not recovered in analysis (always returns w=1.0) | `analysis_n3.py:174` |
| F1 | 🟢 LOW | Duplicated `_get_einf`/`_get_eo` in create_n3.py and analysis_n3.py | Both files |

### Recommendations

1. **Fix ReflectionLine analysis (C1):** Extract direction from eᵢ∧e∞ bivector components rather than grade-1 blade IDs.
2. **Fix Translator extraction (C2, D1, E1):** Use `−(mv·(eᵢ∧e₀)) / mv[0]` instead of raw blade ID reads. Replace all `float(mv[9])` patterns with algebraic extractions.
3. **Implement GeneralDilator analysis (C4):** Extract factor from E-component ratio and translator from eᵢ∧e∞ components.
4. **Fix Motor analysis (C3):** Factorize the motor into T·R first, then extract translator from T and rotor from R separately.
5. **Fix imaginary entity dispatch (B2, F1, F2):** In `create.py`, route `PointPair(is_imaginary=True)` to `create_imag_point_pair` and `Circle(is_imaginary=True)` to `create_imag_circle`.
6. **Remove `e0` alias (A1):** Delete `self.e0 = self.einf` from `basis/n3.py` entirely. It is misleading (Perwass uses e₀ for the origin, not e∞) and serves no purpose — code should use `self.einf` directly.
7. **Deduplicate helpers:** Move `_get_einf`, `_get_eo`, `_einf_coeff`, `_eo_coeff` to a shared `_n3_helpers.py` module.