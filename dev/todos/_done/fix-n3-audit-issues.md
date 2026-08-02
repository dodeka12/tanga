# N3 Audit Issues — Implementation Plan

**Date:** 31 July 2026
**Reference:** `dev/notes/n3-code-audit.md` (Summary of Findings)
**Status:** Plan — do not implement yet

---

## Overview

The N3 code audit found 10 issues: 1 high, 4 medium, 5 low. This plan addresses all of them in dependency order. The key principle is that **raw blade ID reads must be replaced with algebraic extraction methods early** (Phase 3), so that subsequent fixes (ReflectionLine, Motor, GeneralDilator) build on a clean foundation and never need to be re-refactored.

| # | ID | Issue | Severity | Location |
|---|----|-------|----------|----------|
| 1 | A1 | `e0` alias for `einf` is misleading | 🟢 LOW | `basis/n3.py:39` |
| 2 | F1 | Duplicated `_get_einf`/`_get_eo` in create_n3 and analysis_n3 | 🟢 LOW | both files |
| 3 | C2/D1/E1 | Raw blade ID reads in translator/dilator/classification | 🟡 MEDIUM | `analysis_n3.py:496-498,540-547,553` |
| 4 | C1 | ReflectionLine analysis returns zero direction | 🔴 HIGH | `analysis_n3.py:482-484` |
| 5 | C3 | Motor analysis extracts translator from full MV | 🟡 MEDIUM | `analysis_n3.py:517` |
| 6 | C4 | GeneralDilator analysis raises `NotImplementedError` | 🟡 MEDIUM | `analysis_n3.py:508` |
| 7 | B2/F2 | Imaginary entities lost in `create_entity` dispatch | 🟡 MEDIUM | `create.py:101,106` |
| 8 | B1 | HPoint weight not recovered in analysis | 🟢 LOW | `analysis_n3.py:174` |

---

## Dependency Graph

```
Phase 1 (e0 alias)            ── independent, trivial
Phase 2 (shared helpers)      ── independent, enables Phase 3
Phase 3 (algebraic extraction)── depends on Phase 2, enables Phases 4–6
Phase 4 (ReflectionLine)      ── depends on Phase 3
Phase 5 (Motor)               ── depends on Phase 3
Phase 6 (GeneralDilator)      ── depends on Phase 3
Phase 7 (imaginary dispatch)  ── independent of analysis, tested after Phases 4–6
Phase 8 (HPoint weight)       ── depends on Phase 3
```

**Critical ordering constraint:** If ReflectionLine (C1) or Motor (C3) were fixed first using raw blade IDs, they would need to be re-refactored when Phase 3 introduces algebraic extraction. Phase 3 must come before Phases 4–6.

---

## Phase 1 — Remove `e0` alias from BasisN3

**File:** `py/pytanga/basis/n3.py`, line 39

**Issue (A1):** `self.e0 = self.einf` creates a misleading alias. Perwass uses **e₀** (subscript "o" for origin) for the origin null vector, not the point at infinity. A user expects `e0` to mean `eo`, not `einf`.

**Change:** Delete the line and its comment:

```diff
         self.einf = mv({_EP: 1.0,  _EM: 1.0})   # ep + em
         self.eo   = mv({_EP: -0.5, _EM: 0.5})   # 0.5·em - 0.5·ep
-        self.e0   = self.einf                    # conventional alias
         self.I    = mv({self.pseudoscalar_id: 1})
```

**Verification:** `grep -rn "\.e0\b" py/pytanga/ --include="*.py" | grep -v "__pycache__"` — expect zero hits (no pytanga code references this alias externally).

**Dependencies:** None.

---

## Phase 2 — Add blade IDs to BasisN3 + create shared N3 helpers module

**Files:**
- `py/pytanga/basis/n3.py` — add class-level blade ID constants
- **NEW:** `py/pytanga/geometry/_n3_helpers.py`
- `py/pytanga/geometry/create_n3.py`
- `py/pytanga/geometry/analysis_n3.py`

