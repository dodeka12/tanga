# Phase 10: OPNS/IPNS Duality and Homogeneous Point

**Goal:** Add OPNS/IPNS mode to entity analysis/creation, add the `HPoint`
entity (Perwass §4.3.1), and fix translator analysis for PGA3/N3.

**Reference:** Perwass thesis `GAGeometry/GAConfSpc_Rep.tex`, tables 4.3 (OPNS) and 4.4 (IPNS).

---

## 1. OPNS vs IPNS — Core Concept

| | OPNS (GOPNS) — Outer Product Null Space | IPNS (GIPNS) — Inner Product Null Space |
|---|---|---|
| **Definition** | `NOset_G(B) = {x | Cop(x) ∧ B = 0}` | `NIset_G(B) = {x | Cop(x) · B = 0}` |
| **Dual relation** | `NOset_G(B) = NIset_G(dual(B))` | `NIset_G(B) = NOset_G(dual(B))` |
| **Metric-dependent** | No — pure algebra | Yes — uses metric |
| **Current code** | OPNS throughout (implicitly) | Not implemented |

### Implementation Strategy: Dualization with `sdual()`

Since `NIset_G(B) = NOset_G(dual(B))`, IPNS analysis is equivalent to OPNS analysis
of the signed dual blade:

- **IPNS → OPNS analysis:** `analyze_entity(mv, opns=False)` applies `mv.sdual()`
  to convert to OPNS, then calls the existing OPNS analysis.
- **IPNS ← OPNS creation:** `create_entity(basis, entity, opns=False)` creates the
  OPNS blade, then applies `sdual()` again (self-inverse up to sign) to return
  the IPNS blade.

The signed dual `mv.sdual()` (backed by C++) performs a **bitwise blade-ID complement
with pre-computed sign multipliers** — it is faster than computing `mv.ip(I.inv())`
and produces identical results. No pseudoscalar access or sign calculations are needed.

**Self-inverse property:** `mv.sdual().sdual()` equals `±mv` (up to a dimension-dependent
global sign). For homogeneous representation (where scalar multiples represent the same
entity), this is sufficient for round-trip correctness.

---

## 2. Design Decisions

### 2.1 Bool Flag, Not String

```python
def analyze_entity(mv: MV, *, opns: bool = True) -> Entity:
    """opns=True → OPNS interpretation; opns=False → IPNS interpretation."""

def create_entity(basis: Algebra, entity: Entity, *, opns: bool = True) -> MV:
    """opns=True → create OPNS blade; opns=False → create IPNS blade."""
```

### 2.2 Operators Do NOT Get the OPNS Flag

Operators (Reflection, Rotor, Translator, etc.) are versors — they represent
transformations, not geometric entities in a null space. The concept of
OPNS/IPNS does not apply to operators. Functions `analyze_operator` and
`create_operator` keep their current signatures without an `opns` parameter.

**Exception:** An N3 sphere (IPNS grade-1) can be interpreted as an `Inversion`
operator via `analyze_operator`. This is a separate concept — the `analyze_operator`
function already handles this. If the user wants to analyze a sphere as an entity,
they use `analyze_entity` (returns `Sphere`). If they want to analyze it as an
operator, they use `analyze_operator` (returns `Inversion`). No mode flag needed here.

### 2.3 `HPoint` — N3-Only

A *homogeneous point* (flat point) is `A ∧ einf` in OPNS — a grade-2 blade with
basis `{e1i, e2i, e3i, E}` (4 blades). It represents a weighted point at a
finite position.

- **N3:** `HPoint` is distinct from `Point` (grade 1) and from
  `PointPair` (grade 2 with all 10 blades including `e23,e31,e12`).
- **P3:** In P3, a homogeneous point is exactly the same as a regular point
  (both are `x·e1 + y·e2 + z·e3 + w·e4`). No separate type needed.
- **PGA3:** Same as P3 — PGA3 points already carry homogeneous weight via `eo`.
  No separate type needed.

### 2.4 Inversion = Sphere in Operator Mode

A sphere blade can represent either:
- A `Sphere` entity (via `analyze_entity`) — returns `Sphere(center, radius)`
- An `Inversion` operator (via `analyze_operator`) — returns `Inversion(origin)`

