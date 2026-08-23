# PGA3 Audit Issues — Implementation Plan

**Date:** 31 July 2026  
**Reference:** `dev/notes/pga3-code-audit.md` (sections 6, 8)  
**Status:** Plan — do not implement yet

---

## Overview

The PGA3 code audit found **two critical bugs**, **four feature gaps**, and **four minor issues**. This plan addresses all ten findings in dependency order so that no step requires refactoring an earlier step.

The **very first phase** establishes a standalone `BasisPGA3` that uses the Gunn/Dorst naming convention (`e0` for the null vector, `e0_recip` for its reciprocal). The old names `einf` and `eo` are **not** present on the class — they belong to the N3 conformal model, not to PGA3.

| # | Issue | Location | Type |
|---|-------|----------|------|
| 1 | `create_direction` OPNS form is wrong (produces origin, not direction) | `create_pga3.py:create_direction` | Critical bug |
| 2 | `_analyze_entity_ipns` grade‑3 routes to `_plane_from_vector` instead of dualizing | `analysis_pga3.py:_analyze_entity_ipns` | Critical bug |
| 3 | No `GeneralRotor` support (creation) | `create_pga3.py` | Missing feature |
| 4 | No `GeneralRotor` support (analysis) | `analysis_pga3.py:analyze_operator` | Missing feature |
| 5 | Missing creation functions (`create_reflection_line`, `create_reflection_origin`) | `create_pga3.py` | Missing feature |
| 6 | No normalization of point weight in analysis | `analysis_pga3.py:_point_or_direction_from_ipns`, `_point_from_trivector` | Bug / design gap |
| 7 | No blade‑ness check before `blade_factorize()` | `analysis_pga3.py:_line_from_bivector` | Defensive coding |
| 8 | Dead code in `_line_origin_from_planes` | `analysis_pga3.py:_line_origin_from_planes` | Code quality |
| 9 | `create_space` is fragile (manual blade ID assignment) | `create_pga3.py:create_space` | Robustness |
| 10 | Use `e0` / `e0_recip` instead of `einf` / `eo` everywhere (Gunn/Dorst convention) | `basis/pga3.py`, `create_pga3.py`, `analysis_pga3.py` | API consistency |

---

## Phase 1 — Standalone BasisPGA3 with `e0` / `e0_recip` + shared PGA3 utilities

**Files:**
- `py/pytanga/basis/pga3.py` — **rewrite**: extend `Algebra` directly; expose `e0` & `e0_recip`; no `einf`/`eo`
- **NEW:** `py/pytanga/geometry/_pga3_utils.py` — shared PGA3 helpers (dual, pseudo‑inverse, `e0`‑coeff extraction)
- `py/pytanga/geometry/create_pga3.py` — adapt imports & call sites
- `py/pytanga/geometry/analysis_pga3.py` — adapt imports & call sites

**Motivation:** `BasisPGA3` currently inherits from `BasisN3` and carries the N3 names `einf`/`eo`.  PGA3 (Gunn/Dorst) uses a single null vector **e₀**; the conformal pair e∞/eₒ belongs to N3.  The PGA3 basis must stand alone, define `e0` (= old `einf`) and `e0_recip` (= old `−eo`), and never expose `einf` or `eo`.

**Design:**

| Concept | PGA3 name | Internal embedding |
|---------|-----------|-------------------|
| Null vector | `e0` | `ep + em` (5D proxy) |
| Reciprocal of null vector | `e0_recip` | `0.5·ep − 0.5·em` (satisfies ⟨e0·e0_recip⟩₀ = 1) |
| Basis vectors | `e1, e2, e3` | dim=3 subspace of the 5D algebra |
| Algebra | G(3, 0, 1) — 4D PGA via 5D embedding | `Algebra(5, 0b10000)` |

### 1a — Rewrite `basis/pga3.py`

Replace the current implementation (which extends `BasisN3`) with a
standalone `BasisPGA3` class that extends `Algebra` directly.

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""BasisPGA3 — Gunn/Dorst 4D PGA via 5D null‑vector embedding.

Implements the plane‑based projective geometric algebra described in:

- Charles Gunn, *Geometric algebras for Euclidean geometry*,
  arXiv:1411.6502 (2016).

- Leo Dorst, *A Guided Tour to the Plane‑Based Geometric Algebra PGA*,
  bivector.net/PGA4CS.html (2020).

