# Plan: Update Reflection Operators & Homogeneous Entities

**Status:** draft  
**Based on:** `dev/src/test_ops_0.ipynb` — user's geometric insights about reflection operators in the conformal model  

## Key Geometric Insights

In the conformal model (N3/N2), entity blades wrapped with an `e∞` factor act as **reflection operators**
via the versor product (sandwich).  The entity and its dual (IPNS form) produce exactly the same
operator effect.

| MV form | Entity | Operator effect |
|---------|--------|-----------------|
| `d∧e∞` (d ∈ Euclidean 3D) | **HDirection** (new) | Reflection in point at infinity → maps to e∞ |
| `p∧e∞` (Cop(p)∧e∞) | **HPoint** (existing entity) | **ReflectionPoint** (reflection in point *p*) |
| `Cop(a)∧Cop(b)∧e∞` | **Line** (OPNS) | **ReflectionLine** |
| `Cop(a)∧Cop(b)∧Cop(c)∧e∞` | **Plane** (OPNS) | **ReflectionPlane** |
| Dual of any above | Same entity (IPNS) | Same operator effect |

Reflection in the origin is the special case `ReflectionPoint(Point(0,0,0))`, whose MV
is `Cop(0)∧e∞ = e₀∧e∞`.  No separate `ReflectionOrigin` type is needed.

This changes everything: reflections are no longer restricted to passing through the origin —
they can be placed anywhere in space by using the full entity blade as the operator.

---

## 0. `analyze()` Dispatch Behavior: Entity First, Operator Fallback

The `analyze()` dispatcher in `analysis.py` already implements the correct priority order:
it calls `analyze_entity()` first, and only falls back to `analyze_operator()` if entity
analysis returns `None` or raises an exception.

```
analyze(mv):
  1. try analyze_entity(mv) → if Entity, return it
  2. try analyze_operator(mv) → if Operator, return it
  3. return None
```

This means:
- A grade-3 line blade `Cop(a)∧Cop(b)∧e∞` → `analyze()` → `analyze_entity` succeeds → `Line`
- Same blade → `analyze_operator()` → `_classify_single_grade_versor` detects e∞ factor → `ReflectionLine`
- A grade-4 plane blade → `analyze()` → `analyze_entity` succeeds → `Plane`
- Same blade → `analyze_operator()` → `_classify_single_grade_versor` detects e∞ factor → `ReflectionPlane`
- A grade-2 `Cop(p)∧e∞` → `analyze()` → `analyze_entity` succeeds → `HPoint`
- Same blade → `analyze_operator()` → `_classify_single_grade_versor` → `ReflectionPoint`
- A grade-2 `d∧e∞` → `analyze()` → `analyze_entity` succeeds → `HDirection`
- Same blade → `analyze_operator()` → `_classify_single_grade_versor` → `HDirection` (as operator)

**Key implication for implementation**: The N3/N2 `analyze_operator` paths for grades 3 and 4
must NOT be reached when called from `analyze()`, because `analyze_entity` for those same blades
(grade-3 line, grade-4 plane) already succeeds and returns first.  The operator interpretation
at those grades is only reachable via explicit `analyze_operator()` calls.

For grade-2 blades (`HPoint`/`HDirection`), the entity analysis in `_decompose_grade2` succeeds,
so `analyze()` returns the entity.  Only explicit `analyze_operator()` calls interpret them as
operators (`ReflectionPoint`/`HDirection`-as-operator).

**No changes needed to `analysis.py`** — the existing entity-first dispatch is correct.

---

## 1. New Entity: `HDirection` (Homogeneous Direction)

### 1.1 Dataclass
**File:** `py/pytanga/geometry/entities.py`
- Add `@dataclass(frozen=True) class HDirection:` with field `direction: Direction`
- Add to `Entity` union type

