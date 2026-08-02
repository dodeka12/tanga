# P3 Audit Issues — Implementation Plan

**Date:** 31 July 2026  
**Reference:** `dev/notes/p3-code-audit.md` (section I. Summary of Issues, section K. Recommendations)  
**Status:** Plan — do not implement yet

---

## Overview

The P3 code audit found **no critical issues** — the implementation is faithfully aligned with the Perwass projective space model. This plan addresses all six issues in dependency order, with the key requirement that **all geometric entities can be created as both OPNS and IPNS**.

| # | Issue | Location | Type |
|---|-------|----------|------|
| 1 | No blade‑ness check before `blade_factorize()` | `analysis_p3.py:_line_from_factors` | Defensive coding |
| 2 | Zero‑norm direction not rejected | `create_p3.py:create_direction` + `analysis_p3.py:_point_or_direction_from_coeffs` | Defensive coding |
| 3 | `create_point`/`create_direction`/`create_line` ignore `opns=False` | `create_p3.py` lines 36–66 | Missing functionality |
| 4 | Python/C++ rotor sign convention mismatch | `create_p3.py:create_rotor` vs `cpp/Tan.GA/BasisP3.h:CreateRotor` | Inconsistency |
| 5 | Redundant `make_*` factory functions | `analysis_p3.py` lines 204–353 | Code quality |
| 6 | Hardcoded blade ID constants | `create_p3.py` + `analysis_p3.py` module-level | Robustness |

---

## Phase 1 — Add blade‑ness check before `blade_factorize()` in line analysis

**File:** `py/pytanga/geometry/analysis_p3.py`, function `_line_from_factors` (line 118)

**Issue:** `_line_from_factors` calls `grade2.blade_factorize()` without first checking whether the bivector is simple (B∧B = 0). A non‑simple bivector passed to `blade_factorize()` will fail unpredictably.

**Change:** Before calling `blade_factorize()`, verify the grade-2 part is a simple bivector by computing `B∧B` (the grade-4 part). If non‑zero, raise `ValueError`.

```python
def _line_from_factors(mv: MV) -> Line:
    """Factorise a grade-2 blade → direction + point on line."""
    grade2 = mv.grade(2)

    # Blade‑ness check: a grade-2 blade must satisfy B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a line blade. "
            "(Bivector has non‑zero grade‑4 part: B∧B ≠ 0. "
            "Only simple (factorisable) bivectors represent lines in P3.)"
        )

    factors = grade2.blade_factorize()
    # … rest unchanged …
```

**Test additions (`py/tests/test_geometry_p3.py`):**
- `test_line_non_simple_bivector_raises`: Construct a non‑simple bivector (sum of two bivectors representing skew lines) and assert `analyze_entity` raises `ValueError` with a message about non‑simple bivectors.

**Dependencies:** None — pure defensive addition, no existing behavior changes.

---

## Phase 2 — Validate zero‑norm direction

**Files:**
- `py/pytanga/geometry/create_p3.py`, function `create_direction` (line 46)
- `py/pytanga/geometry/analysis_p3.py`, function `_point_or_direction_from_coeffs` (line 97)

**Issue:** `create_direction(0, 0, 0)` silently produces a zero MV, and `_point_or_direction_from_coeffs` returns `Direction(0, 0, 0)` when all e₁, e₂, e₃, e₄ coefficients are zero. The zero vector is not a valid geometric direction.

**Change in `create_p3.py`:**
```python
def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Ideal point ``x·e₁ + y·e₂ + z·e₃`` (e₄ = 0)."""
    if abs(x) < 1e-15 and abs(y) < 1e-15 and abs(z) < 1e-15:
        raise ValueError("Zero‑norm direction is not a valid geometric direction")
    if hasattr(basis, "direction"):
        return basis.direction(x, y, z)
    return basis.multivector({E1: x, E2: y, E3: z})
```

**Change in `analysis_p3.py`:**
```python
def _point_or_direction_from_coeffs(mv: MV) -> Point | Direction:
    """Read a grade-1 blade directly from coefficients."""
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    z = float(g1[E3])
    w = float(g1[E4])

    if abs(x) < 1e-15 and abs(y) < 1e-15 and abs(z) < 1e-15:
        if abs(w) < 1e-15:
            raise ValueError("Zero MV — not a point or direction")
        # All Euclidean components zero but e₄ ≠ 0 → only e₄ vector
        raise ValueError("MV has only e₄ component — not a point or direction in P3")

    if abs(w) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / w, y=y / w, z=z / w)
```

