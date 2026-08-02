# E3 Audit Issues — Implementation Plan

**Date:** 31 July 2026  
**Reference:** `dev/notes/e3-code-audit.md` (section J. Recommendations)  
**Status:** Plan — do not implement yet

---

## Overview

The E3 code audit found **no critical issues** — the implementation is faithfully aligned with the Perwass reference. Four minor cosmetic/documentation issues were identified. This plan addresses them in dependency order so that no step requires refactoring an earlier step.

| Issue                                    | Location                    | Type            |
| ---------------------------------------- | --------------------------- | --------------- |
| `Direction` docstring excludes E3        | `entities.py:53`            | Documentation   |
| Blade name e₃₁ vs e₁₃                    | `basis/e3.py:25`            | Cosmetic        |
| `BasisE3.rotor` duplicates create_rotor  | `basis/e3.py:46-50`         | Code quality    |
| Line → Direction round-trip confusion    | `create_e3.py` + `analysis_e3.py` | Documentation   |

---

## Phase 1 — Fix `Direction` docstring

**File:** `py/pytanga/geometry/entities.py`, line 53

**Current:**
```python
"""A direction vector in 3D space (ideal point at infinity).

Attributes:
    x: The x-component of the direction vector.
    y: The y-component of the direction vector.
    z: The z-component of the direction vector.

Supported algebras: P3, N3/PGA3 (not E3)
"""
```

**Change:** Add E3 to the supported algebras list and clarify its role:

```python
"""A direction vector in 3D space.

In E3, a grade-1 vector represents a line through the origin in OPNS
(see Perwass §"Outer Product Representations", eqn. GAGeo:E3:OPLine1).
In P3/N3/PGA3, a direction represents an ideal point at infinity.

Attributes:
    x: The x-component of the direction vector.
    y: The y-component of the direction vector.
    z: The z-component of the direction vector.

Supported algebras: E3, P3, N3/PGA3
"""
```

**Rationale:** The `Direction` dataclass is returned by `analysis_e3.py:_direction_from_factor` for grade-1 OPNS entities (lines through origin). The current docstring incorrectly excludes E3.

**Dependencies:** None — pure documentation change, no code logic affected.

---

## Phase 2 — Harmonize blade naming (e₃₁ → e₁₃)

**File:** `py/pytanga/basis/e3.py`, line 25

**Current:**
```python
self.e31 = self.op(self.e3, self.e1)
```

**Analysis:** Perwass Table GAGeo:G3AlgBasis uses e₁₃ as the canonical name for the bivector containing e₁ and e₃. The code constructs e₃₁ = e₃∧e₁ = −e₁₃, which is algebraically correct (the sign flip is consistent throughout the algebra), but the displayed name "e31" differs from the reference.

**Option A — Change construction order (pure cosmetic):**
```python
self.e13 = self.op(self.e1, self.e3)
```
- Blade ID is still 5 (bitmask 101 = e₁∧e₃ in canonical ordering)
- Coefficient value is now +1 instead of −1 (flips sign of this blade vs e31)
- Display name changes from "e31" to "e13"
- ⚠️ **All existing test assertions that reference `e31` by name must be updated**
- ⚠️ **Any user code that references `basis_e3.e31` will break**

**Option B — Add an alias, keep the old name working:**
```python
self.e31 = self.op(self.e3, self.e1)
self.e13 = -self.e31   # alias matching Perwass notation
```
- Non-breaking: both `e31` and `e13` work
- Adds one line, no test changes needed
- ✅ Safe to implement at any point

**Option C — Do nothing:**
- Accepted as a known minor discrepancy, documented in the audit
- Simplest option — no risk

**Decision needed:** Which option to implement?

**Dependencies:** Depends on the chosen option. Option B has no dependencies and can be done at any point. Option A requires updating all references in tests and examples (but no refactoring of Phase 1 or 3).

---

## Phase 3 — Consolidate rotor creation

**Files:**
- `py/pytanga/basis/e3.py`, lines 46–50: `BasisE3.rotor()`
- `py/pytanga/geometry/create_e3.py`, lines 147–165: `create_rotor()`

### Current state

Two independent implementations produce the same rotor formula:

**`BasisE3.rotor()` (basis/e3.py:46–50):**
```python
def rotor(self, theta: float, axis: MV) -> MV:
    axis = axis.normalized()
    plane = self.I | axis          # inner product: I · axis = axis·I⁻¹ → bivector
    return math.cos(theta / 2.0) + plane * math.sin(theta / 2.0)
```