### 1.2 Creation — N3
**File:** `py/pytanga/geometry/create_n3.py`
- Add `create_homogeneous_direction(basis, x, y, z, *, opns=True)`:
  - OPNS (default): `d∧e∞` (grade 2) where d = `{E1: x, E2: y, E3: z}`
  - IPNS: `dual()` of OPNS

### 1.3 Creation — N2
**File:** `py/pytanga/geometry/create_n2.py`
- Same as N3 but with 2D direction (E1, E2 only)

### 1.4 Analysis — N3
**File:** `py/pytanga/geometry/analysis_n3.py`
- In `_decompose_grade2()`: after the HPoint check, add HDirection check:
  - If grade-2 blade has only Euclidean components wedged with e∞ (no e₀), it's an HDirection
  - Detect via: `mv∧e∞ == 0` AND `mv·E` has zero scalar (no e₀∧e∞ component)
  - Extract direction via `mv·e₀ = -d` (same as ReflectionLine extraction)

### 1.5 Analysis — N2
**File:** `py/pytanga/geometry/analysis_n2.py`
- Same as N3 but for 2D

### 1.6 Entity dispatcher
**File:** `py/pytanga/geometry/create.py` → `create_entity()`
- Add `elif isinstance(entity, HDirection):` → `mod.create_homogeneous_direction(basis, ...)`

### 1.7 Export
**File:** `py/pytanga/geometry/__init__.py`
- Add `HDirection` to imports from `.entities` and `__all__`

---

## 2. Update Reflection Operators — Dataclasses

### 2.1 `ReflectionLine`
**File:** `py/pytanga/geometry/operators.py`

Current (wrong — origin-only):
```python
@dataclass(frozen=True)
class ReflectionLine:
    direction: Direction
```

New (full line):
```python
@dataclass(frozen=True)
class ReflectionLine:
    line: Line
```

Rationale: `Cop(p₁)∧Cop(p₂)∧e∞` is a general line and reflects across that line.
We can construct the MV directly from the `Line` entity.

### 2.2 `ReflectionPlane`
**File:** `py/pytanga/geometry/operators.py`

Current (wrong — origin-only):
```python
@dataclass(frozen=True)
class ReflectionPlane:
    normal: Direction
```

New (full plane):
```python
@dataclass(frozen=True)
class ReflectionPlane:
    plane: Plane
```

### 2.3 **Removed:** `ReflectionOrigin`
The `ReflectionOrigin` operator type is removed.  Reflection in the origin is now handled
by `ReflectionPoint(Point(0,0,0))`, whose MV is `Cop(0)∧e∞ = e₀∧e∞`.  All references to
`ReflectionOrigin` in creation, analysis, and tests are removed.

### 2.4 New operator: `ReflectionPoint`
**File:** `py/pytanga/geometry/operators.py`
- Add:
```python
@dataclass(frozen=True)
class ReflectionPoint:
    point: Point
```
- This is distinct from `HPoint` (entity). `ReflectionPoint` is the *operator* form.
- Add to `Operator` union type.

### 2.5 New operator detection: `HDirection` as operator
- `HDirection(d)` applied as operator → reflection in point at infinity → maps to e∞.
- The dataclass `HDirection` (entity) also serves as the operator type — or add a
  separate `ReflectionInfinity`?  
  **Decision:** Reuse `HDirection` entity as the operator type by adding it to the
  `Operator` union.  An `HDirection` IS the operator "reflect in point at infinity".

### 2.5 Operator union update
**File:** `py/pytanga/geometry/operators.py`
- Remove `ReflectionOrigin` from `Operator` union
- Add `ReflectionPoint` and `HDirection` (imported from entities) to `Operator` union

### 2.6 Export
**File:** `py/pytanga/geometry/__init__.py`
- Remove `ReflectionOrigin` from imports and `__all__`
- Add `ReflectionPoint` to imports and `__all__`

---

## 3. Update Reflection Operator Creation

### 3.1 N3 — `create_reflection_line`
**File:** `py/pytanga/geometry/create_n3.py`

Current: `create_reflection_line(basis, direction)` → `d∧e∞` (origin-only)