**Test additions:**
- `test_create_direction_zero_norm_raises`: `create_entity(basis_p3, Direction(0,0,0))` → `ValueError`
- `test_analyze_zero_vector_raises`: Zero MV passed to `analyze_entity` → `ValueError`

**Dependencies:** None — pure validation additions. This runs before Phase 3 so that when IPNS creation calls the OPNS creation path, the validation is already in place.

---

## Phase 3 — Implement IPNS creation for all entities via dualization

**Files:**
- `py/pytanga/geometry/create_p3.py`: `create_point`, `create_direction`, `create_line`, `create_space`
- `py/tests/test_geometry_p3.py`: add IPNS round-trip tests

**Strategy:** IPNS is the dual of OPNS. In G(4,0) with invertible pseudoscalar I = e₁₂₃₄ (I² = +1, I⁻¹ = I), the dual maps:

| Entity | OPNS grade | IPNS grade | Dual mapping |
|--------|-----------|-----------|--------------|
| Point | 1 (vector) | 3 (trivector) | IPNS(point) = OPNS(point).dual() |
| Direction | 1 (vector, e₄=0) | 3 (trivector, no e₄) | IPNS(dir) = OPNS(dir).dual() |
| Line | 2 (bivector) | 2 (bivector) | Self‑dual grade — IPNS(line) ≈ OPNS(line) up to sign |
| Plane | 3 (trivector) | 1 (vector) | OPNS(plane) = IPNS(plane).dual() ← already implemented correctly |
| Space | 4 (pseudoscalar) | 0 (scalar) | IPNS(space) = Space(scale).dual() → scalar |

**Key insight:** For point, direction, and line, IPNS creation is simply: create the OPNS form, then call `.dual()`. For space, likewise. This is clean, follows Perwass's dual‑based OPNS/IPNS construction, and requires no new grade‑level coefficient assignments.

**Algebraic verification — IPNS point from OPNS point:**
- OPNS point: `P = x·e₁ + y·e₂ + z·e₃ + 1·e₄` (grade 1)
- IPNS point: `P.dual() = P·I⁻¹ = P·I` where I = e₁₂₃₄ (grade 4)
- Result: `x·e₂₃₄ − y·e₁₃₄ + z·e₁₂₄ − 1·e₁₂₃` (grade 3)
- Perwass (GAPrjSpc.tex lines 246–248): "a point can be represented by the GIPNS of a 3‑blade. This corresponds to the intersection point of three planes." ✅

**Algebraic verification — IPNS direction:**
- OPNS direction: `D = x·e₁ + y·e₂ + z·e₃` (grade 1, e₄=0)
- IPNS direction: `D.dual() = D·I` (grade 3, no e₁₂₃ term, only e₂₃₄, e₁₃₄, e₁₂₄)

**Algebraic verification — IPNS line (self‑dual grade):**
- In G(4,0), grade 2 is the self‑dual grade (4 − 2 = 2). So IPNS(line) ≈ dual(OPNS(line)) which is another grade-2 bivector.
- However, the Perwass text (lines 228–242) describes IPNS line as the wedge of two IPNS plane vectors: `IPNS(line) = ipns_plane1 ∧ ipns_plane2`.
- For consistency and correctness, implement IPNS line via dualization: create the OPNS line bivector, then dualize. The analysis already handles IPNS lines correctly via `opns=False` → dual → `_line_from_factors`.

**Algebraic verification — IPNS space:**
- OPNS space: `S = scale·e₁₂₃₄` (grade 4)
- IPNS space: `S.dual() = scale·e₁₂₃₄·I = scale·I·I = scale·1` (grade 0 scalar, since I²=+1)
- Perwass: IPNS of pseudoscalar is just a scalar (no geometric constraint). ✅

### Changes

**`create_point` — add IPNS via dual:**
```python
def create_point(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Homogeneous point ``Hop(a) = x·e₁ + y·e₂ + z·e₃ + e₄``.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: grade‑1 vector ``Hop(a)``.
        *False* → IPNS: grade‑3 trivector (dual of Hop(a)), representing
        the intersection of three orthogonal planes through the point.
    """
    if hasattr(basis, "point"):
        opns_mv = basis.point(x, y, z)
    else:
        opns_mv = basis.multivector({E1: x, E2: y, E3: z, E4: 1})

    if opns:
        return opns_mv
    return opns_mv.dual()
```

