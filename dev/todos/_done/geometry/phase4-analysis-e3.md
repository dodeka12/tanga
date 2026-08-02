# Phase 4: E3 Entity and Operator Analysis

**File:** `py/pytanga/geometry/analysis_e3.py`

**Goal:** Implement entity and operator analysis for Euclidean 3D algebra (G(3,0)).

---

## 1. E3 Algebra Overview

| Property | Value |
|----------|-------|
| Basis class | `BasisE3` |
| Dimension | 3 |
| Signature | 0 |
| Blade count | 8 (2³) |
| Entity grades | 1 (Point), 2 (Plane), 3 (Space) |
| Operator grades | 1 (Reflection), {0,2} (Rotor) |

E3 is the simplest algebra: all entities are pure-grade blades.

### Blade ID Reference

| Blade | ID | Grade |
|-------|----|-------|
| 1 (scalar) | 0 | 0 |
| e1 | 1 | 1 |
| e2 | 2 | 1 |
| e3 | 4 | 1 |
| e12 | 3 | 2 |
| e31 | 5 | 2 |
| e23 | 6 | 2 |
| e123 (I) | 7 | 3 |

---

## 2. Entity Detection — Using `blade_factorize()`

### 2.1 Strategy

1. Determine the grade of the MV.
2. Use `mv.grade(k).blade_factorize()` to get factor vectors.
3. Extract Euclidean (x,y,z) coordinates from the factor vectors.

| Entity | Grade | # Factors | Factor Meaning |
|--------|-------|-----------|----------------|
| Point | 1 | 1 | Position vector `x·e1 + y·e2 + z·e3` |
| Plane | 2 | — | Dualize to grade 1, 1 factor = normal vector |
| Space | 3 | — | Pseudoscalar (no parameters needed) |

### 2.2 Plane Detection

In E3, a plane through the origin is represented as a bivector:
`nx·e23 + ny·e31 + nz·e12`

To extract: dualize the bivector (IP with I⁻¹) to get the normal vector (grade 1),
then factorize to get the normalized normal.

For offset planes: the IPNS representation `n + d·I` (grade-1 + pseudoscalar) produces
an offset after dualization. The offset `d` is the pseudoscalar component. This is
an extension for later.

---

## 3. Operator Detection — Using `blade_factorize_versor()`

### 3.1 Strategy

1. Factorize the versor: `scale, factors = mv.blade_factorize_versor()`.
2. Classify by number of factors:
   - **1 factor** → `Reflection` (the factor IS the reflector plane normal)
   - **2 factors** → `Rotor` (2 reflection planes = rotation)

### 3.2 Rotor Decomposition

The two reflector factors `n1, n2` give the rotation:
- **Angle:** `θ = 2·acos(n1·n2)`
- **Axis:** `n1 ∧ n2` (bivector, extract e23/e31/e12 components)

---

## 4. Implementation