New:
```python
def create_reflection_line(basis, line: Line) -> MV:
    """Reflection in a line (not necessarily through origin).
    
    OPNS: Cop(a)∧Cop(b)∧e∞ where a, b are two points on the line.
    This is the same MV as the line entity itself.
    """
    a = _cop(basis, line.origin.x, line.origin.y, line.origin.z)
    b = _cop(basis, 
             line.origin.x + line.direction.x,
             line.origin.y + line.direction.y,
             line.origin.z + line.direction.z)
    return a.op(b).op(get_einf(basis))
```

### 3.2 N3 — `create_reflection_plane`
**File:** `py/pytanga/geometry/create_n3.py`

Current: `create_reflection_plane(basis, normal)` → `n` (Euclidean vector, origin-only)

New:
```python
def create_reflection_plane(basis, plane: Plane) -> MV:
    """Reflection in a plane (not necessarily through origin).
    
    OPNS: Cop(a)∧Cop(b)∧Cop(c)∧e∞ where a,b,c are three non-collinear points
    on the plane.  Equivalent to creating the plane entity OPNS.
    """
    # Use the plane entity creation directly
    return create_plane(basis, plane, opns=True)
```

### 3.3 **Removed:** `create_reflection_origin`
**File:** `py/pytanga/geometry/create_n3.py`
- Remove `create_reflection_origin` function.  Reflection in the origin is now
  `create_reflection_point(basis, Point(0,0,0))`.

### 3.4 N3 — `create_reflection_point` (new)
**File:** `py/pytanga/geometry/create_n3.py`

```python
def create_reflection_point(basis, point: Point) -> MV:
    """Reflection in a point.
    
    OPNS: Cop(p)∧e∞ — the HPoint blade used as a versor.
    This is identical to the OPNS HPoint entity.
    """
    return create_homogeneous_point(basis, point, weight=1.0, opns=True)
```

### 3.5 N2 equivalents
**File:** `py/pytanga/geometry/create_n2.py`
- Same changes as N3 (3.1–3.4) adapted for 2D.  Remove `create_reflection_origin`,
  add `create_reflection_point`.

### 3.6 Operator dispatcher
**File:** `py/pytanga/geometry/create.py` → `create_operator()`

Update:
```python
elif isinstance(operator, ReflectionLine):
    return mod.create_reflection_line(basis, operator.line)
elif isinstance(operator, ReflectionPlane):
    return mod.create_reflection_plane(basis, operator.plane)
elif isinstance(operator, ReflectionPoint):
    return mod.create_reflection_point(basis, operator.point)
elif isinstance(operator, HDirection):
    return mod.create_homogeneous_direction(
        basis, operator.direction.x, operator.direction.y, operator.direction.z
    )
```

---

## 4. Update Reflection Operator Analysis

### 4.0 Key Principle: Dualize High-Grade Pure Blades

When analyzing a pure blade as an operator, **the dual has the same operator effect**
(up to sign, which is irrelevant in homogeneous space):

```
G · I⁻¹ · X · I · G̃ = ± G · X · G̃
```

Therefore, for pure-grade single blades, `analyze_operator` should:
1. Versor-factorize to get the number of grade-1 factors (versor grade)
2. If versor grade ≥ 3: dualize the blade and use the dual instead (versor grade becomes `5 − v_grade`)
3. Classify at the **reduced** grade (always ≤ 2)

This eliminates the need to handle grades 3 and 4 directly in operator analysis.
The dualization step is inspired by `get_op_type()` in `dev/src/test_ops_0.ipynb`.

### 4.1 N3 operator analysis — pure blade path
**File:** `py/pytanga/geometry/analysis_n3.py` → `analyze_operator()` and helpers