**`create_direction` — add IPNS via dual:**
```python
def create_direction(
    basis: Algebra, x: float, y: float, z: float, *, opns: bool = True
) -> MV:
    """Ideal point ``x·e₁ + y·e₂ + z·e₃`` (e₄ = 0).

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: grade‑1 direction vector (no e₄).
        *False* → IPNS: grade‑3 trivector (dual of the direction vector).
    """
    if abs(x) < 1e-15 and abs(y) < 1e-15 and abs(z) < 1e-15:
        raise ValueError("Zero‑norm direction is not a valid geometric direction")

    if hasattr(basis, "direction"):
        opns_mv = basis.direction(x, y, z)
    else:
        opns_mv = basis.multivector({E1: x, E2: y, E3: z})

    if opns:
        return opns_mv
    return opns_mv.dual()
```

**`create_line` — add IPNS via dual:**
```python
def create_line(
    basis: Algebra, origin: Point, direction: Direction, *, opns: bool = True
) -> MV:
    """Line through *origin* with direction *d*.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: ``Hop(origin) ∧ Hop(origin + d)``
        (grade‑2 bivector, two homogeneous points on the line).
        *False* → IPNS: grade‑2 bivector (dual of the OPNS bivector),
        representing the intersection of two IPNS planes containing the line.

    Notes
    -----
    In G(4,0), grade 2 is the self‑dual grade, so OPNS and IPNS lines
    are both bivectors (but with different blade coefficients).
    """
    a = create_point(basis, origin.x, origin.y, origin.z, opns=True)
    b = create_point(
        basis, origin.x + direction.x, origin.y + direction.y, origin.z + direction.z,
        opns=True,
    )
    opns_mv = a.op(b)

    if opns:
        return opns_mv
    return opns_mv.dual()
```

**`create_space` — add IPNS via dual:**
```python
def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """Pseudoscalar.

    Parameters
    ----------
    opns : bool
        *True* (default) → OPNS: ``scale * e₁₂₃₄`` (grade‑4 pseudoscalar).
        *False* → IPNS: ``scale * 1`` (grade‑0 scalar).
    """
    opns_mv = basis.multivector({basis.pseudoscalar_id: scale})

    if opns:
        return opns_mv
    return opns_mv.dual()
```

**Test additions:**

Add IPNS round‑trip tests for point, direction, line, and space. Each test should:
1. Create the entity with `opns=False`
2. Analyze with `analyze_entity(mv, opns=False)`
3. Assert the result matches the original parameters

```python
# ═══════════════════════════════════════════════════════════════
# IPNS round‑trip tests
# ═══════════════════════════════════════════════════════════════

def test_create_point_ipns_round_trip(basis_p3):
    """Point(1,2,3) → IPNS (grade‑3) → analyze IPNS → Point(1,2,3)."""
    mv = create_entity(basis_p3, Point(1, 2, 3), opns=False)
    assert set(mv.grades) == {3}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(2)
    assert result.z == pytest.approx(3)

def test_create_direction_ipns_round_trip(basis_p3):
    """Direction(1,0,0) → IPNS (grade‑3) → analyze IPNS → Direction(1,0,0)."""
    mv = create_entity(basis_p3, Direction(1, 0, 0), opns=False)
    assert set(mv.grades) == {3}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Direction)
    assert result.x == pytest.approx(1)
    assert result.y == pytest.approx(0)
    assert result.z == pytest.approx(0)

def test_create_line_ipns_round_trip(basis_p3):
    """Line → IPNS → analyze IPNS → Line with correct direction."""
    line = Line(origin=Point(1, 2, 3), direction=Direction(0, 0, 1))
    mv = create_entity(basis_p3, line, opns=False)
    assert set(mv.grades) == {2}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Line)
    assert abs(result.direction.z) == pytest.approx(1)
    # origin may differ due to orthogonalization; direction is the invariant

def test_create_space_ipns_round_trip(basis_p3):
    """Space(scale=3) → IPNS (grade‑0 scalar) → analyze IPNS → Space(3)."""
    mv = create_entity(basis_p3, Space(scale=3.0), opns=False)
    assert set(mv.grades) == {0}
    result = analyze_entity(mv, opns=False)
    assert isinstance(result, Space)
    assert result.scale == pytest.approx(3)
```

**Dependencies:** Phase 2 (zero‑norm validation in `create_direction`) should be applied before or simultaneously with this phase, since the IPNS branch in `create_direction` calls the same validation logic.

**Analysis impact:** No changes needed in `analysis_p3.py` for entity IPNS — the existing `analyze_entity(mv, opns=False)` already correctly dualizes IPNS input to OPNS and routes to the right handler. The IPNS round‑trip will work automatically.

---

## Phase 4 — Harmonize Python/C++ rotor sign convention

**Files:**
- `py/pytanga/geometry/create_p3.py`, function `create_rotor` (line 141)
- `py/pytanga/geometry/analysis_p3.py`, function `make_rotor` (line 343)

