# E3 — Euclidean 3D Space — Fix Plan

Reference: `dev/todos/geo_fix/e3_entities.md`

## Design Principle

**If an entity or operator cannot be represented in a given space, raise a
`ValueError` with an explanation — do NOT silently map it to something else
or approximate it.** This applies across all spaces (E3, P3, N3).

In E3:
- Points are **not representable** (all null spaces pass through the origin).
- Lines and planes **must pass through the origin**.
- Transformations are limited to reflections and rotations about axes through
  the origin.

---

## 1. Entity Coverage Audit

### Entities in Perwass vs Code

| Entity | Perwass | Code (`create_e3.py`) | Code (`analysis_e3.py`) | Required Behaviour |
|--------|---------|----------------------|------------------------|-------------------|
| Point | ❌ Not representable | `create_point()` emits grade-1 vector | maps grade-1 → Point | **RAISE** `ValueError("Points cannot be represented as null spaces in E3; use P3 or N3 for point representation.")` |
| Direction / line through origin (OPNS) | Grade 1 vector = NO_G(a) | `create_direction()` emits grade-1 vector | grade 1 mapped to Point | `create_direction()` is correct as-is. Analysis must return **Direction** (represents a line through origin), not Point. |
| Line NOT through origin (OPNS) | ❌ Not representable | – | – | **RAISE** in `create_line()` if `origin ≠ (0,0,0)`: `"In E3 only lines through the origin can be represented; use P3 or N3 for general lines."` |
| Plane through origin (OPNS) | Grade 2 bivector = NO_G(a∧b) | `create_plane()` emits bivector | grade 2 → Plane | `create_plane()` must check that `point == (0,0,0)`, otherwise **RAISE**. Analysis: grade 2 OPNS → Plane(point=(0,0,0), ...). |
| Plane NOT through origin (OPNS) | ❌ Not representable | – | – | **RAISE** `ValueError("In E3 only planes through the origin can be represented; use P3 or N3 for general planes.")` |
| Whole space (OPNS) | Grade 3 trivector | `create_space()` | grade 3 → Space | **OK** |
| Plane (IPNS) | Grade 1 vector = NI_G(n), n = dual(a∧b) | via `sdual()` of OPNS | `_analyze_entity_ipns()`: grade 1 → Plane | **OK** (IPNS path works, plane passes through origin) |
| Line (IPNS) | Grade 2 bivector = NI_G(n∧m) | via `sdual()` | `_analyze_entity_ipns()`: grade 2 → Point | **WRONG** — IPNS grade 2 is a **Line** (intersection of two planes through origin), not Point. |
| Point (IPNS) | Grade 3 trivector = NI_G(a∧b∧c) = {0} | – | – | Grade 3 IPNS dualizes to a scalar in OPNS. Should raise `ValueError` because only the trivial origin is the solution — not a meaningful point. |

### Findings

**`create_point()` in E3 is fundamentally wrong.** In E3, a 1D subspace (grade-1
blade) represents a **line through the origin** in OPNS, not a point.
Points require projective (P3) or conformal (N3) embedding.

The correct behaviour for an E3 line or plane NOT through the origin
is an exception — the caller should use P3 or N3.

`create_direction()` is correct: a free direction vector in E3 is semantically
a line through the origin in OPNS (or a plane normal in IPNS).

---

## 2. Operator Coverage Audit

### Reflection Operators in E3

Perwass gives the general blade reflection formula (equation in §"Reflection"):
```
(−1)^(k+1) B_k a B_k⁻¹ = proj_{B_k}(a) − rej_{B_k}(a)
```

In E3 (Cl(3)), this has two geometrically distinct cases:

**Line reflection (k=1, grade-1 vector d):**
```
d a d⁻¹ = a∥_d − a⊥_d
```
Component parallel to d (along the line) stays, perpendicular component flips.
→ Reflection on the **LINE** through origin with direction d.
The versor is a grade-1 **vector**.

**Plane reflection (k=2, grade-2 bivector B):**
```
(−1)^(2+1) B a B̃ = −B a B̃ = a∥_B − a⊥_B
```
Component in the plane stays, component normal to the plane flips.
→ Reflection on the **PLANE** through origin, where the plane is represented by B (OPNS) or equivalently has normal n = dual(B).
The (−1)^(k+1) = −1 factor distinguishes plane from line reflection.