Updated classification flow for **pure blades**:
```
1. Versor-factorize to get versor grade v_grade
2. If v_grade ≥ 3: op = op.dual(), v_grade = 5 − v_grade
3. Classify at reduced grade:

   v_grade == 1:
     - Has einf component (op·eo ≠ 0) → Inversion (IPNS sphere)
       Extract center & radius via existing _sphere_from_ipns / _inversion_from_blade
     - Else has Euclidean components → ReflectionPlane (IPNS plane)
       Extract plane via Euclidean normal + einf coefficient

   v_grade == 2:
     - Has E = einf∧eo component (op·E ≠ 0) → ReflectionPoint (HPoint)
       Extract point: normalize by E coefficient, extract Euclidean part
       (origin case: Cop(0)∧e∞ = e₀∧e∞ automatically handled)
     - Else has Euclidean bivector components (E12, E23, E13) → ReflectionLine (IPNS line)
       Extract direction from bivector, line origin from Euclidean part
     - Else Euclidean vector-only bivector (d∧e∞, no E, no Euclidean bivector) → HDirection
       Extract direction via op·eo = −d
```

**Concrete implementation in `_classify_single_grade_versor`:**

The dualization happens **before** grade dispatch:
```python
def _classify_single_grade_versor(mv, einf, eo):
    # Dualize high-grade blades
    v_scale, v_factors = mv.blade_factorize_versor()
    v_grade = len(v_factors)
    if v_grade >= 3:
        op = mv.dual()
        v_grade = 5 - v_grade
    else:
        op = mv

    if v_grade == 1:
        return _classify_grade1_operator(op, einf, eo)
    elif v_grade == 2:
        return _classify_grade2_operator(op, einf, eo)
    raise ValueError(...)
```

**`_classify_grade1_operator(op, einf, eo)`**:
```python
def _classify_grade1_operator(op, einf, eo):
    # Check for IPNS sphere (has einf component)
    einf_c = eo_coeff(op, einf)  # op·eo
    if abs(einf_c) > 1e-10:
        # IPNS sphere → Inversion
        return _inversion_from_ipns(op, einf, eo)
    # IPNS plane (no e₀, Euclidean normal + einf offset)
    return _plane_from_ipns_operator(op, einf, eo)
```

**`_classify_grade2_operator(op, einf, eo)`**:
```python
def _classify_grade2_operator(op, einf, eo):
    E = einf.op(eo)
    # Check for E component → ReflectionPoint
    e_scalar = op.ip(E)
    if abs(float(e_scalar[0])) > 1e-10:
        return _reflection_point_from_hpoint(op, einf, eo)
    # Check for Euclidean bivector → ReflectionLine (IPNS line)
    if _has_euclidean_bivector(op):
        return _reflection_line_from_ipns(op, einf, eo)
    # Pure d∧e∞ → HDirection
    return _hdirection_from_blade(op, einf, eo)
```

**New/extracted helper functions** (all in `analysis_n3.py`):

- `_inversion_from_ipns(op, einf, eo)` — extracts center & radius from IPNS sphere blade
  (reuse existing `_sphere_from_ipns` logic)
- `_plane_from_ipns_operator(op, einf, eo)` — extracts Plane from IPNS plane blade
  (eucl_part for normal, sp(eo) for einf coefficient → signed distance)
- `_reflection_point_from_hpoint(op, einf, eo)` — extracts Point from HPoint blade
  (E coefficient gives weight, Euclidean part gives point)
- `_reflection_line_from_ipns(op, einf, eo)` — extracts Line from IPNS line bivector
  (decompose bivector → direction + closest point to origin)
- `_hdirection_from_blade(op, einf, eo)` — extracts Direction via `op·eo = −d`
- `_has_euclidean_bivector(op)` — checks for E12/E23/E13 components

### 4.2 Multivector versor path (unchanged)
The existing 2-factor and 4-factor classification (Rotor, Translator, Dilator, Motor,
GeneralRotor) remains unchanged — these are handled by `_classify_double_reflector`
and `_classify_quad_reflector`.