**Issue:** The Python `create_rotor` uses `+sin(θ/2)` while the C++ `CBasisP3::CreateRotor` uses `−sin(θ/2)`. The standard literature convention is `R = exp(−θ·B/2) = cos(θ/2) − sin(θ/2)·B`.

**Decision:** Change Python to use `−sin(θ/2)` to match C++ and the standard exponential convention.

**Change in `create_p3.py:create_rotor`:**
```python
def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    """``cos(θ/2) − sin(θ/2)·(ax·e₂₃ + ay·e₃₁ + az·e₁₂)``.

    Uses the standard exponential convention R = exp(−θ·B/2), matching
    the C++ ``CBasisP3::CreateRotor`` implementation.
    """
    half = angle / 2.0
    return basis.multivector(
        {
            0: math.cos(half),
            E23: -math.sin(half) * axis.x,
            E13: math.sin(half) * axis.y,
            E12: -math.sin(half) * axis.z,
        }
    )
```

**Change in `analysis_p3.py:make_rotor`:** Same sign flip (will be deleted in Phase 5, but keep consistent until then).

**Test impact analysis:**
- `test_rotor_round_trip`: Round‑trip is sign‑insensitive — `_rotor_from_factors` computes `angle = 2·acos(n₁·n₂)` which recovers the angle magnitude regardless of whether the original rotor used +sin or −sin. No test changes needed.
- `test_rotor_application_homogeneous`: Uses 180° rotation (π), which is symmetric — +π and −π produce the same endpoint. No test changes needed.
- No test currently tests a non‑symmetric application angle (e.g., 60°), so no tests break.

**Dependencies:** Phase 3 touches independent functions. No conflict.

---

## Phase 5 — Remove redundant `make_*` factory functions

**File:** `py/pytanga/geometry/analysis_p3.py`, lines 204–353

**Issue:** `make_point`, `make_direction`, `make_line`, `make_plane`, and `make_rotor` duplicate the functions in `create_p3.py`. They appear to be unused by the public API.

**Before removal — verify no callers exist:**
```bash
grep -rn "make_point\|make_direction\|make_line\|make_plane\|make_rotor" py/ --include="*.py" | grep -v "def make_\|#\|import"
```

**If no callers are found:** Delete the `make_*` functions (lines 204–353). Keep the helper function `_get_grades` (line 361) which is used by the analysis code above.

**If callers are found:** Replace each call site with the corresponding `create_p3.py` function (which now supports both OPNS and IPNS via the `opns` parameter), then delete the `make_*` functions.

**Test impact:** None — these functions are not part of the public `create_entity`/`create_operator` API.

**Dependencies:** Phase 4 (rotor sign) touches `make_rotor`. Since we're deleting it anyway, the order doesn't matter for correctness. However, for code cleanliness, apply Phase 4 first so `make_rotor` has the corrected sign during the brief window before deletion.

---

## Phase 6 — Make blade IDs available as BasisP3 class attributes

**Files:**
- `py/pytanga/basis/p3.py` — add class attributes
- `py/pytanga/geometry/create_p3.py` — source from `BasisP3`
- `py/pytanga/geometry/analysis_p3.py` — source from `BasisP3`

**Issue:** Blade IDs are hardcoded as module-level constants in both
`create_p3.py` and `analysis_p3.py`. The E3 module has established the
pattern of defining blade IDs once on the basis class and sourcing from
there.

### 6a — Add blade IDs to BasisP3

Add class-level blade ID constants to `BasisP3` in `basis/p3.py`:

```python
class BasisP3(Algebra):
    """Projective 3D geometric algebra G(4, 0) with named blade attributes."""

    # Blade bitmask IDs (dim=4: e₁=1, e₂=2, e₃=4, e₄=8)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    E4: int = 8
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E14: int = 9
    E24: int = 10
    E34: int = 12
    E123: int = 7
```

### 6b — Update create_p3.py

Replace the module-level blade ID definitions with imports from `BasisP3`:

```python
# Blade IDs are sourced from BasisP3 as the single source of truth.
# The module-level aliases exist for backward compatibility with code
# that imports them directly.  Prefer basis.E12 for new code.
from pytanga.basis.p3 import BasisP3

E1 = BasisP3.E1
E2 = BasisP3.E2
E3 = BasisP3.E3
E4 = BasisP3.E4
E12 = BasisP3.E12
E13 = BasisP3.E13
E23 = BasisP3.E23
E14 = BasisP3.E14
E24 = BasisP3.E24
E34 = BasisP3.E34
E123 = BasisP3.E123
```

### 6c — Update analysis_p3.py