Using I² = −1 in Cl(3), if n is the plane normal, then B = dual(n) = n·I⁻¹, so the plane reflection versor is a grade-2 **bivector** `n·I⁻¹ = nx·e₂₃ + ny·e₃₁ + nz·e₁₂`.

This means a single ambiguity-free `create_reflection()` cannot cover both cases. We need two functions.

| Operator | Perwass | Code (`create_e3.py`) | Required Behaviour |
|----------|---------|----------------------|-------------------|
| **Reflection on line** through origin | `d a d⁻¹` = a∥_d − a⊥_d (d = line direction) | (currently `create_reflection()` but the semantics are ambiguous) | **REPLACE with `create_reflection_line(d)`** → grade-1 **vector** d. |
| **Reflection on plane** through origin | `−B a B̃` = a∥_B − a⊥_B, where B = dual(n) is plane bivector | **MISSING** | **ADD `create_reflection_plane(n)`** → grade-2 **bivector** `n·I⁻¹` = nx·e₂₃ + ny·e₃₁ + nz·e₁₂. |
| Rotor (rotation about axis through origin) | `R = cos(θ/2) - sin(θ/2)·N₂` | `create_rotor()` → `cos(θ/2) + sin(θ/2)·axis_bivector` | **Sign check needed** — Perwass uses `- sin`, code uses `+ sin`. Verify equivalence. |
| Rotor NOT through origin | ❌ Not representable | – | **RAISE** — general rotations require N3. |
| Translator | ❌ Not representable | – | **RAISE** `ValueError("Translators require conformal embedding (N3); not available in E3.")` |
| Reflector | `refor(x,y)` | **MISSING** | Low priority — versor that reflects vector x into y. |

### Findings

**Rotor sign**: Perwass: `R = cos(θ/2) - sin(θ/2)·N₂`. Code: `R = cos(θ/2) + sin(θ/2)·axis_bivector`. In E3, N₂ (rotation plane bivector) and r (rotation axis vector) are related by r = dual(N₂) = N₂·I⁻¹ and N₂ = r·I. Since I² = −1 and I = −Ĩ, this sign difference may be equivalent. Must test: does `R x R̃` rotate x by θ about the given axis in the right-handed sense?

**Reflection ambiguity fixed**: The original `create_reflection()` produced a grade-1 vector but called it "reflection in a plane". Using the Perwass formula, a grade-1 vector d reflects on the line d (parallel stays, perpendicular flips). A grade-2 bivector B (with B = dual(n)) reflects on the plane with normal n. By providing two separate functions, the semantics are clear and match Perwass exactly.

---

## 3. Specific Fixes

### create_e3.py

| Function | Current Issue | Fix |
|----------|--------------|-----|
| `create_point()` | Returns grade-1 vector — wrong semantics for E3 | **RAISE** `ValueError("Points cannot be represented as null spaces in E3; use P3 or N3 for point representation.")` |
| `create_direction()` | Same as old `create_point()` | Keep as-is. Produces a grade-1 vector = line through origin (OPNS) or plane normal (IPNS). |
| `create_line()` | (does not exist) | **ADD**: Accept `Line(origin, direction)`. If `origin ≈ (0,0,0)`, return the direction vector (grade 1). Otherwise **RAISE**. |
| `create_plane()` | Emits bivector without checking origin | **ADD check**: If `plane.point ≠ (0,0,0)`, **RAISE**. Otherwise emit `nx·e23 + ny·e31 + nz·e12`. |
| `create_space()` | OK | No change |
| `create_rotor()` | Sign convention | Verify. Add comment documenting relation to Perwass. |
| `create_reflection()` | Ambiguous semantics | **REMOVE.** Replace with two functions below. |
| **`create_reflection_line(d)`** | (new) | Return grade-1 **vector** (components d.x, d.y, d.z at e₁, e₂, e₃). Reflects on the LINE through origin with direction d: parallel stays, perpendicular flips. |
| **`create_reflection_plane(n)`** | (new) | Return grade-2 **bivector** `n·I⁻¹` = nx·e₂₃ + ny·e₃₁ + nz·e₁₂. Reflects on the PLANE through origin with normal n: in-plane stays, normal flips. The `−1` from `(−1)^(k+1)` is built into the bivector form via I² = −1. |
| Missing stubs | N3-only entities/operators | **RAISE** `ValueError` for: `create_sphere`, `create_circle`, `create_point_pair`, `create_homogeneous_point`, `create_translator`, `create_dilator`, `create_inversion`, `create_motor`, `create_general_rotor`, `create_general_dilator`. |