The Gunn/Dorst model uses a single null basis vector ``e₀`` with
``e₀² = 0``.  Since TANGA's Clifford algebra only supports metric
signatures with squares ±1, the null vector is modelled via the
embedding

    e₀ → ep + em,   ep² = +1, em² = -1,

as documented in ``docs/py/basis/pga_null_embedding.md``.  The pair
(ep, em) generates the 5‑dimensional algebra G(5, 0b10000); the
subspace {e₁, e₂, e₃, e₀} is algebraically isomorphic to the
Gunn/Dorst 4D PGA.

This class does **not** expose ``einf`` or ``eo`` — those belong to the
N3 conformal model.  Instead it exposes ``e0`` (the null vector) and
``e0_recip`` (its reciprocal, satisfying ⟨e0·e0_recip⟩₀ = 1).
"""

from __future__ import annotations

from functools import cached_property

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV


class BasisPGA3(Algebra):
    """Gunn/Dorst 4D PGA via 5D null‑vector embedding.

    Attributes:
        e0: The Gunn/Dorst null vector (embedding: ep + em).
        e0_recip: Reciprocal of e0 (embedding: 0.5·ep − 0.5·em).
        e1, e2, e3: Euclidean basis vectors.
        ep, em: Internal 5D embedding vectors (private; prefer e0).
    """

    # Blade bitmask IDs (dim=5: e₁=1, e₂=2, e₃=4, ep=8, em=16)
    E1: int = 1
    E2: int = 2
    E3: int = 4
    EP: int = 8   # ep = e4,  ep² = +1 (internal embedding)
    EM: int = 16  # em = e5,  em² = -1 (internal embedding)
    E12: int = 3
    E13: int = 5
    E23: int = 6
    E123: int = 7

    def __init__(self, dtype: str = "float64", **kw) -> None:
        super().__init__(5, 0b10000, dtype, **kw)
        mv = self.multivector
        self.e1 = mv({1: 1})
        self.e2 = mv({2: 1})
        self.e3 = mv({4: 1})
        self.ep = mv({self.EP: 1})   # internal — e4
        self.em = mv({self.EM: 1})   # internal — e5
        # e0 = ep + em — the Gunn/Dorst null vector
        self.e0 = mv({self.EP: 1.0, self.EM: 1.0})
        # e0_recip = 0.5·ep − 0.5·em  →  ⟨e0·e0_recip⟩₀ = 1
        self.e0_recip = mv({self.EP: 0.5, self.EM: -0.5})

    # ── convenience constructors ──────────────────────────────────

    def point(self, x: float, y: float, z: float) -> MV:
        """Point in IPNS / dual form: ``x·e₁ + y·e₂ + z·e₃ + e₀``.

        The OPNS form (grade‑3 trivector) is obtained via ``_pga3_dual(mv)``
        or by wedging three orthogonal planes through the point.
        """
        return self.multivector({1: x, 2: y, 4: z, self.EP: 1.0, self.EM: 1.0})

    def direction(self, x: float, y: float, z: float) -> MV:
        """Direction / ideal point (IPNS): ``x·e₁ + y·e₂ + z·e₃``
        (no e₀ component)."""
        return self.multivector({1: x, 2: y, 4: z})

    def plane(self, nx: float, ny: float, nz: float, d: float = 0.0) -> MV:
        """Plane (grade‑1): ``nx·e₁ + ny·e₂ + nz·e₃ + d·e₀``.

        *d* is the signed distance from the origin.
        """
        return self.multivector({1: nx, 2: ny, 4: nz, self.EP: d, self.EM: d})

    # ── display ───────────────────────────────────────────────────

    @cached_property
    def _display_basis(self) -> list:
        """Lazily built display basis — e₀ as the null generator."""
        from pytanga.algebra._display_basis import build_display_basis

        return build_display_basis(
            [("e1", self.e1), ("e2", self.e2), ("e3", self.e3), ("e0", self.e0)],
            self,
        )
```

Key changes from current code:
- **No `BasisN3` inheritance.** `BasisPGA3` extends `Algebra` directly.
- **No `einf` or `eo` attributes.**  `e0` replaces `einf`; `e0_recip` replaces `−eo`.
- **Blade IDs are class attributes** (`E1..E123, EP, EM`), following the `BasisE3` pattern.
- **`_display_basis`** uses `e0` (not `einf`) as the null basis generator.

### 1b — Create `_pga3_utils.py`

Move `_pga3_dual`, `_pga3_pinv`, and a new `_get_e0_coeff` helper to a shared
utility module.  Blade IDs are sourced from `BasisPGA3` as the single source
of truth.

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Shared PGA3 helper functions for creation and analysis modules.

PGA3 is modelled via the 5D null‑vector embedding (dim=5).
Blade IDs are sourced from ``BasisPGA3`` as the single source of truth.
"""