Same pattern — replace hardcoded constants with `BasisP3` attributes:

```python
# Blade IDs are sourced from BasisP3 as the single source of truth.
# The module-level aliases exist for backward compatibility with code
# that imports them directly.  Prefer basis.E12 or mv.algebra.E12 for new code.
from pytanga.basis.p3 import BasisP3

E1 = BasisP3.E1
E2 = BasisP3.E2
E3 = BasisP3.E3
E4 = BasisP3.E4
E12 = BasisP3.E12
E13 = BasisP3.E13
E23 = BasisP3.E23
E14 = BasisP3.E14
E24 = BasisP3.E24
E34 = BasisP3.E34
E123 = BasisP3.E123
```

**Dependencies:** None — pure refactoring, blade ID values do not change.
Prefer doing this early to minimize merge conflicts with other phases.
No circular import risk: `analysis_p3.py`/`create_p3.py` import from
`basis/p3.py` which does not import from geometry modules.

> **Note for N3 and PGA3 plans:** Blade IDs must be handled the same way —
> class attributes on the basis class, sourced as module-level aliases in
> the create/analysis modules.  This is not optional.

---

## Summary of Changes (ordered by implementation phase)

| Phase | Files | Changes | New tests | Risk |
|-------|-------|---------|-----------|------|
| 1 | `analysis_p3.py:_line_from_factors` | Add blade‑ness check (B∧B = 0) | +1 | None |
| 2 | `create_p3.py:create_direction`, `analysis_p3.py:_point_or_direction_from_coeffs` | Reject zero‑norm direction | +2 | None |
| 3 | `create_p3.py:create_point`, `create_direction`, `create_line`, `create_space` | Implement IPNS via OPNS→`.dual()` | +4 | Low — IPNS line analysis already works via `opns=False` flag |
| 4 | `create_p3.py:create_rotor`, `analysis_p3.py:make_rotor` | Flip `+sin` → `−sin` | None | Low — tests are sign‑insensitive |
| 5 | `analysis_p3.py` lines 204–353 | Remove `make_*` factory functions | None | None — dead code |
| 6 | `basis/p3.py`, `create_p3.py`, `analysis_p3.py` | Blade IDs as BasisP3 class attributes | None | None |

### Dependency graph

```
Phase 1 (blade‑ness)  ── independent (analysis only)
Phase 2 (zero‑norm)   ── independent
Phase 3 (IPNS)        ── needs Phase 2 first (zero‑norm in create_direction affects IPNS path too)
Phase 4 (rotor sign)  ── independent of Phases 1–3 (rotor code is separate from entity code)
Phase 5 (dead code)   ── after Phase 4 (for cosmetic consistency of make_rotor sign)
Phase 6 (blade IDs)   ── independent of all others; prefer early to minimize merge conflicts
```

### Recommended implementation order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
```

- Phase 1 (blade‑ness) and Phase 2 (zero‑norm) are independent of each other and can be done in either order.
- Phase 3 (IPNS) must come after Phase 2 because `create_direction`'s IPNS path calls the OPNS path internally, which should already have zero‑norm validation.
- Phase 4 (rotor) is independent of entity code; can be done anytime.
- Phase 5 (dead code) follows Phase 4 for cosmetic consistency.
- Phase 6 (blade IDs) is independent — prefer early to minimize merge conflicts.

---

## Test Plan

After all phases are implemented, run the full P3 test suite:

```bash
cd py && python -m pytest tests/test_geometry_p3.py -v
```

**Current test count:** 22  
**New tests added:** 7  
**Expected total:** 29 tests passing

| Phase | New test |
|-------|----------|
| 1 | `test_line_non_simple_bivector_raises` |
| 2 | `test_create_direction_zero_norm_raises` |
| 2 | `test_analyze_zero_vector_raises` |
| 3 | `test_create_point_ipns_round_trip` |
| 3 | `test_create_direction_ipns_round_trip` |
| 3 | `test_create_line_ipns_round_trip` |
| 3 | `test_create_space_ipns_round_trip` |

### IPNS round‑trip coverage matrix

After Phase 3, all entity types support both OPNS and IPNS creation and analysis:

| Entity | OPNS create → analyze | IPNS create → analyze |
|--------|----------------------|----------------------|
| Point | ✅ (existing test) | ✅ (new in Phase 3) |
| Direction | ✅ (existing test) | ✅ (new in Phase 3) |
| Line | ✅ (existing test) | ✅ (new in Phase 3) |
| Plane | ✅ (existing test) | ✅ (existing test) |
| Space | ✅ (existing test) | ✅ (new in Phase 3) |