```python
# py/pytanga/geometry/analysis_e3.py

"""E3-specific entity and operator analysis.

Uses blade_factorize() and blade_factorize_versor() for decomposition.
"""

import math

from pytanga.algebra._mv import MV
from pytanga.geometry.entities import Direction, Plane, Point, Space


# --- Entity Detection ---

def analyze_entity(mv: MV) -> Point | Plane | Space:
    """Analyze an MV in E3 as a geometric entity.

    E3 entities are pure-grade blades:
      - Grade 1 → Point
      - Grade 2 → Plane (dualize to get normal)
      - Grade 3 → Space (pseudoscalar)
    """
    if mv.is_zero:
        raise ValueError("Zero MV does not represent a geometric entity")
    if mv.is_scalar:
        raise ValueError("Scalar MV does not represent a geometric entity")

    grades = _get_grades(mv)
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in E3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _point_from_factor(mv)
    elif max_grade == 2:
        return _plane_from_factor(mv)
    elif max_grade == 3:
        return Space()
    else:
        raise ValueError(f"Unexpected grade {max_grade} in E3")


def _point_from_factor(mv: MV) -> Point:
    """Factorize grade-1 blade → single vector → Point."""
    grade1 = mv.grade(1)
    factors = grade1.blade_factorize()
    n = factors[0]
    return Point(
        x=float(n[1]),   # e1
        y=float(n[2]),   # e2
        z=float(n[4]),   # e3
    )


def _plane_from_factor(mv: MV) -> Plane:
    """Dualize grade-2 blade → factorize normal → Plane."""
    grade2 = mv.grade(2)
    i_inv = mv._alg.I.inv()
    normal_mv = grade2.ip(i_inv)  # dual = IP with I^{-1}
    factors = normal_mv.blade_factorize()
    n = factors[0]

    nx = float(n[1])
    ny = float(n[2])
    nz = float(n[4])
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length == 0:
        raise ValueError("Zero normal, not a valid plane")

    return Plane(
        point=Point(0, 0, 0),  # plane through origin
        normal=Direction(nx / length, ny / length, nz / length),
    )


# --- Entity Construction ---

def make_point(alg, x: float, y: float, z: float) -> MV:
    """Create an E3 point: x·e1 + y·e2 + z·e3."""
    return alg.multivector({1: x, 2: y, 4: z})


def make_plane(alg, normal: Direction, offset: float = 0.0) -> MV:
    """Create an E3 plane MV (bivector form)."""
    return alg.multivector({
        6: normal.x,   # e23
        5: normal.y,   # e31
        3: normal.z,   # e12
    })


# --- Operator Detection ---

def analyze_operator(mv: MV):
    """Analyze an MV in E3 as a versor/operator.

    Classification by factor count:
      - 1 factor  → Reflection
      - 2 factors → Rotor
    """
    from pytanga.geometry.operators import Reflection, Rotor

    if mv.is_zero:
        raise ValueError("Zero MV is not a valid versor")

    scale, factors = mv.blade_factorize_versor()

    if len(factors) == 1:
        return _reflection_from_factor(factors[0])
    elif len(factors) == 2:
        return _rotor_from_factors(factors[0], factors[1])
    else:
        raise ValueError(f"Versor has {len(factors)} factors — unexpected for E3")


def _reflection_from_factor(n: MV) -> Reflection:
    """A single factor vector IS the reflection plane normal."""
    return Reflection(
        normal=Direction(float(n[1]), float(n[2]), float(n[4]))
    )


def _rotor_from_factors(n1: MV, n2: MV) -> Rotor:
    """Two reflection planes → rotation.

    R = n1·n2 = cos(θ/2) + sin(θ/2)·B
    angle = 2·acos(n1·n2), axis = n1 ∧ n2
    """
    from pytanga.geometry.operators import Rotor

    n1_dot_n2 = float(n1.sp(n2))
    angle = 2.0 * math.acos(max(-1.0, min(1.0, n1_dot_n2)))

    bivector = n1.op(n2)
    bx = float(bivector[6])  # e23
    by = float(bivector[5])  # e31
    bz = float(bivector[3])  # e12

    bv_norm = math.sqrt(bx * bx + by * by + bz * bz)
    if bv_norm < 1e-15:
        axis = Direction(1, 0, 0)  # identity or 180°
    else:
        axis = Direction(bx / bv_norm, by / bv_norm, bz / bv_norm)

    return Rotor(angle=angle, axis=axis)


# --- Operator Construction ---

def make_rotor(alg, angle: float, axis: Direction) -> MV:
    """Create an E3 rotor from angle and axis."""
    half_angle = angle / 2.0
    return alg.multivector({
        0: math.cos(half_angle),
        6: math.sin(half_angle) * axis.x,   # e23
        5: math.sin(half_angle) * axis.y,   # e31
        3: math.sin(half_angle) * axis.z,   # e12
    })


# --- Helpers ---

def _get_grades(mv: MV) -> set[int]:
    """Get set of grades present in the MV."""
    grades = set()
    for blade_id in mv.blade_ids():
        grades.add(blade_id.bit_count())
    return grades
```

---

## 5. Implementation Steps

1. Create `py/pytanga/geometry/analysis_e3.py`.
2. Implement `analyze_entity()`: Point (grade 1), Plane (grade 2 → dual), Space (grade 3).
3. Implement `analyze_operator()`: Reflection (1 factor), Rotor (2 factors).
4. Implement factory functions: `make_point()`, `make_plane()`, `make_rotor()`.

## 6. Verification Checklist

- [ ] `analyze_entity()` correctly identifies Point, Plane, Space
- [ ] `analyze_operator()` correctly identifies Reflection, Rotor
- [ ] Round-trip: `make_point(x,y,z)` → `analyze_entity()` returns same Point
- [ ] Round-trip: `make_rotor(angle, axis)` → `analyze_operator()` returns same Rotor
- [ ] Edge cases: identity rotor (2 parallel reflectors), zero-length vectors