from __future__ import annotations

from functools import cache

from pytanga.algebra._algebra import Algebra
from pytanga.algebra._mv import MV
from pytanga.basis.pga3 import BasisPGA3

# Blade IDs for the 5D embedding (sourced from BasisPGA3)
E1 = BasisPGA3.E1
E2 = BasisPGA3.E2
E3 = BasisPGA3.E3
EP = BasisPGA3.EP
EM = BasisPGA3.EM
E12 = BasisPGA3.E12
E13 = BasisPGA3.E13
E23 = BasisPGA3.E23
E123 = BasisPGA3.E123


def _get_e0(alg: Algebra) -> MV:
    """Return the null vector e₀ (Gunn/Dorst PGA convention).

    In the 5D embedding, e₀ = ep + em.  Prefers ``alg.e0`` if available
    (BasisPGA3); falls back to manual construction from blade IDs (generic
    Algebra instances).
    """
    if hasattr(alg, "e0"):
        return alg.e0
    return alg.multivector({EP: 1.0, EM: 1.0})


@cache
def _pga3_pinv(alg: Algebra) -> MV:
    """Pseudo‑inverse of the 4D PGA pseudoscalar I₄ = e₁∧e₂∧e₃∧e₀."""
    I4 = alg.e1.op(alg.e2).op(alg.e3).op(_get_e0(alg))
    return I4.blade_pseudo_inverse()


def _pga3_dual(mv: MV) -> MV:
    """4D PGA dual using pseudo‑inverse of the PGA pseudoscalar."""
    return mv.ip(_pga3_pinv(mv.algebra))


def _get_e0_coeff(mv: MV) -> float:
    """Extract the e₀ coefficient from a grade‑1 IPNS vector.

    Uses the algebraic identity ⟨e₀ · e0_recip⟩₀ = 1, so:

        α = ⟨mv · e0_recip⟩₀

    On ``BasisPGA3`` instances this is exactly the coefficient of the
    e₀ component.  For other algebras the correct dual vector is
    constructed from blade IDs.

    Returns:
        The e₀ coefficient of the grade‑1 portion of *mv*.
    """
    alg = mv.algebra
    if hasattr(alg, "e0_recip"):
        e0_recip = alg.e0_recip
    else:
        e0_recip = alg.multivector({EP: 0.5, EM: -0.5})
    return float(mv.sp(e0_recip))