### 4.3 N2 operator analysis
**File:** `py/pytanga/geometry/analysis_n2.py`
- Same dualization approach: versor grade ≥ 3 → dualize (in N2: `v_grade = 4 − v_grade` since N2 has 4 basis vectors)
- Same `_classify_grade1_operator` / `_classify_grade2_operator` structure adapted for 2D:
  - Grade 1: Inversion (circle IPNS) or ReflectionLine (line IPNS — 2D "plane" is a line)
  - Grade 2: ReflectionPoint (HPoint), ReflectionLine (IPNS line bivector), or HDirection (d∧e∞)

### 4.4 Return type annotations
Update `analyze_operator` return types:
- Remove `ReflectionOrigin`
- Add `ReflectionPoint`, `HDirection`
- `ReflectionLine` and `ReflectionPlane` remain (but now with full entity extraction)

---

## 5. Update HPoint Entity Handling

### 5.1 Entity analysis
Current: `HPoint` is already detected in `_decompose_grade2` via `mv∧e∞ == 0`.
This is correct and doesn't change.

### 5.2 Entity creation
Current: `create_homogeneous_point(basis, point, weight)` creates `Cop(p)∧e∞`.
This is correct — it produces the same MV that `create_reflection_point` would produce.
Both `HPoint` (entity) and `ReflectionPoint` (operator) are represented by the same MV.

---

## 6. Effect Validation: What Each Operator Does

### 6.1 ReflectionPoint `Cop(p)∧e∞` applied to `Cop(q)`:
- Expected: q reflected in point p → q' = 2p − q
- Sandwich: `(Cop(p)∧e∞) · Cop(q) · (Cop(p)∧e∞)̃`
- This should produce `Cop(2p − q)` (up to scale)

### 6.2 HDirection `d∧e∞` applied to `Cop(q)`:
- Expected: maps q to e∞ (infinity)
- This is reflection in a point at infinity
- q' has e₀ coefficient = 0 → ideal point

### 6.3 ReflectionLine `Cop(a)∧Cop(b)∧e∞` applied to `Cop(q)`:
- Expected: q reflected across the line through a and b
- This is the general line reflection (currently broken for off-origin lines)

### 6.4 ReflectionPlane `Cop(a)∧Cop(b)∧Cop(c)∧e∞` applied to `Cop(q)`:
- Expected: q reflected across the plane through a, b, c
- This is the general plane reflection (currently broken for off-origin planes)

### 6.5 ReflectionPoint origin case `Cop(0)∧e∞ = e₀∧e∞` applied to `Cop(q)`:
- Expected: q reflected in the origin → `Cop(−q)`
- This is the special case `ReflectionPoint(Point(0,0,0))`

---

## 6.6 Entity-as-Operator Dual Role: Tests

A key design principle: **HPoint and HDirection serve dual roles** — they are entities when
inspected via `analyze_entity`, and operators when used in a sandwich or inspected via
`analyze_operator`.  The same MV object has different interpretations depending on context.

This must be validated explicitly:

1. **HPoint entity → operator sandwich**: Create an `HPoint(p, w)` entity MV, apply the
   sandwich `hp · Cop(q) · hp̃`, and verify the result is `Cop(2p − q)` (reflection in
   point p).  Weight should normalize out.

2. **HDirection entity → operator sandwich**: Create an `HDirection(d)` entity MV, apply
   the sandwich `hd · Cop(q) · hd̃`, and verify the result is a Direction (e₀ coefficient
   = 0, mapped to infinity).

3. **`analyze_entity` vs `analyze_operator` on the same MV**:
   - `analyze_entity(Cop(p)∧e∞)` → `HPoint`
   - `analyze_operator(Cop(p)∧e∞)` → `ReflectionPoint`
   - The same MV is valid in both contexts.

4. **Operator creation produces entity-valid MVs**:
   - `create_operator(ReflectionPoint(p))` → same MV as `create_entity(HPoint(p))`
   - `create_operator(HDirection(d))` → same MV as `create_entity(HDirection(d))`