**Issues addressed:** F1 (duplicated helpers) and C2/D1/E1 (raw blade ID reads)

### Step 2a — Add blade IDs to BasisN3

Add class-level blade ID constants to `BasisN3` in `basis/n3.py`
(following the pattern established by `BasisE3`):

```python
class BasisN3(Algebra):
    """Null 3D algebra G(5, 0b10000) — raw named blades, no geometric interpretation."""

    # Blade bitmask IDs (dim=5: e₁=1, e₂=2, e₃=4, ep=8, em=16)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    EP: int = 8   # ep = e4,  ep² = +1
    EM: int = 16  # em = e5,  em² = -1
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7
```

This makes the blade IDs available as `basis.E1`, `mv.algebra.E12`, etc.
and provides a single canonical definition.  The existing module‑level
private constants `_EP` and `_EM` in `basis/n3.py` can remain or be
removed in a cleanup pass.

### Step 2b — Create `_n3_helpers.py`

Create a shared N3 helpers module for algebraic extraction functions
that were previously duplicated between `create_n3.py` and
`analysis_n3.py`.  Blade IDs are sourced from `BasisN3`.

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared N3 helper functions for creation and analysis modules.

Provides algebraic extraction of null-vector components (e∞ and e₀)
without relying on raw blade IDs of the ep/em embedding.

Reference: Perwass, "Geometric Algebra with Applications in Engineering",
           Chapter "Conformal Space".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytanga.algebra._algebra import Algebra
    from pytanga.algebra._mv import MV

# Blade IDs are sourced from BasisN3 as the single source of truth.
# The module-level aliases exist for backward compatibility with code
# that imports them directly.  Prefer basis.E12 for new code.
from pytanga.basis.n3 import BasisN3

E1 = BasisN3.E1
E2 = BasisN3.E2
E3 = BasisN3.E3
E12 = BasisN3.E12
E13 = BasisN3.E13
E23 = BasisN3.E23
E123 = BasisN3.E123


def get_einf(basis: Algebra) -> MV:
    """Return the point-at-infinity null vector e∞."""
    if hasattr(basis, "einf"):
        return basis.einf
    return basis.multivector({8: 1.0, 16: 1.0})


def get_eo(basis: Algebra) -> MV:
    """Return the origin null vector e₀."""
    if hasattr(basis, "eo"):
        return basis.eo
    return basis.multivector({8: -0.5, 16: 0.5})


def einf_coeff(mv: MV, eo: MV) -> float:
    """e∞ coefficient of *mv* = −mv·e₀ (since e∞·e₀ = −1)."""
    return -float(mv.sp(eo))


def eo_coeff(mv: MV, einf: MV) -> float:
    """e₀ coefficient of *mv* = −mv·e∞."""
    return -float(mv.sp(einf))


def eucl_part(mv: MV, einf: MV, eo: MV) -> tuple[float, float, float]:
    """Euclidean (e₁, e₂, e₃) coefficients of a grade-1 blade.

    Subtracts the null components to recover the pure Euclidean part:
        x = mv − einf_c·e∞ − eo_c·e₀
    """
    einf_c = einf_coeff(mv, eo)
    eo_c = eo_coeff(mv, einf)
    return (
        float(mv[E1]) - einf_c * float(einf[E1]) - eo_c * float(eo[E1]),
        float(mv[E2]) - einf_c * float(einf[E2]) - eo_c * float(eo[E2]),
        float(mv[E3]) - einf_c * float(einf[E3]) - eo_c * float(eo[E3]),
    )