This is already the behavior in our N3 analysis. In `analyze_operator`, a single
reflector factor with `eo` content is classified as `Inversion`. The entity
analysis (`analyze_entity`) always analyzes the blade as its geometric entity
type, never as an operator.

---

## 3. New Entity: `HPoint`

```python
@dataclass(frozen=True)
class HPoint:
    """A flat point — finite point with homogeneous weight (N3-only).

    OPNS representation (grade 2): ``A ∧ einf`` where A is a conformal point.
    The basis is {e1∧einf, e2∧einf, e3∧einf, eo∧einf} (4 blades).

    IPNS representation (grade 3): ``P1 ∧ P2 ∧ P3`` — intersection of three
    planes (one of which may be at infinity).

    Distinguished from:
    - ``Direction``: ideal point at infinity (no finite position, pure Euclidean vector)
    - ``Point``: single null vector on the null cone (grade 1)
    """
    point: Point       # the Euclidean position
    weight: float = 1.0  # optional weight (≥ 0)
```

**Algebra support:** N3 only.

**Updated `Entity` union:**
```python
Entity = Point | Direction | PointPair | HPoint | Line | Plane | Circle | Sphere | Space
```

---

## 4. E3 OPNS/IPNS Entity Mapping

| Grade | OPNS Entity | IPNS Entity (via sdual) |
|-------|-------------|-------------------------|
| 1 | Point | Plane (normal vector, through origin) |
| 2 | Plane (bivector) | Point (direction from origin) |
| 3 | Space | — (scalar, not an entity) |

**IPNS analysis in E3:** Apply `mv.sdual()` to convert to OPNS, run the
existing OPNS analysis, then reverse the entity-type mapping:

- OPNS returns `Point` → IPNS was a `Plane` through origin
- OPNS returns `Plane` → IPNS was a `Point` (the normal maps to the point direction)
- OPNS returns `Space` → raise `ValueError` (scalar is not a geometric entity)

**Verification** (empirically confirmed via `sdual()`):
- `v = e1` → `v.sdual() = -e23` → OPNS reads as Plane with normal e1 → IPNS plane ✓
- `b = e12` → `b.sdual() = e3` → OPNS reads as Point along e3 → IPNS point ✓

```python
def analyze_entity_e3(mv: MV, *, opns: bool = True) -> Entity:
    if opns:
        return _analyze_entity_opns_e3(mv)
    else:
        dual = mv.sdual()
        opns_entity = _analyze_entity_opns_e3(dual)
        if isinstance(opns_entity, Point):
            return Plane(point=Point(0,0,0),
                        normal=Direction(opns_entity.x, opns_entity.y, opns_entity.z))
        elif isinstance(opns_entity, Plane):
            return Point(x=opns_entity.normal.x,
                        y=opns_entity.normal.y, z=opns_entity.normal.z)
        elif isinstance(opns_entity, Space):
            raise ValueError("IPNS of pseudoscalar is scalar — not a geometric entity")
```

---

## 5. HPoint Detection in OPNS (N3)

A grade-2 blade in N3 OPNS can be either:
- **PointPair**: has ALL 10 grade-2 basis elements possibly non-zero, including
  Euclidean bivectors `e23, e31, e12` (blade IDs 6, 5, 3)
- **HPoint**: only has the 4 basis elements `{e1i, e2i, e3i, E}` where
  `e1i = e1∧einf` covers blades `{e1p, e1m}` = `{9, 17}`,
  `e2i = e2∧einf` = `{10, 18}`,
  `e3i = e3∧einf` = `{12, 20}`,
  `E = einf∧eo` = blade `24`

**Detection algorithm:**
1. Check if any Euclidean bivector (blade IDs 3, 5, 6) is non-zero.
   If YES → PointPair.
   If NO → HPoint.

**After factorization:** If there are 2 factor vectors, check:
- If both factors are conformal points (have both Euclidean and null components) → PointPair
- If one factor is `einf` (pure null) and the other is a conformal point → HPoint

The factorization approach: a HPoint blade `A ∧ einf` factorizes into
two vectors: `A` (conformal point) and `einf` (pure null). A PointPair factorizes
into two conformal point vectors. Check if one factor is pure null → HPoint.

