# N3 — Conformal 3D Space — Fix Plan

Reference: `dev/todos/geo_fix/n3_entities.md`

## Design Principle

**If an entity or operator cannot be represented in a given space, raise a
`ValueError` with an explanation — do NOT silently map it to something else
or approximate it. Placeholder/stub implementations that silently produce
wrong results must be fixed to either produce the correct result or raise
`NotImplementedError` with a clear message.**

In N3 (the conformal model Cl(4,1)): **All entities and operators described by
Perwass are representable.** N3 subsumes both E3 and P3.

---

## 1. Entity Coverage Audit

### GIPNS (Inner Product Null Space)

| Entity | Grade | Perwass Formula | Code (`create_n3.py`) | Required Behaviour |
|--------|-------|-----------------|----------------------|-------------------|
| Point | 1 | A = Cop(a) | OPNS point, then `sdual()` | **OK** via dual |
| **Sphere** | 1 | **S = A - ½ ρ² e∞** | OPNS 4-point sphere, then `sdual()` | **FIX** — use direct IPNS: `Cop(center) - ½·radius²·e∞`. |
| Imaginary Sphere | 1 | S = A + ½ ρ² e∞ | **(MISSING)** | **RAISE** `NotImplementedError` (or implement). |
| **Plane** | 1 | **P = â + α e∞** | OPNS 3-point∧e∞, then `sdual()` | **FIX** — use direct IPNS: `normal + signed_distance·e∞`. |
| Line | 2 | L = P₁ ∧ P₂ | via `sdual()` | **OK** via dual |
| Circle | 2 | C = S₁ ∧ S₂ | via `sdual()` | **OK** via dual |
| Point Pair | 3 | PP = S₁ ∧ S₂ ∧ S₃ | via `sdual()` | **OK** via dual |
| Homog. Point | 3 | P₁ ∧ P₂ ∧ P₃ | via `sdual()` | **OK** via dual |
| Point | 4 | S₁∧S₂∧S₃∧S₄ | via `sdual()` | **OK** via dual |

### GOPNS (Outer Product Null Space)

| Entity | Grade | Perwass Formula | Code (`create_n3.py`) | Required Behaviour |
|--------|-------|-----------------|----------------------|-------------------|
| Point | 1 | A = Cop(a) | `create_point()` | **OK** — formula verified in ep/em basis |
| Point Pair | 2 | A ∧ B | `create_point_pair()` | **OK** |
| Homogeneous Point | 2 | A ∧ e∞ | `create_homogeneous_point()` | **OK** |
| Line | 3 | A ∧ B ∧ e∞ | `create_line()` | **OK** |
| Circle | 3 | A ∧ B ∧ C | `create_circle()` | **FIX** — ignores `normal`, only xy-plane. |
| Plane | 4 | A ∧ B ∧ C ∧ e∞ | `create_plane()` | **OK** |
| Sphere | 4 | A ∧ B ∧ C ∧ D | `create_sphere()` | **OK** |

### Findings

**Conformal point embedding verified**: The `create_point()` formula
`EP: 0.5*(r²-1), EM: 0.5*(r²+1)` expands to `Cop(x)`. ✓ Correct.

**IPNS sphere**: Must use direct `S = Cop(center) - ½·radius²·e∞`, not 4 OPNS points + dualize.

**IPNS plane**: Must use direct `P = normal + signed_distance·e∞`, not 3 OPNS points ∧ e∞ + dualize.

**Circle**: `create_circle()` ignores the `normal` parameter, constructs in xy-plane only.

---

## 2. Operator Coverage Audit