def translator_coeffs(mv: MV, basis: Algebra) -> tuple[float, float, float]:
    """Extract (dx, dy, dz) from a translator versor via algebraic extraction.

    For T = 1 − ½·t·e∞, the translation vector is:
        tᵢ = +2 · mv·(eᵢ∧e₀) / mv[0]

    Uses the algebraic identity (eᵢ∧e∞)·(eᵢ∧e₀) = 1 to extract
    the eᵢ∧e∞ coefficient without relying on raw ep/em blade IDs.

    Replaces the fragile:  dx = −2.0 * float(mv[9]) / scal
    """
    eo = get_eo(basis)
    scal = float(mv[0])
    if abs(scal) < 1e-15:
        raise ValueError("Translator has zero scalar component")

    e1_e0 = basis.e1.op(eo)  # e₁∧e₀
    e2_e0 = basis.e2.op(eo)  # e₂∧e₀
    e3_e0 = basis.e3.op(eo)  # e₃∧e₀

    return (
        +2.0 * float(mv.sp(e1_e0)) / scal,
        +2.0 * float(mv.sp(e2_e0)) / scal,
        +2.0 * float(mv.sp(e3_e0)) / scal,
    )


def has_translator_components(mv: MV, basis: Algebra) -> bool:
    """Check if *mv* has eᵢ∧e∞ bivector components."""
    try:
        tx, ty, tz = translator_coeffs(mv, basis)
    except ValueError:
        return False
    return abs(tx) + abs(ty) + abs(tz) > 1e-15


def has_E_component(mv: MV, basis: Algebra) -> bool:
    """Check if *mv* has an e∞∧e₀ component (E = e∞∧e₀).

    Since E² = (e∞∧e₀)·(e∞∧e₀) = −1, the E coefficient in mv
    is given by −mv·E.
    """
    einf = get_einf(basis)
    eo = get_eo(basis)
    E = einf.op(eo)  # e∞∧e₀
    coeff = -float(mv.sp(E))
    return abs(coeff) > 1e-15


def E_coefficient(mv: MV, basis: Algebra) -> float:
    """Extract the e∞∧e₀ bivector coefficient from *mv*.

    Since E² = −1, the coefficient is −mv·E.
    """
    einf = get_einf(basis)
    eo = get_eo(basis)
    E = einf.op(eo)
    return -float(mv.sp(E))


def bivec_has_null(factor: MV, einf: MV, eo: MV) -> bool:
    """True if a bivector factor has e∞ or e₀ component."""
    return abs(einf_coeff(factor, eo)) > 1e-15 or abs(eo_coeff(factor, einf)) > 1e-15
```

### Step 2b — Update `create_n3.py`

Replace the local `_einf`, `_eo`, and blade ID constants with imports from `_n3_helpers`:

```diff
-from .entities import Direction, Plane, Point
-from .operators import Rotor, Translator
+from ._n3_helpers import (
+    E1, E2, E3, E12, E13, E23, E123,
+    get_einf, get_eo,
+)
+from .entities import Direction, Plane, Point
+from .operators import Rotor, Translator

-# Blade IDs for Euclidean components only
-E1, E2, E3 = 1, 2, 4
-E12, E13, E23 = 3, 5, 6
-
-
-def _einf(basis: Algebra) -> MV:
-    """Return the point-at-infinity null vector e∞."""
-    if hasattr(basis, "einf"):
-        return basis.einf
-    return basis.multivector({8: 1.0, 16: 1.0})
-
-
-def _eo(basis: Algebra) -> MV:
-    """Return the origin null vector e₀."""
-    if hasattr(basis, "eo"):
-        return basis.eo
-    return basis.multivector({8: -0.5, 16: 0.5})
```

Then update all call sites (~12): `_einf(basis)` → `get_einf(basis)`, `_eo(basis)` → `get_eo(basis)`. The blade IDs (E1/E2/E3/E12/E13/E23) come from the shared module now — no local definitions remain.

### Step 2c — Update `analysis_n3.py`

Replace local definitions with imports:

```diff
+from ._n3_helpers import (
+    E1, E2, E3, E12, E13, E23, E123,
+    get_einf, get_eo, einf_coeff, eo_coeff, eucl_part,
+    translator_coeffs, has_translator_components, has_E_component,
+    E_coefficient, bivec_has_null,
+)
 from .entities import ( ... )
 from .operators import ( ... )