**`create_rotor()` (create_e3.py:147–165):**
```python
def create_rotor(basis: Algebra, angle: float, axis: Direction) -> MV:
    half = angle / 2.0
    return basis.multivector({
        0: math.cos(half),
        E23: math.sin(half) * axis.x,
        E13: -math.sin(half) * axis.y,
        E12: math.sin(half) * axis.z,
    })
```

### Issue

Both produce the same MV but use different approaches:
- `BasisE3.rotor` uses `I | axis` (inner product), which is elegant but less obvious
- `create_rotor` manually assigns blade coefficients, which is explicit but fragile (hardcoded blade IDs)

### Plan

Make `BasisE3.rotor` delegate to `create_e3.create_rotor`:

```python
# basis/e3.py
def rotor(self, theta: float, axis: MV) -> MV:
    """Rotor for rotation by angle theta about the given axis.

    Delegates to create_e3.create_rotor for a single source of truth.
    """
    from pytanga.geometry.create_e3 import create_rotor
    from pytanga.geometry.entities import Direction
    return create_rotor(
        self,
        float(theta),
        Direction(float(axis[1]), float(axis[2]), float(axis[4]))
    )
```

Before making this change, verify the two implementations produce identical results for a set of test cases.

**Steps:**
1. Write/run a verification script comparing both implementations
2. If identical, update `BasisE3.rotor` to delegate to `create_rotor`
3. Mark `BasisE3.rotor` as a convenience method in its docstring

**Dependencies:** None from Phase 1 or 2. Can be done independently at any point.

---

## Phase 4 — Document Line → Direction round-trip

**Files:** `py/pytanga/geometry/create_e3.py` (docstring), `py/pytanga/geometry/analysis_e3.py` (docstring)

### Issue

The round-trip is:
```
create_entity(Line(origin=(0,0,0), direction=d)) → grade-1 MV → analyze_entity → Direction
```

The entity type changes from `Line` to `Direction`. This happens because:
- In E3 OPNS, a grade-1 vector is a line through the origin — syntactically identical to a direction vector
- The `Line` dataclass carries an `origin` field, but E3 can only represent lines through the origin (origin is always (0,0,0))
- The analysis cannot reconstruct the `origin` field because it's always implicit

Perwass explicitly states that points (hence origins) cannot be represented in E3 Cl(3).

### Plan

Add documentation to both `create_e3.py` and `analysis_e3.py`:

**`create_e3.py` — `create_line` docstring addition:**
```python
def create_line(basis, origin, direction, *, opns=True):
    """Line through the origin in direction *d* (grade-1 vector).

    In E3 only lines through the origin can be represented.  If *origin*
    is not (0, 0, 0), a ``ValueError`` is raised.

    .. note::

       The returned MV is a grade-1 vector.  When analyzed with
       ``analyze_entity(opns=True)``, it is recognized as a
       :class:`Direction`, not a :class:`Line`.  This is because E3
       cannot distinguish a line-through-origin from a raw direction
       vector — the origin is always implicitly (0, 0, 0).  Use P3
       or N3 for round-trips that preserve the ``Line`` entity type.
    """
```

**`analysis_e3.py` — `analyze_entity` docstring addition:**
```python
    OPNS entities (pure-grade blades):

    - Grade 1 → :class:`Direction` (line through origin in OPNS)
      .. note::

         A grade-1 vector created from a :class:`Line` through the
         origin will be analyzed as a :class:`Direction`, not a
         :class:`Line`.  This is an inherent limitation of E3 —
         the origin is always (0, 0, 0) and cannot be recovered.
```

**Dependencies:** None — pure documentation additions, independent of all other phases.

---

## Summary of Changes (ordered by implementation phase)

| Phase | File                          | Change                                                     | Risk       |
| ----- | ----------------------------- | ---------------------------------------------------------- | ---------- |
| 1     | `geometry/entities.py:53`     | Fix `Direction` docstring — add E3 to supported algebras   | None       |
| 2     | `basis/e3.py:25`              | Harmonize e₃₁ → e₁₃ blade naming (option B or C TBD)      | Low (B)    |
| 3     | `basis/e3.py:46-50`           | Consolidate `BasisE3.rotor` to delegate to `create_rotor`  | Low        |
| 4     | `create_e3.py` + `analysis_e3.py` | Document Line → Direction round-trip limitation        | None       |

Phases 1–4 are independent — each can be implemented in any order without requiring refactoring of the others.