| Operator | Perwass Formula | Code (`create_n3.py`) | Required Behaviour |
|----------|-----------------|----------------------|-------------------|
| **Reflection on any plane** | P = â + α e∞ | `create_reflection()` → pure Euclidean vector | **RENAME** → `create_reflection_plane(normal, distance=0)`. Produce `normal + distance·e∞`. Any plane (not just through origin) acts as a reflection versor. |
| **Inversion** | S = A - ½ ρ² e∞ | `create_inversion()` → Cop(origin) (null point!) | **FIX** — produce `Cop(center) - ½·radius²·e∞`. |
| Rotor | R = cos(θ/2) - sin(θ/2)·N₂ | `create_rotor()` → `cos + sin·axis_bivector` | **Sign check** — same as E3/P3. |
| Translator | T = 1 - ½ t e∞ | `create_translator()` → hardcoded blade IDs | **FIX** — verify blade IDs, construct via algebra ops if possible. |
| **Dilator** | D = 1 + (1-d)/(1+d) e∞∧e₀ | `create_dilator()` → cosh/sinh, wrong sign | **FIX** — use Perwass formula directly. |
| General Dilator | T·D·T̃ | **(Not implemented)** | **RAISE** `NotImplementedError`. |
| Motor | M = T·R | `create_motor()` → T·R | **OK** functionally, but translator extraction fragile. |
| General Rotor | T·R·T̃ | **(Not implemented)** | **RAISE** `NotImplementedError`. |

### Critical Findings

**Reflection**: Current creates pure Euclidean vector (plane through origin only, α=0). Fix: rename to `create_reflection_plane(normal, distance=0)` for consistency with E3/P3 naming. Produce `normal + distance·e∞`. Any plane (not just through origin) is a valid versor — this is the key feature that enables translations and rotations about arbitrary axes in N3.

**Inversion**: Current creates Cop(origin) = **null vector** (S²=0), but an inversion sphere must be off the null cone (S²=ρ²≠0). Fix: `Cop(center) - ½·radius²·e∞`.

**Dilator sign**: Perwass `D = 1 + (1-d)/(1+d)·E`, code produces `1 + (d-1)/(d+1)·E` (opposite).

---

## 3. Analysis Fixes

### Entity Analysis — Use Perwass Formulas

| Entity | Current Method | Recommended Method |
|--------|---------------|-------------------|
| Point (grade 1) | `f_eo = -SP(point, einf)` | **OK** — correct |
| PointPair (grade 2) | Factorize, check for pure null | Perwass: `L = Q∧e∞`, `P̃ = Q·e∞`, `X = P̃·L`, `S̃ = Q·L⁻¹`, `d = 2√(S̃·S̃)` |
| HPoint (grade 2) | Factorize, check for pure null | Check `Q∧e∞ ≈ 0` |
| **Line (grade 3)** | Factorize, extract two point factors | Perwass: `d = L·(e∞∧e₀)`, `X = d·L` |
| **Circle (grade 3)** | Factorize, compute circumcenter | Perwass: `P = C∧e∞`, `C̃ = dual(C)`, `L = C̃∧e∞`, `U = dual(P)·L`, `r² = (C·C)/(P·P)` |
| **Plane (grade 4)** | Factorize, extract three points | Perwass: `P̃ = dual(P) = α(â + d e∞)`, extract â, d |
| **Sphere (grade 4)** | Factorize, solve for center | Perwass: `S̃ = dual(S) = α(A - ½r² e∞)`, extract a, r |

### Operator Analysis

| Operator | Current Issue | Fix |
|----------|--------------|-----|
| Reflection vs Inversion | `_has_eo()` only; doesn't check null cone | Add null-cone check: if `factor² ≈ 0` → point, not operator. If `factor² ≠ 0` and has e₀ → Inversion. If `factor² ≠ 0` and no e₀ → ReflectionPlane. |
| Translator | Reads only `mv[9]` (e1∧ep) | Normalize versor. Read both eᵢ∧ep and eᵢ∧em, verify consistency. |
| Dilator | `exp(sp(f1,f2))` | Use Perwass: `d = (a0 - aE)/(a0 + aE)` from `D = a0 + aE·E`. |
| GeneralDilator | Returns factor=1.0 placeholder | **RAISE** `NotImplementedError`. |

---

## 4. Implementation Checklist

### Creation Functions (create_n3.py) — High Priority 🔴

- [ ] **Add file header reference**: At top of `create_n3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Conformal Space".`