**In IPNS:** The IPNS representation of a HPoint is a grade-3 blade
`P1 ∧ P2 ∧ P3` (intersection of 3 planes). Via dualization, this becomes
`dual(P1∧P2∧P3) = A ∧ einf` in OPNS — a HPoint. So the IPNS detection
works automatically via dualization.

---

## 6. Translator Analysis Fix (PGA3 and N3)

### Problem

The current `_translator_from_factors` function in both `analysis_pga3.py` and
`analysis_n3.py` sums the Euclidean components of the factor vectors:

```python
def _translator_from_factors(factors):
    dx = sum(float(f[E1]) for f in factors)
    dy = sum(float(f[E2]) for f in factors)
    dz = sum(float(f[E3]) for f in factors)
    return Translator(vector=Direction(dx, dy, dz))
```

This is **not correct**. The versor factorization of a translator `T = 1 - 0.5·t·einf`
typically produces two reflector factors that are not simply related to the
translation vector components by summation.

### Correct Approach

Read the translator components directly from the versor's bivector coefficients,
matching the C++ `CreateTranslator()` construction:

```
T = 1 - 0.5·(dx·e1i + dy·e2i + dz·e3i)
```

where `e1i = e1∧einf = e1∧ep + e1∧em` (blades 9 and 17),
`e2i = e2∧einf` (blades 10 and 18),
`e3i = e3∧einf` (blades 12 and 20).

**Extraction:**
```
dx = -2 * coeff(e1i)     # e1i ≈ coeff[9] or coeff[17] (take the ep component)
dy = -2 * coeff(e2i)     # e2i ≈ coeff[10] or coeff[18]
dz = -2 * coeff(e3i)     # e3i ≈ coeff[12] or coeff[20]
```

Since each `e∧einf` blade is split across `ep` and `em` (both with the same
coefficient in the translator), we can read either the `ep` or `em` component:

```python
def _translator_from_versor(mv: MV) -> Translator:
    """Extract translator directly from versor coefficients."""
    # e1⊲einf components (blades 9=e1p, 17=e1m)
    dx = -2.0 * float(mv[9])
    dy = -2.0 * float(mv[10])
    dz = -2.0 * float(mv[12])
    return Translator(vector=Direction(dx, dy, dz))
```

This replaces the factor-based approach for translators. The factor count is
still used for classification (2 factors with einf → Translator), but the
actual parameters are extracted from the versor coefficients.

**Motor analysis** can then combine:
- Rotor from 2 Euclidean factors → `_rotor_from_factors`
- Translator from versor coefficients → `_translator_from_versor`

---

## 7. Entity × Algebra Coverage (Updated)

| Entity | E3 | P3 | PGA3 | N3 | Notes |
|--------|:--:|:--:|:----:|:--:|-------|
| Point | ✓ | ✓ | ✓ | ✓ | |
| Direction | — | ✓ | ✓ | ✓ | |
| HPoint | — | — | — | ✓ | N3-only |
| PointPair | — | — | — | ✓ | |
| Line | — | ✓ | ✓ | ✓ | |
| Circle | — | — | — | ✓ | |
| Plane | ✓ | ✓ | ✓ | ✓ | |
| Sphere | — | — | — | ✓ | |
| Space | ✓ | ✓ | ✓ | ✓ | |

---

## 8. IPNS Entity Detection by Algebra

### E3 IPNS

| Grade | IPNS Entity | Implementation |
|-------|-------------|----------------|
| 1 | Plane (through origin, normal = vector) | Dualize to grade 2, OPNS → Plane |
| 2 | Point (direction perpendicular to bivector) | Dualize to grade 1, OPNS → Point |
| 3 | Scalar → raise ValueError | |

### P3 IPNS

P3 uses homogeneous coordinates. The IPNS/OPNS dualization works similarly.
Via dualization to OPNS and then using existing OPNS analysis. No new entity
types for IPNS — the dualization maps to existing OPNS types.

### PGA3 IPNS

Same as N3 for the sub-algebra with only `einf` (no `eo`). Via dualization to
OPNS. HPoint is NOT returned (PGA3 point = homogeneous point).