5. **Weight insensitivity of operator sandwich**: Verify that an HPoint entity with
   weight w=2.5, used as an operator, still produces the same geometric reflection
   (the weight cancels in the sandwich normalization).

---

## 7. Implementation Order

### Phase 1: New HDirection entity (no operator changes)
1. Add `HDirection` dataclass to `entities.py`
2. Add `create_homogeneous_direction` to `create_n3.py`, `create_n2.py`
3. Add HDirection detection to `analysis_n3.py` `_decompose_grade2`
4. Add HDirection detection to `analysis_n2.py` `_decompose_grade2`
5. Update `create_entity` dispatcher in `create.py` (HDirection only for N3/N2,
   raises TypeError for PGA — no stubs needed)
6. Update `__init__.py` exports (HDirection)

### Phase 2: Update operator dataclasses
7. Update `ReflectionLine` to use `Line` instead of `Direction`
8. Update `ReflectionPlane` to use `Plane` instead of `Direction`
9. Remove `ReflectionOrigin` dataclass from `operators.py` (ReflectionOrigin removed
   from exports, but **PGA3/PGA2 `create_reflection_origin`/`analyze_operator` left
   untouched** — they will break at the dispatcher level and be deferred to PGA follow-up)
10. Add `ReflectionPoint` dataclass
11. Update `Operator` union type (remove ReflectionOrigin, add ReflectionPoint, HDirection)
12. Update `__init__.py` exports (remove ReflectionOrigin, add ReflectionPoint)

### Phase 3: Update operator creation (N3/N2 only)
13. Rewrite `create_reflection_line` in `create_n3.py` / `create_n2.py`
14. Rewrite `create_reflection_plane` in `create_n3.py` / `create_n2.py`
15. Remove `create_reflection_origin` from `create_n3.py` / `create_n2.py`
16. Add `create_reflection_point` in `create_n3.py` / `create_n2.py`
17. Update `create_operator` dispatcher in `create.py`:
    - New operator types only dispatched for N3/N2 modules
    - PGA3/PGA2 modules keep their existing `create_reflection_line`/`create_reflection_plane`/
      `create_reflection_origin` functions (untouched)

### Phase 4: Update operator analysis (N3/N2 only)
18. In `analysis_n3.py`, refactor `_classify_single_grade_versor`:
    - Add dualization step: versor-factorize, if v_grade ≥ 3 → dualize (v_grade = 5 − v_grade)
    - Remove old grade-3 and grade-4 branches
    - Add `_classify_grade1_operator(op, einf, eo)` — Inversion (IPNS sphere) or ReflectionPlane
    - Add `_classify_grade2_operator(op, einf, eo)` — ReflectionPoint, ReflectionLine (IPNS line), or HDirection
    - Add helper functions:
      - `_inversion_from_ipns(op, einf, eo)` — reuse existing `_sphere_from_ipns` logic
      - `_plane_from_ipns_operator(op, einf, eo)` — normal + signed distance from IPNS plane
      - `_reflection_point_from_hpoint(op, einf, eo)` — E coefficient for weight, Euclidean part for point
      - `_reflection_line_from_ipns(op, einf, eo)` — direction + closest point from IPNS line bivector
      - `_hdirection_from_blade(op, einf, eo)` — `op·eo = −d`
      - `_has_euclidean_bivector(op)` — check for E12/E23/E13
19. In `analysis_n2.py`, same refactoring adapted for 2D:
    - Dualize when v_grade ≥ 3 (N2: v_grade = 4 − v_grade)
    - `_classify_grade1_operator`: Inversion (circle IPNS) or ReflectionLine (line IPNS)
    - `_classify_grade2_operator`: ReflectionPoint, ReflectionLine (IPNS line bivector), or HDirection
20. Update `analyze_operator` return type annotations in both files:
    - Remove `ReflectionOrigin` from return types
    - Add `ReflectionPoint`, `HDirection` to return types