- [ ] **`create_sphere(opns)`**: Use direct IPNS formula for *both* paths: `S = center_point - 0.5 * radius² * einf` (grade‑1 vector). When `opns=True`, dualize the IPNS result (`S.sdual()` → grade‑4 OPNS sphere). When `opns=False`, return the IPNS blade directly. The IPNS formula is a one‑liner; 4‑point OPNS construction is neither simpler nor more precise.
- [ ] **`create_plane(opns)`**: Use direct IPNS formula for *both* paths: `P = normal + signed_distance * einf` (grade‑1 vector). Signed distance = `plane.point · plane.normal`. When `opns=True`, dualize the IPNS result (`P.sdual()` → grade‑4 OPNS plane). When `opns=False`, return the IPNS blade directly.
- [ ] **`create_reflection_plane(normal, distance=0)`**: Rename from old `create_reflection`. Accept `normal: Direction` and `distance: float = 0.0`. Produce grade-1 vector `normal.x·e1 + normal.y·e2 + normal.z·e3 + distance·e∞`. The plane IPNS `P = â + α e∞` acts as a versor for any α.
- [ ] **`create_inversion()`**: Accept `center: Point, radius: float = 1.0`. Produce `Cop(center) - ½·radius²·e∞` (same as IPNS sphere).
- [ ] **`create_translator()`**: Verify hardcoded blade IDs 9,17,10,18,12,20 match the actual basis enumeration. Add comment documenting mapping. If possible, construct via `t∧e∞` using algebra ops.
- [ ] **`create_dilator()`**: Fix to use Perwass formula: `D = 1 + (1-d)/(1+d)·E` where `E = e∞∧e₀`. Compute as `einf.op(eo)`.

### Creation Functions (create_n3.py) — Medium Priority 🟡

- [ ] **`create_circle()`**: Accept `normal` parameter. Construct 3 points on the circle in the plane perpendicular to normal. If too complex, raise `NotImplementedError("Circle creation with arbitrary normal not yet implemented; create 3 conformal points and wedge them directly.")` until implemented.

### Creation Functions (create_n3.py) — NotImplementedError Stubs 🟢

- [ ] **`create_imaginary_sphere()`**: Raise `NotImplementedError` or implement `Cop(center) + ½·radius²·e∞`.
- [ ] **`create_general_rotor()`**: Raise `NotImplementedError`.
- [ ] **`create_general_dilator()`**: Raise `NotImplementedError`.
- [ ] **`create_motor()`**: Verify T·R formula is correct. Add comment.
- [ ] **`create_rotor()`**: Verify sign convention (same as E3/P3). Add comment.

### Analysis Functions (analysis_n3.py) — Entity Analysis 🔴

- [ ] **Add file header reference**: At top of `analysis_n3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Conformal Space".`

- [ ] **`_plane_or_sphere_n3()` — sphere path**: Use Perwass: dualize to IPNS `S̃`, then `r² = S̃²/(S̃·e∞)²`, `a = proj_e123(S̃)/(-S̃·e∞)`.
- [ ] **`_plane_or_sphere_n3()` — plane path**: Use Perwass: `P̃ = dual(P)`, `â = proj_e123(P̃)/‖â‖`, `d = -P̃·e₀/‖â‖`, `point = -d·â`.
- [ ] **`_line_or_circle_n3()` — line path**: Use Perwass: `d = L·(e∞∧e₀)` (direction), `X = d·L` (closest point).
- [ ] **`_line_or_circle_n3()` — circle path**: Use Perwass: `P = C∧e∞`, `C̃ = dual(C)`, `L = C̃∧e∞`, `U = dual(P)·L`, `r² = (C·C)/(P·P)`.
- [ ] **`_decompose_grade2()` — HPoint path**: Check `Q∧e∞ ≈ 0`.
- [ ] **`_decompose_grade2()` — PointPair path**: Use Perwass: `L = Q∧e∞`, `P̃ = Q·e∞`, `X = P̃·L`, `S̃ = Q·L⁻¹`, `d = 2√(S̃·S̃)`.

### Analysis Functions (analysis_n3.py) — Operator Analysis 🔴