### N3 IPNS

Via dualization to OPNS. The IPNS entity mapping is:

| IPNS Grade | Dualized OPNS Grade | Entity |
|------------|---------------------|--------|
| 1 (has eo, coeff_ep ≠ coeff_em) | 4 | Sphere |
| 1 (no eo, coeff_ep = coeff_em) | 4 (no e123o) | Plane |
| 2 (has eo bivectors) | 3 (has e123) | Circle |
| 2 (no eo bivectors) | 3 (no e123) | Line |
| 3 (has e123) | 2 (has Euclidean bivectors) | PointPair |
| 3 (no e123) | 2 (no Euclidean bivectors, 4-blade basis) | HPoint |
| 4 | 1 | Point |

The dualization approach handles all of this automatically — we don't need to
re-implement the IPNS classification. We just dualize and call the OPNS analyzer.

---

## 9. Files to Modify

| File | Changes |
|------|---------|
| `entities.py` | Add `HPoint`, update `Entity` union |
| `analysis.py` | Add `*, opns: bool = True` to `analyze_entity` and `analyze`; remove from `analyze_operator` |
| `analysis_e3.py` | Add `opns` flag; IPNS path via dualization with entity-type remapping |
| `analysis_p3.py` | Add `opns` flag; IPNS path via dualization |
| `analysis_pga3.py` | Add `opns` flag; IPNS via dualization; HPoint NOT returned (falls through to PointPair analysis); fix `_translator_from_factors` → `_translator_from_versor` |
| `analysis_n3.py` | Add `opns` flag; IPNS via dualization; HPoint detection in `_decompose_grade2_opns`; fix translator extraction |
| `create.py` | Add `*, opns: bool = True` to `create_entity` and `create`; remove from `create_operator` |
| `create_e3.py` | Add `opns` flag functions; IPNS creation via OPNS+sdual |
| `create_p3.py` | Add `opns` flag; IPNS creation via OPNS+sdual |
| `create_pga3.py` | Add `opns` flag; IPNS creation via OPNS+sdual |
| `create_n3.py` | Add `opns` flag; IPNS creation via OPNS+sdual; add `create_homogeneous_point` |
| `__init__.py` | Re-export `HPoint` |
| `docs/py/geometry/entities.md` | Add `HPoint` documentation |
| `docs/py/geometry/analysis.md` | Add OPNS/IPNS mode documentation |
| `docs/py/geometry/create.md` | Add OPNS/IPNS mode documentation |

### Files NOT Modified

| File | Reason |
|------|--------|
| `operators.py` | No changes — `HPoint` is an entity, not an operator |
| `py/pytanga/__init__.py` | `HPoint` re-exported via `pytanga.geometry` which is already imported |

---

## 10. Function Signature Changes (Summary)

### Analysis

```python
# analysis.py
def analyze_entity(mv: MV, *, opns: bool = True) -> Entity: ...
def analyze_operator(mv: MV) -> Operator: ...  # NO opns flag
def analyze(mv: MV, *, opns: bool = True) -> Entity | Operator: ...

# analysis_e3.py / _p3.py / _pga3.py / _n3.py
def analyze_entity(mv: MV, *, opns: bool = True) -> Entity: ...
def analyze_operator(mv: MV) -> Operator: ...  # NO opns flag
```

### Creation

```python
# create.py
def create_entity(basis: Algebra, entity: Entity, *, opns: bool = True) -> MV: ...
def create_operator(basis: Algebra, operator: Operator) -> MV: ...  # NO opns flag
def create(basis: Algebra, obj: Entity | Operator, *, opns: bool = True) -> MV: ...

# create_e3.py / _p3.py / _pga3.py / _n3.py
def create_point(basis, x, y, z, *, opns: bool = True) -> MV: ...
# ... same for all entity creation functions
def create_homogeneous_point(basis, point, weight=1.0, *, opns: bool = True) -> MV: ...  # N3 only
# Operator functions: NO opns flag
```

---

## 11. HPoint OPNS/IPNS in N3

### OPNS Creation

```python
def create_homogeneous_point(basis, point, weight=1.0):
    """OPNS: A ∧ einf where A = Cop(point)."""
    a = create_point(basis, point.x, point.y, point.z)  # conformal point
    einf = _get_einf(basis)
    return a.op(einf) * weight
```