```

The `_get_e0_coeff` function uses the algebraic identity ⟨e0·e0_recip⟩₀ = 1.  
Because `e0 = ep + em` and `e0_recip = 0.5·ep − 0.5·em`:

    e0 · e0_recip = (ep)(0.5·ep) + (em)(−0.5·em) = 0.5 + 0.5 = 1

so the scalar product with `e0_recip` directly yields the `e0` coefficient.

### 1c — Update `create_pga3.py`

Replace module‑level blade IDs and the local `_einf` helper with imports
from `_pga3_utils`.  Replace all `_einf(basis)` / `basis.einf` references
with `_get_e0(basis)` / `basis.e0`.

```diff
-# Blade IDs (5D)
-E1, E2, E3 = 1, 2, 4
-EP, EM = 8, 16  # ep=e4, em=e5
-E12, E13, E23 = 3, 5, 6
-
+from ._pga3_utils import (
+    E1, E2, E3, EP, EM, E12, E13, E23,
+    _get_e0, _pga3_dual,
+)
```

Update every docstring that mentions `einf` → `e₀` (mathematical notation)
or `e0` (code reference).  For example:

```diff
-def create_point(basis, x, y, z) -> MV:
-    """x·e1 + y·e2 + z·e3 + einf"""
+def create_point(basis, x, y, z) -> MV:
+    """x·e₁ + y·e₂ + z·e₃ + e₀"""
```

### 1d — Update `analysis_pga3.py`

Replace module‑level blade IDs, the local `_pga3_dual`/`_pga3_pinv`, and
any `_get_einf`‑style helpers with imports from `_pga3_utils`.

```diff
-# Blade IDs for the 5D embedding
-E1, E2, E3 = 1, 2, 4
-EP, EM = 8, 16
-E12, E13, E23 = 3, 5, 6
-E123 = 7
-
-from functools import cache
-
-@cache
-def _pga3_pinv(alg):
-    ...
-
-def _pga3_dual(mv):
-    ...
-
-def _get_einf(alg):
-    ...
-
+from ._pga3_utils import (
+    E1, E2, E3, EP, EM, E12, E13, E23, E123,
+    _get_e0, _pga3_dual, _pga3_pinv, _get_e0_coeff,
+)
```

Then update every call site: `_get_einf(alg)` → `_get_e0(alg)`,  
`alg.einf` → `alg.e0` (or `_get_e0(alg)` for safety).

Update docstrings: `e∞` / `einf` → `e₀`.

### 1e — Verify no `einf` / `eo` references remain

Run a project‑wide search after Phase 1:

```bash
grep -rn 'einf\|\.eo\b' py/pytanga/basis/pga3.py py/pytanga/geometry/create_pga3.py py/pytanga/geometry/analysis_pga3.py
```

These three files should have **zero** matches (except possibly in
a comment explaining the historical rename).  The `eo` name remains
valid in N3‑module files (`basis/n3.py`, `create_n3.py`, `analysis_n3.py`),
which are not touched by this plan.

**Dependencies:** None — Phase 1 is the foundation for all subsequent phases.  
**Risk:** Medium — rewrites `BasisPGA3` and touches every PGA3 file.  
**Tests:** Existing PGA3 test suite must pass with no regressions.

---

## Phase 2 — Fix Critical Bugs (Independent)

Both critical bugs are independent of each other — they affect different
functions with no shared state.  Both now use `_pga3_dual` / blade IDs from
Phase 1.

### 2.1 Fix `create_direction` OPNS form

**File:** `py/pytanga/geometry/create_pga3.py`, function `create_direction`

**Problem:** The OPNS branch creates `e1 ∧ e2 ∧ e3 = I₃` (the origin point), not a direction at infinity.

**Fix:** Dualize the IPNS direction vector. A direction's IPNS form is
$v_1 e_1 + v_2 e_2 + v_3 e_3$ (no $e₀$). Its OPNS form is the 4D dual of this: `_pga3_dual(ipns)`. This produces a grade‑3 trivector whose 4D dual has zero $e₀$ component.

```python
def create_direction(basis: Algebra, x: float, y: float, z: float, *, opns: bool = True) -> MV:
    """Create a PGA3 direction (ideal point).

    *opns=True* (default): grade‑3 trivector (4D dual of the IPNS direction vector).
    *opns=False* (IPNS): grade‑1 vector ``x·e₁ + y·e₂ + z·e₃``.
    """
    if not opns:
        return basis.multivector({E1: x, E2: y, E3: z})

    # OPNS: dualize the IPNS direction vector using the 4D PGA dual.
    ipns = basis.multivector({E1: x, E2: y, E3: z})
    return _pga3_dual(ipns)
```

**Test additions:**
- `test_create_direction_opns_is_ideal` — Create a direction in OPNS, analyze it → returns `Direction`, not `Point`.
- `test_create_direction_opns_round_trip` — Direction(1,2,3) → OPNS → analyze OPNS → Direction(1,2,3).

### 2.2 Fix `_analyze_entity_ipns` grade‑3 path

**File:** `py/pytanga/geometry/analysis_pga3.py`, function `_analyze_entity_ipns`

**Problem:** IPNS grade‑3 trivectors are routed to `_plane_from_vector(mv)` without dualizing first. An IPNS trivector represents a plane; its OPNS form (grade‑1 plane vector) is obtained by dualizing.

**Fix:** Dualize the IPNS trivector before routing to `_plane_from_vector`:

```python
elif max_grade == 3:
    # IPNS trivector → dual → OPNS grade-1 vector → plane
    opns = _pga3_dual(mv)
    return _plane_from_vector(opns)