- [ ] **`_classify_single_reflector()`**: Add null-cone check: if `factor² ≈ 0` → raise (point, not operator). If `factor² ≠ 0` and no e₀ → ReflectionPlane. If `factor² ≠ 0` and has e₀ → Inversion (sphere).
- [ ] **`_translator_from_versor()`**: Normalize versor to scalar=1. Read both eᵢ∧ep and eᵢ∧em; average or verify consistency.
- [ ] **`_dilator_from_factors()`**: From versor `D = a0 + aE·E`, compute `d = (a0 - aE)/(a0 + aE)`.
- [ ] **`_general_dilator_from_factors()`**: Raise `NotImplementedError` instead of returning placeholder.
- [ ] **`_classify_double_reflector()`**: Improve by checking versor grades directly (Rotor: grades {0,2} all-Euclidean; Translator: grades {0,2} with eᵢ∞; Dilator: grades {0,2} with e∞₀).

### Dispatcher (create.py)

- [ ] Verify routing for `create_plane(opns=False)` uses new direct IPNS N3 path.
- [ ] Verify routing for `create_sphere(opns=False)` uses new direct IPNS N3 path.
- [ ] Verify routing for `create_reflection_plane` with distance parameter.
- [ ] Verify routing for `create_inversion` with center+radius parameters.
- [ ] Verify routing for `create_imaginary_sphere`, `create_general_rotor`, `create_general_dilator` raises `NotImplementedError`.

### Tests — Entity Creation

- [ ] **Test: `create_point` round-trip**: `create_entity(basis_n3, Point(1,2,3))` → analyze OPNS → `Point(1,2,3)`.
- [ ] **Test: `create_point` on null cone**: `create_entity(basis_n3, Point(1,2,3))` → mv² ≈ 0.
- [ ] **Test: `create_point` inner product**: `Cop(a)·Cop(b) = -½‖a-b‖²`. Verify with two known points.
- [ ] **Test: `create_line` OPNS round-trip**: `create_entity(basis_n3, Line(origin=Point(1,2,3), direction=Direction(1,0,0)))` → analyze OPNS → Line through (1,2,3) with direction (1,0,0).
- [ ] **Test: `create_plane` OPNS round-trip**: `create_entity(basis_n3, Plane(point=Point(1,0,0), normal=Direction(0,0,1)))` → analyze OPNS → Plane with normal (0,0,1), point on plane.
- [ ] **Test: `create_plane` IPNS round-trip**: `create_entity(basis_n3, Plane(point=Point(0,0,4), normal=Direction(0,0,1)), opns=False)` → analyze `opns=False` → Plane(normal≈(0,0,1), point on plane has z≈4).
- [ ] **Test: `create_plane` IPNS direct formula**: Verify that `normal + distance·e∞` produces the correct plane. Apply to point: point on plane → inner product ≈ 0.
- [ ] **Test: `create_sphere` OPNS round-trip**: `create_entity(basis_n3, Sphere(center=Point(0,0,0), radius=2))` → analyze OPNS → Sphere(center≈(0,0,0), radius≈2).
- [ ] **Test: `create_sphere` IPNS round-trip**: `create_entity(basis_n3, Sphere(center=Point(1,2,3), radius=2), opns=False)` → analyze `opns=False` → Sphere(center≈(1,2,3), radius≈2).
- [ ] **Test: `create_sphere` IPNS direct formula**: `S = Cop(center) - ½·radius²·e∞`. Verify `S² = radius²` and `S = -S·e∞ = 1` (normalized).
- [ ] **Test: `create_sphere` inside/outside test**: Point inside sphere → `S·X / ((S·e∞)(X·e∞)) > 0`. Point on sphere → = 0. Point outside → < 0.
- [ ] **Test: `create_circle` OPNS round-trip**: `create_entity(basis_n3, Circle(center=Point(0,0,0), normal=Direction(0,0,1), radius=2))` → analyze OPNS → Circle(center≈(0,0,0), normal≈(0,0,1), radius≈2).
- [ ] **Test: `create_circle` with arbitrary normal**: Circle with normal (1,0,0) → verify 3 points lie in plane x=const.
- [ ] **Test: `create_point_pair` round-trip**: `create_entity(basis_n3, PointPair(point_a=Point(1,0,0), point_b=Point(3,0,0)))` → analyze OPNS → PointPair with separation≈2.
- [ ] **Test: `create_homogeneous_point` round-trip**: `create_entity(basis_n3, HPoint(point=Point(1,2,3)))` → analyze OPNS → HPoint.
- [ ] **Test: `create_space` round-trip**: `create_space(basis_n3, scale=2)` → analyze OPNS → `Space(scale=2)`.
- [ ] **Test: `create_direction` round-trip**: `create_entity(basis_n3, Direction(1,0,0))` → analyze OPNS → `Direction(1,0,0)`.