21. **PGA3/PGA2 analysis files (`analysis_pga3.py`, `analysis_pga2.py`) are NOT touched.**
    They still return `ReflectionOrigin` from their `analyze_operator`, which will
    break at the top-level `Operator` type-check level.  This is explicitly deferred.

### Phase 5: Tests
22. Add N3 entity round-trip test for HDirection
23. Add N3 operator round-trip tests for updated ReflectionLine, ReflectionPlane
24. Add N3 operator round-trip test for ReflectionPoint (origin case: Point(0,0,0))
25. Add N3 **dual-role tests** (section 6.6):
    - HPoint entity MV used as operator sandwich → verifies reflection in point
    - HDirection entity MV used as operator sandwich → verifies maps to infinity
    - Same MV: `analyze_entity` returns `HPoint`, `analyze_operator` returns `ReflectionPoint`
    - Same MV: `analyze_entity` returns `HDirection`, `analyze_operator` returns `HDirection`
    - `create_operator(ReflectionPoint(p))` produces MVs valid as `HPoint` entity
    - Weight insensitivity: `HPoint(p, w=2.5)` as operator → same geometric result
26. Add N3 **application tests** for:
    - ReflectionPoint: point reflected in another point
    - ReflectionPoint origin case: point reflected in origin
    - HDirection: point mapped to infinity (result is a Direction)
    - ReflectionLine (off-origin): point reflected across a line
    - ReflectionPlane (off-origin): point reflected across a plane
27. Add N2 equivalents of all N3 tests
28. Update existing N3 tests that reference `ReflectionOrigin` (O5, A5):
    - Replace with `ReflectionPoint(Point(0,0,0))` tests
29. **Skip PGA tests** that would break due to operator dataclass changes —
    deferred to PGA follow-up plan

---

## 8. Files Affected (Summary)

| File | Changes |
|------|---------|
| `py/pytanga/geometry/entities.py` | Add `HDirection` dataclass, update `Entity` union |
| `py/pytanga/geometry/operators.py` | Update `ReflectionLine`, `ReflectionPlane`; remove `ReflectionOrigin`; add `ReflectionPoint`; update `Operator` union |
| `py/pytanga/geometry/create_n3.py` | Rewrite `create_reflection_line`, `create_reflection_plane`; remove `create_reflection_origin`; add `create_reflection_point`, `create_homogeneous_direction` |
| `py/pytanga/geometry/create_n2.py` | Same as N3 (2D) |
| `py/pytanga/geometry/analysis_n3.py` | Rewrite `_classify_single_grade_versor` with dualization; add HDirection detection; add grade1/grade2 operator classifiers |
| `py/pytanga/geometry/analysis_n2.py` | Same as N3 (2D) |
| `py/pytanga/geometry/create.py` | Update `create_entity` (HDirection, N3/N2 only) and `create_operator` dispatchers |
| `py/pytanga/geometry/__init__.py` | Remove `ReflectionOrigin`; add exports for `HDirection`, `ReflectionPoint` |
| `py/tests/geometry/test_geometry_n3_analysis.py` | Add new tests (Phase 5); update ReflectionOrigin → ReflectionPoint |
| `py/tests/geometry/test_geometry_n2_analysis.py` | Add new tests (Phase 5) |

**NOT touched in this plan:** `create_pga2.py`, `create_pga3.py`, `analysis_pga2.py`, `analysis_pga3.py` —
PGA reflection updates are fully deferred.

---

## 9. Deferred to Follow-up

- **PGA3/PGA2 reflection operator updates** (origin-only → full entity in `create_pga3.py`,
  `create_pga2.py`, `analysis_pga3.py`, `analysis_pga2.py`)
- **HDirection stub addition** to `create_pga2.py` and `create_pga3.py`
- **Removal of `ReflectionOrigin`** from PGA2/PGA3 analysis/creation
- TripleReflection handling with new reflection semantics
- Backward-compatibility aliases for the old `ReflectionLine(direction=...)` /
  `ReflectionPlane(normal=...)` / `ReflectionOrigin()` constructors