```

**Test addition:**
- `test_analyze_ipns_plane_round_trip` — Create a plane in IPNS (via `create_entity(Plane(...), opns=False)`), analyze with `opns=False`, verify it returns a `Plane` with matching normal and position.

**Dependencies:** None between 2.1 and 2.2. Both depend on Phase 1 for `_pga3_dual` and blade IDs.

---

## Phase 3 — Add Blade‑ness Validation and Clean Up Dead Code

### 3.1 Add blade‑ness check before `blade_factorize()`

**File:** `py/pytanga/geometry/analysis_pga3.py`, function `_line_from_bivector`

**Problem:** The function calls `blade_factorize()` on the grade‑2 portion without verifying it is a simple bivector. A non‑simple 2‑vector (a screw, per Dorst §5.6) would fail unpredictably.

**Fix:** Insert a blade‑ness check before factorization. Compute $B \wedge B$; if non‑zero, the bivector is not a blade.

```python
def _line_from_bivector(mv: MV) -> Line:
    """Decompose a grade‑2 bivector → Line (intersection of 2 planes)."""
    grade2 = mv.grade(2)

    # Blade‑ness check: a simple bivector satisfies B∧B = 0
    grade4 = grade2.op(grade2)
    if not grade4.is_zero:
        raise ValueError(
            "Non‑simple bivector — not a line. "
            "Only simple (factorisable) bivectors represent lines in PGA3. "
            "A non‑simple bivector is a screw/motor bivector; use analyze_operator instead."
        )

    factors = grade2.blade_factorize()
    # … rest unchanged …
```

**Test addition:**
- `test_line_non_simple_bivector_raises` — Construct a non‑simple bivector (sum of two skew lines) and assert `analyze_entity` raises `ValueError`.

### 3.2 Clean up dead code in `_line_origin_from_planes`

**File:** `py/pytanga/geometry/analysis_pga3.py`, function `_line_origin_from_planes`

**Problem:** The first three determinant computations are immediately overwritten by a second set labeled "Correction." The dead code is confusing.

**Fix:** Remove the overwritten dead code, keeping only the corrected Cramer's rule computation.

**Test:** No new test needed — existing line tests validate correctness by exercising this code path. Before/after verification: run existing PGA3 tests and confirm all still pass.

**Dependencies:** 3.1 and 3.2 are independent of each other. Both build on Phase 2 (correct entity analysis) but do not require it.

---

## Phase 4 — Add Weight Normalization to Point Analysis

**File:** `py/pytanga/geometry/analysis_pga3.py`, functions `_point_or_direction_from_ipns` and `_point_from_trivector`

**Problem:** Both functions read Euclidean coordinates from blade coefficients without dividing by the homogeneous weight $\alpha$ (the $e₀$ coefficient). This produces wrong Euclidean positions for any non‑unit‑weight point (centroids, interpolations, scaled versor applications).

**Key insight:** The PGA3 model lives in the 5D embedding where $e₀ = e_p + e_m$. The coefficient $\alpha$ is distributed across two blade IDs (`EP` and `EM`). The correct extraction uses $\alpha = \langle X \cdot e_0^{\text{recip}} \rangle_0$ (since $\langle e₀ \cdot e_0^{\text{recip}} \rangle_0 = 1$), which is algebraically robust.  `_get_e0_coeff` from Phase 1 already provides this.

### 4.1 Apply normalization in `_point_or_direction_from_ipns`

```python
def _point_or_direction_from_ipns(mv: MV) -> Point | Direction:
    """Extract Point/Direction from a grade‑1 IPNS vector.

    Finite point: ``x·e₁ + y·e₂ + z·e₃ + α·e₀`` → Point(x/α, y/α, z/α).
    Direction:    ``x·e₁ + y·e₂ + z·e₃`` (α = 0).
    """
    g1 = mv.grade(1)
    x = float(g1[E1])
    y = float(g1[E2])
    z = float(g1[E3])

    # Extract homogeneous weight α algebraically
    alpha = _get_e0_coeff(mv)

    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / alpha, y=y / alpha, z=z / alpha)
```

### 4.2 Apply normalization in `_point_from_trivector`

```python
def _point_from_trivector(mv: MV) -> Point | Direction:
    """Extract a Point or Direction from a grade‑3 trivector.

    The dual of a point trivector is ``x·e₁ + y·e₂ + z·e₃ + α·e₀``
    for a finite point, or ``x·e₁ + y·e₂ + z·e₃`` for a direction.
    """
    dual = -_pga3_dual(mv)  # grade‑1 vector; negate for correct sign

    x = float(dual[E1])
    y = float(dual[E2])
    z = float(dual[E3])

    # Extract homogeneous weight α algebraically
    alpha = _get_e0_coeff(dual)

    if abs(alpha) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x / alpha, y=y / alpha, z=z / alpha)