The result has 4 non-zero blades: `e1p, e2p, e3p, ep*em` (blades 9, 10, 12, 24)
and the corresponding `em` counterparts (17, 18, 20).

### IPNS Creation

For IPNS, create in OPNS and apply `sdual()`:
```python
def create_homogeneous_point(basis, point, weight=1.0, *, opns=True):
    mv = _create_homogeneous_point_opns(basis, point, weight)
    if not opns:
        mv = mv.sdual()
    return mv
```

All entity creation functions in `create_n3.py` (and analogously in other
`create_*.py` modules) follow the same pattern: build the OPNS blade, then
apply `sdual()` when `opns=False`. This avoids duplicating the construction
logic for IPNS and guarantees correctness via the dual relation.

### OPNS Analysis (Detection)

```python
def _decompose_grade2_opns(mv: MV) -> PointPair | HPoint:
    """Grade 2 in OPNS → PointPair or HPoint."""
    grade2 = mv.grade(2)
    factors = grade2.blade_factorize()
    # Check if either factor is pure einf (no Euclidean, only null)
    null_only = []
    for f in factors:
        if _has_null(f) and not _has_euclidean(f):
            null_only.append(f)
    if len(null_only) == 1:
        # One factor is pure einf → HPoint
        point_factors = [f for f in factors if f is not null_only[0]]
        p = _factor_to_point_n3(point_factors[0], mv.algebra)
        return HPoint(point=p)
    else:
        # Both factors are points → PointPair
        p1 = _factor_to_point_n3(factors[0], mv.algebra)
        p2 = _factor_to_point_n3(factors[1], mv.algebra)
        return PointPair(point_a=p1, point_b=p2)
```

---

## 12. Implementation Phases (within Phase 10)

| Sub-phase | Description |
|-----------|-------------|
| 10a | Add `HPoint` to `entities.py` + `__init__.py` |
| 10b | Refactor analysis signatures: add `opns` to entity functions, remove from operator functions |
| 10c | Implement IPNS in `analysis_e3.py` via dualization + type remapping |
| 10d | Implement IPNS in `analysis_p3.py` via dualization |
| 10e | Implement IPNS + HPoint detection in `analysis_pga3.py`; fix translator |
| 10f | Implement IPNS + HPoint detection in `analysis_n3.py`; fix translator |
| 10g | Refactor create signatures: add `opns` to entity functions, remove from operator functions |
| 10h | Implement IPNS creation in all `create_*.py` modules via OPNS+sdual |
| 10i | Add `create_homogeneous_point` to `create_n3.py` |
| 10j | Update `__init__.py` exports |
| 10k | Update documentation |

---

## 13. Verification Checklist

- [ ] `HPoint` created and re-exported
- [ ] `Entity` union type includes `HPoint`
- [ ] `analyze_entity(mv, opns=True)` returns same results as before (backward compatible)
- [ ] `analyze_entity(mv, opns=False)` correctly dualizes in E3, P3, PGA3, N3
- [ ] E3 IPNS: grade 1 vector → Plane through origin
- [ ] E3 IPNS: grade 2 bivector → Point
- [ ] N3 OPNS: grade 2 blade without Euclidean bivectors → HPoint
- [ ] N3 OPNS: grade 2 blade with Euclidean bivectors → PointPair
- [ ] N3 IPNS: blade correctly dualizes and returns appropriate entity
- [ ] PGA3 HPoint NOT detected (only Point)
- [ ] P3 HPoint NOT detected (only Point)
- [ ] `analyze_operator` has NO `opns` parameter
- [ ] `create_operator` has NO `opns` parameter
- [ ] Translator extraction uses direct coefficient reading (not factor sum)
- [ ] `create_entity(point, opns=False)` returns IPNS blade (dual of OPNS)
- [ ] Round-trip: `analyze_entity(create_entity(basis, entity, opns=X), opns=X)` returns equivalent entity
- [ ] N3 Sphere analyzed as `Sphere` via `analyze_entity`
- [ ] N3 Sphere analyzed as `Inversion` via `analyze_operator`