### Tests — Operator Creation

- [ ] **Test: `create_reflection_plane` default (through origin)**: `create_operator(basis_n3, ReflectionPlane(normal=Direction(0,0,1)))` → grade-1 vector with e∞=0. Apply to point → reflect on z=0 plane.
- [ ] **Test: `create_reflection_plane` with distance**: `create_operator(basis_n3, ReflectionPlane(normal=Direction(0,0,1), distance=3.0))` → grade-1 vector with e∞=3. Apply to point (1,2,5) → should reflect to (1,2,1) (reflected on plane z=3).
- [ ] **Test: `create_inversion` unit sphere**: `create_operator(basis_n3, Inversion(center=Point(0,0,0), radius=1))` → S²=1. Apply to point (2,0,0) → result projects to (0.5,0,0).
- [ ] **Test: `create_inversion` round-trip**: Create → analyze → `Inversion(center≈center, radius≈radius)`.
- [ ] **Test: `create_rotor` round-trip**: `create_operator(basis_n3, Rotor(angle, axis))` → analyze → `Rotor(angle≈angle, axis≈axis)`.
- [ ] **Test: `create_rotor` application**: Apply rotor to point → verify correct rotation.
- [ ] **Test: `create_translator` round-trip**: `create_operator(basis_n3, Translator(vector=Direction(dx,dy,dz)))` → analyze → `Translator(vector≈(dx,dy,dz))`.
- [ ] **Test: `create_translator` application**: Apply translator to point (1,2,3) with vector (10,0,0) → result projects to (11,2,3).
- [ ] **Test: `create_translator` on einf**: Apply any translator to e∞ → e∞ unchanged.
- [ ] **Test: `create_translator` on eo**: Apply translator for t to e₀ → Cop(t).
- [ ] **Test: `create_dilator` round-trip**: `create_operator(basis_n3, Dilator(factor=2.0))` → analyze → `Dilator(factor≈2.0)`.
- [ ] **Test: `create_dilator` application**: Apply dilator with factor=2 to point (1,0,0) → scales to (2,0,0) (about origin).
- [ ] **Test: `create_dilator` simplest form**: `D = 1 + (1-d)/(1+d)·E`. Verify formula directly.
- [ ] **Test: `create_motor` round-trip**: `create_operator(basis_n3, Motor(rotor=Rotor(...), translator=Translator(...)))` → analyze → Motor with matching rotor and translator.
- [ ] **Test: `create_motor` application**: Apply motor (rotation + translation) to point → verify correct combined transformation.

### Tests — Exception Behaviour

- [ ] **Test: `create_imaginary_sphere` raises**: `create_entity(basis_n3, ImaginarySphere(...))` → `NotImplementedError`.
- [ ] **Test: `create_general_rotor` raises**: `create_operator(basis_n3, GeneralRotor(...))` → `NotImplementedError`.
- [ ] **Test: `create_general_dilator` raises**: `create_operator(basis_n3, GeneralDilator(...))` → `NotImplementedError`.

### Tests — Analysis Round-Trips

- [ ] **Test: round-trip all OPNS entities**: For every entity type, `analyze(create(entity, opns=True), opns=True) ≈ entity`.
- [ ] **Test: round-trip all IPNS entities**: For Sphere and Plane, `analyze(create(entity, opns=False), opns=False) ≈ entity`.
- [ ] **Test: round-trip all operators**: For every operator type, `analyze(create(operator)) ≈ operator`.
- [ ] **Test: blade → entity → blade round-trip**: For a hand-constructed blade, `create(analyze(blade)) ≈ blade` (up to scale).