```

### 4.3 Test additions

```python
def test_analyze_point_centroid_normalization(basis_pga3):
    """Weighted sum of two points should return centroid."""
    P = basis_pga3.point(1, 0, 0)     # 1·e₁ + e₀  → α=1
    Q = basis_pga3.point(3, 0, 0)     # 3·e₁ + e₀  → α=1
    C = P + Q                          # IPNS: 4·e₁ + 2·e₀ → α=2
    result = analyze_entity(C, opns=False)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(2.0)   # 4/2
    assert result.y == pytest.approx(0.0)
    assert result.z == pytest.approx(0.0)

def test_analyze_point_scaled_mv(basis_pga3):
    """A scaled point MV should still return the correct position."""
    P = basis_pga3.point(5, 6, 7)     # unit weight
    scaled = P * 3.0                   # 3·(5·e₁ + 6·e₂ + 7·e₃ + e₀)
    result = analyze_entity(scaled, opns=False)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(5.0)
    assert result.y == pytest.approx(6.0)
    assert result.z == pytest.approx(7.0)

def test_analyze_point_unit_weight_still_works(basis_pga3):
    """Unit‑weight points (the common case) must still work."""
    P = basis_pga3.point(1, 2, 3)
    result = analyze_entity(P, opns=False)
    assert isinstance(result, Point)
    assert result.x == pytest.approx(1.0)
    assert result.y == pytest.approx(2.0)
    assert result.z == pytest.approx(3.0)
```

**Dependencies:** Phase 4 uses `_get_e0_coeff` from Phase 1. It touches
`_point_or_direction_from_ipns` and `_point_from_trivector`. Phase 2.2 fixes
a bug in the caller (`_analyze_entity_ipns`) but the two changes are
independent — normalization is correct regardless of whether the IPNS
grade‑3 routing is fixed.

---

## Phase 5 — Add GeneralRotor Support and Missing Creation Functions

### 5.1 Add `create_general_rotor` to `create_pga3.py`

**Reference:** N3 implementation in `create_n3.py:create_general_rotor`.

A general rotor is $G = T \cdot R \cdot \tilde{T}$ — a translator‑conjugated rotor that rotates about a displaced axis not passing through the origin. It has grades 0 and 2 (no grade‑4 term).

```python
def create_general_rotor(basis: Algebra, rotor: Rotor, translator: Translator) -> MV:
    """General rotor: rotation about an axis NOT passing through the origin.

    ``G = T · R · T̃`` — the conjugation cancels the translator's effect on
    position, leaving a pure rotation about a displaced axis.

    The result has grades {0, 2} (scalar + bivector), distinguishing it from
    a Motor which also has a grade‑4 term.
    """
    t_mv = create_translator(
        basis, translator.vector.x, translator.vector.y, translator.vector.z
    )
    r_mv = create_rotor(basis, rotor.angle, rotor.axis)
    return t_mv.gp(r_mv).gp(t_mv.rev())
```

### 5.2 Add `GeneralRotor` recognition to `analyze_operator`

**File:** `py/pytanga/geometry/analysis_pga3.py`, function `analyze_operator`

**Current return type:** `Reflection | Rotor | Translator | Motor`

**Change:** Add `GeneralRotor` to the return type. Extend the 2‑factor classification to detect the mixed null/Euclidean case that distinguishes a GeneralRotor from a pure Rotor or pure Translator.

A GeneralRotor arises when a 2‑factor versor has **both** null and Euclidean components in its grade‑2 part, but **no** grade‑4 part. Since 2‑factor versors never have grade‑4 terms (products of exactly 2 grade‑1 reflectors), any 2‑factor versor with both null and Euclidean components is a GeneralRotor.

```python
from .operators import GeneralRotor  # add to imports

# In analyze_operator, modify the 2-factor branch:
if n == 2:
    if any(has_null_flags) and not all(has_null_flags):
        # Mixed null + Euclidean → GeneralRotor
        return _general_rotor_from_versor(mv)
    elif any(has_null_flags):
        return _translator_from_versor(mv)
    else:
        return _rotor_from_factors(factors[0], factors[1])