### analysis_e3.py

| Function | Current Issue | Fix |
|----------|--------------|-----|
| `_analyze_entity_opns()` | Grade 1 → Point | Grade 1 → **Direction** (represents line through origin) |
| `_analyze_entity_opns()` | Grade 2 → Plane(point=(0,0,0)) | **OK** — all planes in E3 pass through origin |
| `_analyze_entity_ipns()` | Grade 1 → Plane (via dual) | **OK** |
| `_analyze_entity_ipns()` | Grade 2 → Point | Grade 2 IPNS → **Line** (intersection of two planes) |
| `_analyze_entity_ipns()` | Grade 3 → (not handled) | Raise `ValueError` (only trivial origin solution). |
| `_plane_from_bivector()` | Computes normal via dual | **OK** |
| `_rotor_from_factors()` | Extracts axis from n1∧n2 | **OK** |
| `_reflection_from_factor()` | Currently grade-1 only | **SPLIT**: grade-1 factor → `ReflectionLine`; grade-2 bivector factor (with blade factorization) → `ReflectionPlane` (extract normal via dual). |

### operators.py

| Dataclass | Issue | Fix |
|-----------|-------|-----|
| `Reflection` | Ambiguous — line or plane? | **SPLIT** into `ReflectionLine(direction: Direction)` and `ReflectionPlane(normal: Direction)`. |

### create.py (dispatcher)

| Route | Fix |
|-------|-----|
| `create_entity(basis, Point(...))` on E3 | E3 module raises `ValueError`. |
| `create_entity(basis, Line(...))` on E3 | Routes to `create_e3.create_line()`. |
| `create_entity(basis, Plane(...))` on E3 | Routes to fixed `create_e3.create_plane()`. |
| `create_entity(basis, Sphere/Circle/PointPair/HPoint)` on E3 | E3 module raises `ValueError`. |
| `create_operator(basis, ReflectionLine(...))` | Routes to `create_e3.create_reflection_line()`. |
| `create_operator(basis, ReflectionPlane(...))` | Routes to `create_e3.create_reflection_plane()`. |
| `create_operator(basis, Translator/Dilator/Inversion/Motor/...)` on E3 | E3 module raises `ValueError`. |

---

## 4. Implementation Checklist

### operators.py

- [ ] **Split `Reflection` into `ReflectionLine` and `ReflectionPlane`**: Add both dataclasses, update `Operator` union type.

### Creation Functions (create_e3.py)

- [ ] **Add file header reference**: At top of `create_e3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Euclidean Space".`
- [ ] **`create_point()`**: Raise `ValueError`.
- [ ] **`create_direction()`**: Keep as-is. Document semantics.
- [ ] **`create_line()`**: Add. If origin≈0, return direction vector. Otherwise raise.
- [ ] **`create_plane()`**: Add origin check. Raise for offset planes.
- [ ] **`create_space()`**: No change.
- [ ] **`create_rotor()`**: Verify sign convention. Add comment.
- [ ] **`create_reflection_line(direction)`**: Return grade-1 vector.
- [ ] **`create_reflection_plane(normal)`**: Return grade-2 bivector `n·I⁻¹` = nx·e₂₃ + ny·e₃₁ + nz·e₁₂.
- [ ] **Exception stubs**: `create_sphere`, `create_circle`, `create_point_pair`, `create_homogeneous_point`, `create_translator`, `create_dilator`, `create_inversion`, `create_motor`, `create_general_rotor`, `create_general_dilator` → raise `ValueError`.

### Analysis Functions (analysis_e3.py)