-# Blade IDs for Euclidean components only
-E1, E2, E3 = 1, 2, 4
-E12, E13, E23 = 3, 5, 6
-E123 = 7
-
-# ── Helpers for algebraic extraction ──
-def _get_einf(alg: Algebra) -> MV:
-    ...
-def _get_eo(alg: Algebra) -> MV:
-    ...
-def _einf_coeff(mv: MV, eo: MV) -> float:
-    ...
-def _eo_coeff(mv: MV, einf: MV) -> float:
-    ...
-def _eucl_part(mv: MV, einf: MV, eo: MV) -> tuple[float, float, float]:
-    ...
```

Then update all call sites (~30) with find-and-replace:
- `_get_einf(` → `get_einf(`
- `_get_eo(` → `get_eo(`
- `_einf_coeff(` → `einf_coeff(`
- `_eo_coeff(` → `eo_coeff(`
- `_eucl_part(` → `eucl_part(`

Also remove these now-redundant helper functions (lines 572–601):
- `_has_euclidean` — inline the one call site in `_classify_quad_reflector`
- `_has_einf_only` — replaced by `not bivec_has_null` in Phase 5
- `_has_any_null` — replaced by `bivec_has_null`
- `_has_null` — wrapper; replace call sites with `bivec_has_null`

**Dependencies:** None. Pure refactoring — same behavior, different import location.

---

## Phase 3 — Replace raw blade IDs with algebraic extraction

**Files:**
- `py/pytanga/geometry/analysis_n3.py`
- `py/pytanga/geometry/_n3_helpers.py`

**Issues addressed:** C2 (translator raw IDs), D1 (scale fragility), E1 (blade-ID fragility)

### Step 3a — Replace `_translator_from_versor`

**Current (lines 540–547):**
```python
def _translator_from_versor(mv: MV) -> Translator:
    scal = float(mv[0])
    if abs(scal) < 1e-15:
        raise ValueError("Translator has zero scalar component")
    dx = -2.0 * float(mv[9]) / scal     # ep∧e₁ only — fragile!
    dy = -2.0 * float(mv[10]) / scal
    dz = -2.0 * float(mv[12]) / scal
    return Translator(vector=Direction(dx, dy, dz))
```

**New:**
```python
def _translator_from_versor(mv: MV) -> Translator:
    """Extract translation vector using algebraic eᵢ∧e₀ inner product.

    Uses the algebraic identity (eᵢ∧e∞)·(eᵢ∧e₀) = 1 to extract
    the eᵢ∧e∞ coefficient without relying on raw ep/em blade IDs.
    For T = 1 − ½·t·e∞:  tᵢ = +2 · mv·(eᵢ∧e₀) / mv[0].
    """
    dx, dy, dz = translator_coeffs(mv, mv.algebra)
    return Translator(vector=Direction(dx, dy, dz))
```

### Step 3b — Replace `_classify_double_reflector` blade-ID checks

**Current (lines 492–508):**
```python
def _classify_double_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    t_x = abs(float(mv[9])) + abs(float(mv[17]))
    t_y = abs(float(mv[10])) + abs(float(mv[18]))
    t_z = abs(float(mv[12])) + abs(float(mv[20]))
    has_t = (t_x + t_y + t_z) > 1e-15
    has_E = abs(float(mv[24])) > 1e-15  # ep∧em
    ...
```

**New:**
```python
def _classify_double_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    has_t = has_translator_components(mv, mv.algebra)
    has_E = has_E_component(mv, mv.algebra)
    ...
```

### Step 3c — Replace `_dilator_from_versor` blade-ID read

**Current (line 553):**
```python
    aE = float(mv[24])  # ep∧em = e∞∧e₀
```

**New:**
```python
    aE = E_coefficient(mv, mv.algebra)
```

**Dependencies:** Phase 2 must be complete (shared helpers available).

---

## Phase 4 — Fix ReflectionLine analysis (C1)

**File:** `py/pytanga/geometry/analysis_n3.py`, `_classify_single_grade_versor` (lines 481–484)

**Issue (C1):** The grade-2 branch reads blade IDs E1, E2, E3 (= grade-1 blades) from a grade-2 MV. These will always be zero.

**Current:**
```python
    elif max_grade == 2:
        return ReflectionLine(
            direction=Direction(float(mv[E1]), float(mv[E2]), float(mv[E3]))
        )
```

**Fix:** The created ReflectionLine is `d∧e∞`. The direction is recovered via `d = −(d∧e∞)·e₀` because `(eᵢ∧e∞)·e₀ = eᵢ·(e∞·e₀) = −eᵢ`. So the grade-1 part of `mv·e₀` is exactly `−d`.

```python
    elif max_grade == 2:
        # ReflectionLine: mv = d∧e∞ where d is a Euclidean direction
        # d = −mv·e₀  (algebraic identity: (eᵢ∧e∞)·e₀ = −eᵢ)
        inner = mv.sp(eo)  # grade-1, purely Euclidean
        dx, dy, dz = float(inner[E1]), float(inner[E2]), float(inner[E3])
        # inner = −d, so flip signs to get d
        d_norm = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d_norm < 1e-15:
            raise ValueError("Zero direction in ReflectionLine versor")
        return ReflectionLine(
            direction=Direction(-dx / d_norm, -dy / d_norm, -dz / d_norm)
        )
```

**Dependencies:** Phase 3 (algebraic extraction) should be done first to ensure consistency, but this fix only strictly needs `get_eo` from Phase 2.

---

## Phase 5 — Fix Motor analysis (C3)

**File:** `py/pytanga/geometry/analysis_n3.py`, `_classify_quad_reflector` (lines 511–520)

**Issue (C3):** `_classify_quad_reflector` calls `_translator_from_versor(mv)` on the full motor `M = T·R`. For a motor, the rotor's scalar and bivector parts mix with the translator's components, corrupting the extraction.

### Analysis

A motor `M = T·R` has grades {0, 2, 4}. For `M = T·R = (1 − ½·t·e∞)·(s + B)`:
- The eᵢ∧e∞ components get contributions from both `−½·s·tᵢ·eᵢ∧e∞` (T × scalar) and from `−½·(t·e∞)·B` (T × rotor bivector)
- Reading raw blade IDs from the full MV gives contaminated results

### Fix

Use the blade factorization to separate rotor and translator. The 4 factors consist of 2 Euclidean reflection planes (→ rotor) and 2 null-containing planes (→ translator). Extract the translator from the null factors' product, not the full motor:

```python
def _classify_quad_reflector(mv: MV, einf: MV, eo: MV, factors: list[MV]):
    """Classify a 4-factor versor: Motor or GeneralRotor.

    Perwass table:
    - Motor:      grades {0,2,4}, 4 factors (2 Euclidean + 2 null = T·R)
    - GenRotor:   grades {0,2},   4 factors (T·R·T̃)
    """
    eucl = [f for f in factors if not bivec_has_null(f, einf, eo)]
    null_factors = [f for f in factors if bivec_has_null(f, einf, eo)]

    # Extract rotor from the Euclidean factors
    if len(eucl) == 2:
        rotor = _rotor_from_factors(eucl[0], eucl[1])
    else:
        rotor = Rotor(0.0, Direction(1, 0, 0))

    # Extract translator from the null factors' product (not the full motor)
    if len(null_factors) >= 2:
        T_part = null_factors[0].gp(null_factors[1])
        translator = _translator_from_versor(T_part)
    else:
        translator = _translator_from_versor(mv)

    # Grade-4 component distinguishes Motor from GeneralRotor
    grades = _get_grades(mv)
    if 4 in grades:
        return Motor(rotor=rotor, translator=translator)
    return GeneralRotor(rotor=rotor, translator=translator)
```

**Dependencies:** Phase 3 (translator_coeffs, bivec_has_null available).

---

## Phase 6 — Implement GeneralDilator analysis (C4)

**File:** `py/pytanga/geometry/analysis_n3.py`, `_classify_double_reflector` (line 508)

**Issue (C4):** The `has_E and has_t` case raises `NotImplementedError`.

### Analysis

Perwass table (GAConfSpc_Op.tex): GeneralDilator = T·D·T̃ has grades {0,2} with basis elements {1, e₁∞, e₂∞, e₃∞, e∞₀}. It has both eᵢ∧e∞ components (translator) and an e∞∧e₀ component (dilator).

### Implementation

Replace the `NotImplementedError` with:

```python
    elif has_E and has_t:
        # GeneralDilator: T·D·T̃ — has both eᵢ∧e∞ and e∞∧e₀
        dilator = _dilator_from_versor(mv)
        tx, ty, tz = translator_coeffs(mv, mv.algebra)
        translator = Translator(vector=Direction(tx, ty, tz))
        return GeneralDilator(factor=dilator.factor, translator=translator)
```

The existing `_dilator_from_versor` extracts the factor from a0 and aE. The `translator_coeffs` (from Phase 3) extracts the translation from the eᵢ∧e∞ components. Since `_classify_double_reflector` already handles `has_E and not has_t` → pure Dilator, this branch always has a non-None translator.

**Dependencies:** Phase 3 (translator_coeffs, has_E_component, has_translator_components available).

---

## Phase 7 — Fix imaginary entity dispatch in create_entity

**File:** `py/pytanga/geometry/create.py`, lines 96–109

**Issue (B2/F2):** `create_entity` dispatches `PointPair` to `create_point_pair` unconditionally, ignoring the `is_imaginary` flag. Same for `Circle` → `create_circle`.

### Approach

Add optional reconstruction fields to `PointPair` in `entities.py` so that analysis can store the parameters used to construct an imaginary point pair, enabling exact round-trip:

```python
@dataclass(frozen=True)
class PointPair:
    point_a: Point
    point_b: Point
    is_imaginary: bool = False
    # Reconstruction fields for imaginary point pairs (from dual circle)
    _center: Point | None = None
    _direction: Direction | None = None
    _separation: float | None = None
```

Update `_decompose_grade2` in `analysis_n3.py` to populate these fields for imaginary point pairs (they're already computed during the decomposition as center/direction/separation).

Then in `create.py`, use the reconstruction fields when available:

```python
    elif isinstance(entity, PointPair):
        if entity.is_imaginary and _detect(basis) == "n3":
            if entity._center is not None and entity._direction is not None:
                return mod.create_imag_point_pair(
                    basis, entity._center, entity._direction,
                    entity._separation or 1.0, opns=opns,
                )
            # Fallback: reconstruct from point_a/point_b
            center = Point(
                (entity.point_a.x + entity.point_b.x) / 2,
                (entity.point_a.y + entity.point_b.y) / 2,
                (entity.point_a.z + entity.point_b.z) / 2,
            )
            direction = Direction(
                entity.point_b.x - entity.point_a.x,
                entity.point_b.y - entity.point_a.y,
                entity.point_b.z - entity.point_a.z,
            )
            separation = math.sqrt(
                direction.x ** 2 + direction.y ** 2 + direction.z ** 2
            )
            return mod.create_imag_point_pair(
                basis, center, direction, separation, opns=opns,
            )
        return mod.create_point_pair(basis, entity.point_a, entity.point_b, opns=opns)

    elif isinstance(entity, Circle):
        if entity.is_imaginary and _detect(basis) == "n3":
            return mod.create_imag_circle(
                basis, entity.center, entity.normal, entity.radius, opns=opns,
            )
        return mod.create_circle(
            basis, entity.center, entity.normal, entity.radius, opns=opns,
        )
```

Add `import math` to `create.py` imports.

**Dependencies:** Independent of analysis phases — touches `entities.py` and `create.py`. Should be implemented after Phase 6 so all analysis code is stable for testing round-trips.

---

## Phase 8 — Recover HPoint weight in analysis (B1)

**File:** `py/pytanga/geometry/analysis_n3.py`, `_decompose_grade2` (line 174)

**Issue (B1):** `HPoint` is returned with `weight=1.0` regardless of the blade's scale.

### Analysis

For `H = w·(Cop(a) ∧ e∞) = w·a∧e∞ + w·e₀∧e∞`, the `e₀∧e∞` coefficient is `w`. Since `E² = (e∞∧e₀)·(e∞∧e₀) = −1`, we have `w = −H·(e∞∧e₀)`.

### Implementation

Replace the HPoint return:

```python
    # ── HPoint check: Q = P∧e∞ → Q∧e∞ = 0 ──
    if mv.op(einf).is_zero:
        # Extract weight from e₀∧e∞ coefficient
        # H = w·a∧e∞ + w·e₀∧e∞, and (e₀∧e∞)·(e∞∧e₀) = −1
        # So w = −H·(e∞∧e₀)
        weight = -E_coefficient(mv, alg)
        return HPoint(point=_factor_to_point(mv, alg), weight=weight)
```

Equivalent but more explicit:
```python
    if mv.op(einf).is_zero:
        E = einf.op(eo)  # e∞∧e₀
        weight = -float(mv.sp(E))  # H·E = −w (since E² = −1)
        return HPoint(point=_factor_to_point(mv, alg), weight=weight)
```

**Dependencies:** Phase 3 (`E_coefficient` or `get_einf`/`get_eo` available).

---

## Summary of Changes

| Phase | Files | Changes | Risk |
|-------|-------|---------|------|
| 1 | `basis/n3.py` | Delete `self.e0 = self.einf` line | None |
| 2 | **NEW** `_n3_helpers.py`, `create_n3.py`, `analysis_n3.py` | Extract shared helpers; update imports and ~40 call sites | Low — same logic, new location |
| 3 | `analysis_n3.py` | Replace raw blade ID reads with algebraic extraction in 3 functions | Low-Medium — formula verified numerically |
| 4 | `analysis_n3.py:482-484` | Fix ReflectionLine direction extraction | Low — algebraic identity: d = −mv·e₀ |
| 5 | `analysis_n3.py:511-520` | Fix Motor translator extraction via null-factor factorization | Medium — factorization-based, needs careful testing |
| 6 | `analysis_n3.py:508` | Implement GeneralDilator analysis | Low — new code in already-structured classification |
| 7 | `entities.py`, `create.py` | Add reconstruction fields, route imaginary entities | Low — dispatch change + optional fields |
| 8 | `analysis_n3.py:174` | Recover HPoint weight from e₀∧e∞ coefficient | Low — one-line algebraic extraction |

### Implementation Order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7 → Phase 8
```

- Phases 1 and 2 are independent (either can go first)
- Phase 3 **must** come before Phases 4–6 (provides algebraic helpers)
- Phases 4, 5, 6 are independent of each other within the analysis module
- Phase 7 is independent of Phases 4–6 (touches `create.py` and `entities.py` only)
- Phase 8 is lowest priority

### Test Plan

After all phases, run the full N3 test suite:

```bash
cd py && python -m pytest tests/ -k "n3" -v
```

Key round-trip tests to add (or verify manually):

| Test | Phase | Verifies |
|------|-------|----------|
| `test_reflection_line_round_trip` | 4 | Create ReflLine → analyze → direction matches |
| `test_motor_round_trip` | 5 | Create Motor → analyze → rotor + translator match |
| `test_general_dilator_round_trip` | 6 | Create GenDilator → analyze → factor + translator match |
| `test_imaginary_pp_round_trip` | 7 | Create imag PP → analyze → create → analyze (full round-trip) |
| `test_imaginary_circle_round_trip` | 7 | Create imag circle → analyze → create → analyze (full round-trip) |
| `test_hpoint_weight_round_trip` | 8 | Create HPoint(w=3) → analyze → weight = 3 |
| `test_translator_round_trip_algebraic` | 3 | Verify algebraic translator extraction same as raw blade ID for canonical cases |