# Add new extraction function:
def _general_rotor_from_versor(mv: MV) -> GeneralRotor:
    """Extract a GeneralRotor from a 2‑factor versor with mixed components.

    G = T·R·T̃ has both Euclidean and null bivector parts but no grade-4.
    The Euclidean part gives the rotation angle and axis; the null part
    encodes the displacement of the rotation axis from the origin.
    """
    # Extract rotor from Euclidean bivector components
    bx = float(mv[E23])
    by = float(mv[E13])
    bz = float(mv[E12])
    b_norm = math.sqrt(bx * bx + by * by + bz * bz)

    if b_norm < 1e-15:
        raise ValueError("GeneralRotor has zero Euclidean bivector part")

    scal = float(mv[0])
    if abs(scal) < 1e-15:
        raise ValueError("GeneralRotor has zero scalar component")

    angle = 2.0 * math.atan2(b_norm, scal)
    axis = Direction(bx / b_norm, by / b_norm, bz / b_norm)

    # Extract translator from null bivector components
    dx = -2.0 * float(mv[9]) / scal   # e1∧ep
    dy = -2.0 * float(mv[10]) / scal   # e2∧ep
    dz = -2.0 * float(mv[12]) / scal   # e3∧ep

    return GeneralRotor(
        rotor=Rotor(angle=angle, axis=axis),
        translator=Translator(vector=Direction(dx, dy, dz)),
    )
```

### 5.3 Add missing creation functions

```python
def create_reflection_line(basis: Algebra, direction: Direction) -> MV:
    """Reflection on a line through the origin.

    In PGA3, this is a bivector ``d∧e₀`` (grade 2).
    """
    return basis.multivector({
        9: direction.x, 17: direction.x,   # e1∧ep, e1∧em
        10: direction.y, 18: direction.y,   # e2∧ep, e2∧em
        12: direction.z, 20: direction.z,   # e3∧ep, e3∧em
    })

def create_reflection_origin(basis: Algebra) -> MV:
    """Reflection about the origin.

    In PGA3, this is the trivector ``e₁∧e₂∧e₃`` (grade 3).
    """
    if hasattr(basis, "e1"):
        return basis.e1.op(basis.e2).op(basis.e3)
    return basis.multivector({E123: 1.0}).grade(3)
```

### 5.4 Update dispatchers

**`create.py`:** Add `GeneralRotor`, `ReflectionLine`, `ReflectionOrigin` cases to `create_operator`.

**`analysis.py`:** `analyze_operator` already routes to `analysis_pga3.analyze_operator` which now handles all types.

**Test additions:**
- `test_create_general_rotor_round_trip` — Create via `create_operator(basis_pga3, GeneralRotor(...))`, analyze → reconstructs same parameters.
- `test_general_rotor_rotates_about_displaced_axis` — Apply general rotor to a point off the axis, verify it rotates around the displaced axis (not the origin).
- `test_create_reflection_line_round_trip` — Create → analyze → `ReflectionLine` with matching direction.
- `test_create_reflection_origin_round_trip` — Create → analyze → `ReflectionOrigin`.

**Dependencies:** Phase 5.2 (analysis recognition) depends on Phase 4 (weight normalization) because the translator extraction in `_general_rotor_from_versor` divides by the scalar part — the same scale‑sensitive pattern as the existing translator extractor. Phase 5.1 (creation) is independent and can be implemented before analysis.

---

## Phase 6 — Hardened `create_space`

**File:** `py/pytanga/geometry/create_pga3.py`, function `create_space`

**Problem:** Uses manual blade ID assignment that could break if the blade ID scheme changes, and constructs the 4D pseudoscalar via a fragile grade‑4 extraction.

**Fix:** Replace with the algebraic construction using named basis vectors (already available on the algebra instance after Phase 1):

```python
def create_space(basis: Algebra, *, scale: float = 1.0, opns: bool = True) -> MV:
    """PGA3 Space: ``scale · e₁ ∧ e₂ ∧ e₃ ∧ e₀``.

    *opns=True* (default): grade‑4 blade.
    *opns=False* (IPNS): grade‑0 scalar (dual of the pseudoscalar).
    """
    opns_mv = basis.e1.op(basis.e2).op(basis.e3).op(_get_e0(basis)) * scale

    if not opns:
        return opns_mv.dual()  # IPNS: scalar
    return opns_mv
