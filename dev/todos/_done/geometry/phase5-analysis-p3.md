# Phase 5: P3 Entity and Operator Analysis

**File:** `py/pytanga/geometry/analysis_p3.py`

**Goal:** Implement entity and operator analysis for Projective 3D algebra (G(4,0)).

---

## 1. P3 Algebra Overview

| Property | Value |
|----------|-------|
| Basis class | `BasisP3` |
| Dimension | 4 |
| Signature | 0 |
| Blade count | 16 (2⁴) |
| Entity grades | 1 (Point/Direction), 2 (Line), 3 (Plane), 4 (Space) |
| Operator grades | 1 (Reflection), {0,2} (Rotor) |

P3 uses homogeneous coordinates where the 4th basis vector `e4` provides the
projective embedding.

### Blade ID Reference

| Blade | ID | Grade |
|-------|----|-------|
| 1 (scalar) | 0 | 0 |
| e1 | 1 | 1 |
| e2 | 2 | 1 |
| e3 | 4 | 1 |
| e4 | 8 | 1 |
| e12 | 3 | 2 |
| e31 | 5 | 2 |
| e23 | 6 | 2 |
| e41 | 9 | 2 |
| e42 | 10 | 2 |
| e43 | 12 | 2 |
| e123 | 7 | 3 |
| e234 | 14 | 3 |
| e314 | 13 | 3 |
| e124 | 11 | 3 |
| e1234 (I) | 15 | 4 |

---

## 2. Entity Detection — Using `blade_factorize()`

### 2.1 Strategy

Same approach as E3: factorize the grade-k blade into k grade-1 factor vectors,
then extract Euclidean parameters from the factor vectors.

| Entity | Grade | # Factors | Factor Meaning |
|--------|-------|-----------|----------------|
| Point | 1 | 1 | Homogeneous point, e4 coefficient ≠ 0 |
| Direction | 1 | 1 | Homogeneous point, e4 coefficient = 0 (ideal) |
| Line | 2 | 2 | Factor[0] = origin point, Factor[1] = direction |
| Plane | 3 | 3 | Three points on the plane → IPNS trivector |
| Space | 4 | — | Pseudoscalar |

### 2.2 Point/Direction Detection

A grade-1 blade in P3 is `x·e1 + y·e2 + z·e3 + w·e4`:
- If `w ≠ 0` → finite `Point` at `(x/w, y/w, z/w)`
- If `w = 0` → `Direction` vector (ideal point at infinity)

### 2.3 Line Decomposition

A line is the outer product of two points: `origin_point ∧ direction_point`.
Factorizing the grade-2 blade gives two factor vectors:
- Factor[0] = origin point (homogeneous, e4 = 1)
- Factor[1] = direction point (homogeneous, e4 = 0)

Extract Euclidean coordinates and use `_point_from_factor` on each factor.

Alternatively, follow the C++ `TryGetLineComponents()` approach:
- Read bivector components to get direction (e23, e31, e12) and moment (e41, e42, e43).
- Direction normalization and cross product for origin.

### 2.4 Plane Decomposition

A plane is the outer product of three points: factorize → 3 factors = 3 points.
The dual of the plane trivector gives `normal + offset·e4`.

Alternatively, follow the C++ approach from `CBasisP3::_Init()`:
- Normal from e123 and e4-containing trivector components.
- Offset from the e123 coefficient after normalization.

---

## 3. Operator Detection — Using `blade_factorize_versor()`

Same factor-count-based classification as E3:
- **1 factor** → `Reflection`
- **2 factors** → `Rotor`

The rotor formula is identical to E3 since both algebras use the same rotor basis
{scalar, e23, e31, e12}.

---

## 4. Implementation Skeleton

```python
# py/pytanga/geometry/analysis_p3.py

"""P3-specific entity and operator analysis."""

import math

from pytanga.algebra._mv import MV
from pytanga.geometry.entities import Direction, Line, Plane, Point, Space


# --- Entity Detection ---

def analyze_entity(mv: MV) -> Point | Direction | Line | Plane | Space:
    """Analyze an MV in P3 as a geometric entity."""
    ...


def _point_or_direction_from_factor(mv: MV) -> Point | Direction:
    """Grade-1 blade → Point or Direction by e4 weight."""
    factor = mv.grade(1).blade_factorize()[0]
    x = float(factor[1])  # e1
    y = float(factor[2])  # e2
    z = float(factor[4])  # e3
    w = float(factor[8])  # e4 (homogeneous weight)
    if abs(w) < 1e-15:
        return Direction(x=x, y=y, z=z)
    return Point(x=x/w, y=y/w, z=z/w)


def _line_from_factors(mv: MV) -> Line:
    """Grade-2 blade → 2 factors = origin point + direction."""
    factors = mv.grade(2).blade_factorize()
    # Factor[0] = origin (homogeneous point)
    # Factor[1] = direction (ideal point)
    ...


def _plane_from_factors(mv: MV) -> Plane:
    """Grade-3 blade → 3 factors = 3 points on the plane."""
    ...


# --- Entity Construction ---

def make_point(alg, x: float, y: float, z: float) -> MV:
    """Create a P3 point: x·e1 + y·e2 + z·e3 + e4."""
    return alg.multivector({1: x, 2: y, 4: z, 8: 1})


def make_direction(alg, x: float, y: float, z: float) -> MV:
    """Create a P3 direction: x·e1 + y·e2 + z·e3."""
    return alg.multivector({1: x, 2: y, 4: z})


def make_line(alg, origin: Point, direction: Direction) -> MV:
    """Create a P3 line: origin ∧ direction."""
    p = make_point(alg, origin.x, origin.y, origin.z)
    d = make_direction(alg, direction.x, direction.y, direction.z)
    return p.op(d)


# --- Operator Detection ---

def analyze_operator(mv: MV):
    """Analyze an MV in P3 as a versor (Reflection or Rotor)."""
    ...


def make_rotor(alg, angle: float, axis: Direction) -> MV:
    """Create a P3 rotor from angle and axis."""
    # Same formula as E3
    ...
```

---

## 5. Implementation Steps

1. Create `py/pytanga/geometry/analysis_p3.py`.
2. Implement `analyze_entity()`: Point/Direction (grade 1), Line (grade 2), Plane (grade 3), Space (grade 4).
3. Study C++ `TryPointToVec3()` and `TryGetLineComponents()` for correct decomposition formulas.
4. Implement `analyze_operator()`: Reflection (1 factor), Rotor (2 factors).
5. Implement factory functions.

## 6. Verification Checklist

- [ ] `analyze_entity()` correctly identifies Point, Direction, Line, Plane, Space
- [ ] Point extraction normalizes by e4 weight
- [ ] Direction detected when e4 weight ≈ 0
- [ ] `analyze_operator()` correctly identifies Reflection, Rotor
- [ ] Round-trip: `make_point(x,y,z)` → `analyze_entity()` returns same Point
- [ ] Round-trip: `make_line(origin, dir)` → `analyze_entity()` returns same Line