- [ ] **Add file header reference**: At top of `analysis_e3.py`, add comment: `# Reference: Perwass, "Geometric Algebra with Applications in Engineering", Springer 2009, Chapter "Euclidean Space".`
- [ ] **`_analyze_entity_opns()`**: Grade 1 → `Direction`, Grade 2 → `Plane(point=(0,0,0))`, Grade 3 → `Space`.
- [ ] **`_analyze_entity_ipns()`**: Grade 1 → `Plane` (via dual), Grade 2 → `Line`, Grade 3 → raise.
- [ ] **`_reflection_from_factor()`**: Grade-1 factor → `ReflectionLine`. Grade-2 bivector factor → `ReflectionPlane`.
- [ ] **`_rotor_from_factors()`**: Verify. No change.

### Dispatcher (create.py)

- [ ] Route `ReflectionLine` / `ReflectionPlane` to new E3 functions.
- [ ] Verify all N3-only stubs raise correctly.

### Tests

- [ ] **Test: `create_point` raises**: `create_entity(basis_e3, Point(1,2,3))` → `ValueError`.
- [ ] **Test: `create_line` through origin**: `create_entity(basis_e3, Line(origin=Point(0,0,0), direction=Direction(1,0,0)))` → grade-1 vector.
- [ ] **Test: `create_line` NOT through origin raises**: `create_entity(basis_e3, Line(origin=Point(1,2,3), direction=Direction(1,0,0)))` → `ValueError`.
- [ ] **Test: `create_plane` through origin**: `create_entity(basis_e3, Plane(point=Point(0,0,0), normal=Direction(0,0,1)))` → grade-2 bivector.
- [ ] **Test: `create_plane` NOT through origin raises**: `create_entity(basis_e3, Plane(point=Point(1,0,0), normal=Direction(0,0,1)))` → `ValueError`.
- [ ] **Test: N3 entities/operators raise**: All N3-only types → `ValueError`.
- [ ] **Test: `create_direction` round-trip**: create → analyze OPNS → `Direction(x,y,z)`.
- [ ] **Test: `create_space` round-trip**: create → analyze OPNS → `Space(scale)`.
- [ ] **Test: plane OPNS round-trip**: bivector → analyze OPNS → `Plane(point=(0,0,0), normal=...)`.
- [ ] **Test: plane IPNS round-trip**: vector → analyze `opns=False` → `Plane(point=(0,0,0), normal=...)`.
- [ ] **Test: IPNS line round-trip**: grade 2 (n∧m) → analyze `opns=False` → `Line` through origin.
- [ ] **Test: rotor sign convention**: `create_rotor(π/2, (0,0,1))` applied to `(1,0,0)` → `(0,1,0)`.

#### Reflection Line Tests

- [ ] **Test: `create_reflection_line` round-trip**: `create_reflection_line(e₃)` → analyze → `ReflectionLine(direction=(0,0,1))`.
- [ ] **Test: `create_reflection_line` application (e₃ direction)**: Apply to `(1,2,3)` → `(−1, −2, 3)`. Parallel z-component stays, perpendicular xy flips.
- [ ] **Test: `create_reflection_line` application (e₁ direction)**: Apply to `(1,2,3)` → `(1, −2, −3)`. Parallel x stays, perpendicular y,z flip.

#### Reflection Plane Tests

- [ ] **Test: `create_reflection_plane` round-trip**: `create_reflection_plane(normal=(0,0,1))` → analyze → `ReflectionPlane(normal=(0,0,1))`.
- [ ] **Test: `create_reflection_plane` returns bivector**: Output has grade 2 with components in e₂₃, e₃₁, e₁₂.
- [ ] **Test: `create_reflection_plane` application (normal e₃)**: Apply to `(1,2,3)` → `(1, 2, −3)`. In-plane xy stays, normal z flips.
- [ ] **Test: `create_reflection_plane` application (normal e₁)**: Apply to `(1,2,3)` → `(−1, 2, 3)`. Normal x flips, yz stays.

#### Line vs Plane Reflection Orthogonality

- [ ] **Test: line vs plane reflection are complementary**: `create_reflection_line(e₃)` reflects on z-axis (keeps z, flips xy). `create_reflection_plane(e₃)` reflects on xy-plane (flips z, keeps xy). Verify these are orthogonal operations.