```

**Test:** Existing `test_space_round_trip` validates correctness. The refactored implementation must produce the same result.

**Dependencies:** None — independent of all other phases.

---

## Summary of Changes (ordered by implementation phase)

| Phase | Files | Changes | New tests | Risk |
|-------|-------|---------|-----------|------|
| 1 | `basis/pga3.py` (rewrite), **NEW** `_pga3_utils.py`, `create_pga3.py`, `analysis_pga3.py` | Standalone `BasisPGA3` with `e0`/`e0_recip` (no `einf`/`eo`); shared utils | None — existing suite must pass | Medium — rewrites `BasisPGA3` |
| 2.1 | `create_pga3.py:create_direction` | Fix OPNS form via `_pga3_dual(ipns)` | +2 | None — fixes a bug |
| 2.2 | `analysis_pga3.py:_analyze_entity_ipns` | Fix grade‑3 path to dualize before plane extraction | +1 | None — fixes a bug |
| 3.1 | `analysis_pga3.py:_line_from_bivector` | Add blade‑ness check before factorization | +1 | None — defensive |
| 3.2 | `analysis_pga3.py:_line_origin_from_planes` | Remove dead code, keep corrected Cramer's rule | None | Low — behavior unchanged |
| 4 | `analysis_pga3.py:_point_or_direction_from_ipns`, `_point_from_trivector` | Add algebraic weight extraction and normalization via `_get_e0_coeff` | +3 | Medium — changes point analysis behavior |
| 5.1 | `create_pga3.py` | Add `create_general_rotor` | +1 | Low — new function |
| 5.2 | `analysis_pga3.py:analyze_operator` | Add `GeneralRotor` recognition | +1 | Low — extends classification |
| 5.3 | `create_pga3.py` | Add `create_reflection_line`, `create_reflection_origin` | +2 | Low — new functions |
| 5.4 | `create.py` | Wire new operator types into dispatcher | None | Low |
| 6 | `create_pga3.py:create_space` | Replace manual blade IDs with algebraic construction | None | Low — behavior unchanged |

---

## Dependency graph

```
Phase 1 (standalone BasisPGA3 with e0/e0_recip + shared utils) ── FIRST
    ↓
Phase 2.1 + Phase 2.2 (critical bugs, either order)
    ↓
Phase 3.1 + Phase 3.2 (defensive improvements, either order)
    ↓
Phase 4 (weight normalization — uses _get_e0_coeff from Phase 1)
    ↓
Phase 5.1 + Phase 5.3 + Phase 6 (creation functions — independent)
    ↓
Phase 5.2 (GeneralRotor analysis — depends on Phase 4 for scale handling)
    ↓
Phase 5.4 (wiring dispatchers)
```

### Rationale for ordering

1. **Basis rewrite first.** Phase 1 makes `BasisPGA3` standalone with `e0`/`e0_recip` and no `einf`/`eo`. All other phases depend on `_pga3_utils` which sources blade IDs and the dual from `BasisPGA3`.

2. **Bug fixes next.** Phase 2 fixes broken functionality. Everything else builds on correct behavior.

3. **Defensive checks next.** Phase 3 adds validation without changing behavior.

4. **Normalization before new analysis.** Phase 4's weight normalization must be in place before Phase 5.2 adds GeneralRotor analysis.

5. **Creation functions are independent.** Phase 5.1/5.3 and Phase 6 only add or modify creation code — no dependency on analysis changes.

6. **Dispatchers last.** Phase 5.4 wires everything together after all functions exist.

---

## Test Plan

After all phases are implemented, run the full PGA3 test suite:

```bash
cd py && python -m pytest tests/test_geometry_pga3.py -v
```

**New tests added:** ~12  
**Expected:** All existing tests pass + all new tests pass.

| Phase | New test |
|-------|----------|
| 2.1 | `test_create_direction_opns_is_ideal` |
| 2.1 | `test_create_direction_opns_round_trip` |
| 2.2 | `test_analyze_ipns_plane_round_trip` |
| 3.1 | `test_line_non_simple_bivector_raises` |
| 4 | `test_analyze_point_centroid_normalization` |
| 4 | `test_analyze_point_scaled_mv` |
| 4 | `test_analyze_point_unit_weight_still_works` |
| 5.1 | `test_create_general_rotor_round_trip` |
| 5.1 | `test_general_rotor_rotates_about_displaced_axis` |
| 5.3 | `test_create_reflection_line_round_trip` |
| 5.3 | `test_create_reflection_origin_round_trip` |