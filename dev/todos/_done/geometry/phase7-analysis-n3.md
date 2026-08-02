# Phase 7: N3 Entity and Operator Analysis

**File:** `py/pytanga/geometry/analysis_n3.py`

**Goal:** Implement entity and operator analysis for full Conformal Geometric Algebra
N3 (G(5, 0b10000)), using both null vectors `einf` and `eo`.

---

## 1. N3 Algebra Overview

| Property | Value |
|----------|-------|
| Basis class | `BasisN3` (not `BasisPGA3`) |
| Dimension | 5 |
| Signature | 0b10000 |
| Blade count | 32 (2⁵) |
| Null vectors | `einf = ep + em`, `eo = 0.5·em - 0.5·ep` |
| Geometric model | Full Conformal |

This is the richest algebra with 7 entity types and 8 operator types.

### Blade ID Reference (5D basis)

| Blade | ID | Grade |
|-------|----|-------|
| 1 (scalar) | 0 | 0 |
| e1 | 1 | 1 |
| e2 | 2 | 1 |
| e3 | 4 | 1 |
| ep | 8 | 1 |
| em | 16 | 1 |
| e12 | 3 | 2 |
| e31 | 5 | 2 |
| e23 | 6 | 2 |
| e1p (e1i) | 9 | 2 |
| e2p (e2i) | 10 | 2 |
| e3p (e3i) | 12 | 2 |
| e1m (e1o) | 17 | 2 |
| e2m (e2o) | 18 | 2 |
| e3m (e3o) | 20 | 2 |
| epm (E) | 24 | 2 |
| ... | (etc) | ... |
| e123pm (I) | 31 | 5 |

Note: `einf = ep + em` maps to blade IDs {8, 16}, and `eo = 0.5·em - 0.5·ep`
also maps to {8, 16} but with different coefficients.

---

## 2. Entity Coverage

| Entity | Grade | # Factors | Detection |
|--------|-------|-----------|-----------|
| Point | 1 | 1 | SP(point, einf) ≠ 0 (finite); SP(point, einf) = 0 (ideal) |
| Direction | 1 | 1 | Pure Euclidean vector, no einf/eo |
| Point Pair | 2 | 2 | 2 conformal point factors |
| Line | 3 | 3 | 2 points + einf |
| Circle | 3 | 3 or 10 blades | Contains e123, spans both i and o bivectors |
| Plane | 4 | 4 | 3 points + einf (IPNS: no e123o) |
| Sphere | 4 | 4 or 5 blades | 4 points (IPNS: contains e123o) |
| Space | 5 | — | Pseudoscalar |

### 2.1 Distinguishing Line vs Circle (both grade 3)

Both lines and circles are grade-3 blades in N3. They must be distinguished
by blade composition:

| | Line (IPNS) | Circle (IPNS) |
|---|---|---|
| Contains `eio` components | ✓ | ✓ |
| Contains `e123` | ✗ | ✓ |
| Blade basis size | 6 | 10 |

**Algorithm:** After factorization, check if the blade contains `e123` (blade ID 7).
If yes → Circle; if no → Line.

Alternatively, use the C++ blade mask approach:
- `BasisLine` = {e23i, e31i, e12i, e1io, e2io, e3io} (6 blades)
- `BasisCircle` = {e23i, e31i, e12i, e23o, e31o, e12o, e1io, e2io, e3io, e123} (10 blades)

### 2.2 Distinguishing Plane vs Sphere (both grade 4)

| | Plane (IPNS) | Sphere (IPNS) |
|---|---|---|
| Contains `e123i` | ✓ | ✓ |
| Contains `e123o` | ✗ | ✓ |
| Blade basis size | 4 | 5 |

**Algorithm:** Check presence of `e123o` (blade ID combining e123 with em=16 → 7|16=23).
If present → Sphere; else → Plane.

---

## 3. Operator Coverage

| Operator | # Factors | Blade Composition | Detection |
|----------|-----------|-------------------|-----------|
| Reflection | 1 | Euclidean-only (no einf/eo) | Single grade-1 factor without null components |
| Inversion | 1 | Contains eo | Single grade-1 factor with eo component |
| Rotor | 2 | Both Euclidean (no einf/eo) | Two grade-1 factors, grades {0,2} |
| Translator | 2 | Factors involve einf | Two grade-1 factors with einf component |
| Dilator | 2 | Factors involve E = einf∧eo | Two grade-1 factors with E component |
| General Dilator | 2 | Factors involve einf + E | Mixed einf/E content |
| Motor | 4 | 2 Euclidean + 2 einf | Rotor × Translator in factor form |
| General Rotor | 4 | Rotor + ei-bivectors | Rotor basis + translator basis |

### 3.1 Single-Reflector Classification

For a single factor vector `n`:
- Has NO eo component → `Reflection`
- Has eo component → `Inversion`

Check: if `n[8]` (ep) and `n[16]` (em) represent an `eo`-weighted combination
(the C++ `BasisInversion` mask includes eo while `BasisReflection` does not).

### 3.2 Double-Reflector Classification

For two factor vectors:
- Both Euclidean (no null components) → `Rotor`
- Both involve einf but not eo → `Translator`
- Both involve E = einf∧eo → `Dilator` (requires checking eo component content)
- Mixed einf + E → `GeneralDilator`

### 3.3 Quad-Reflector Classification

For four factor vectors:
- Standard composition → `Motor` (2 Euclidean rotors + 2 translators)
- Rotor + ei-bivectors without e123i → `GeneralRotor`

---

## 4. Point Extraction (Reference: C++ `TryPointToVec3`)

The C++ `CBasisN3::TryPointToVec3()` extracts (x,y,z) from a conformal point:

```cpp
// From BasisN3.h
SP(fValueEo, wPnt, m_wEinf);  // scalar product with einf
fValueEo = -fValueEo;         // negate → gives eo weight

if (wPnt.IsZero(fValueEo))
    return false;              // ideal point (direction at infinity)

wPnt.GetValueBlade(fValue, TBlade(uE1));
vPnt3d.x = TValue(fValue) / fValueEo;  // x / (-SP(point, einf))

wPnt.GetValueBlade(fValue, TBlade(uE2));
vPnt3d.y = TValue(fValue) / fValueEo;

wPnt.GetValueBlade(fValue, TBlade(uE3));
vPnt3d.z = TValue(fValue) / fValueEo;
```

The `einf` blade in `BasisN3` is the combination `{ep, em}` with coefficients
`{1, 1}` for ep and em respectively. The scalar product `SP(point, einf)` extracts
the negative of the eo coefficient.

---

## 5. Implementation Skeleton

```python
# py/pytanga/geometry/analysis_n3.py

"""N3-specific entity and operator analysis (full conformal, two null vectors).

N3 uses both einf and eo null vectors, enabling the full conformal model
with PointPair, Circle, Sphere, and all 8 operator types.
"""

import math

from pytanga.algebra._mv import MV
from pytanga.geometry.entities import (
    Circle, Direction, Line, Plane, Point, PointPair, Space, Sphere,
)
from pytanga.geometry.operators import (
    Dilator, GeneralDilator, GeneralRotor, Inversion, Motor,
    Reflection, Rotor, Translator,
)


# --- Entity Detection ---

def analyze_entity(mv: MV):
    """Analyze an MV in N3 as a geometric entity.

    Uses grade analysis + blade_factorize() for decomposition.
    Distinguishes Line/Circle and Plane/Sphere by blade composition.
    """
    if mv.is_zero:
        raise ValueError("Zero MV is not a geometric entity")

    grades = _get_grades(mv)
    # N3 entities in IPNS can be multi-grade (e.g. mixed grade for offset planes)
    # For now assume pure-grade IPNS representation
    if len(grades) > 1:
        raise ValueError(f"Mixed-grade MV in N3: grades={grades}")

    max_grade = max(grades)

    if max_grade == 1:
        return _decompose_point_n3(mv)
    elif max_grade == 2:
        return _decompose_point_pair(mv)
    elif max_grade == 3:
        return _decompose_line_or_circle(mv)
    elif max_grade == 4:
        return _decompose_plane_or_sphere(mv)
    elif max_grade == 5:
        return Space()
    else:
        raise ValueError(f"Unexpected grade {max_grade} in N3")


def _decompose_point_n3(mv: MV) -> Point | Direction:
    """Extract point from grade-1 N3 blade.

    N3 point: x·e1 + y·e2 + z·e3 + 0.5*(r²-1)*ep + 0.5*(r²+1)*em

    Uses the C++ TryPointToVec3 approach:
      f_eo = -SP(point, einf)
      x = coeff(e1) / f_eo (if f_eo ≠ 0)
    """
    alg = mv._alg
    # einf = ep + em, construct it or get from basis
    einf = _make_einf(alg)

    f_eo = -float(mv.sp(einf))

    if abs(f_eo) < 1e-15:
        # Direction at infinity (ideal point)
        return Direction(
            x=float(mv[1]),
            y=float(mv[2]),
            z=float(mv[4]),
        )

    return Point(
        x=float(mv[1]) / f_eo,
        y=float(mv[2]) / f_eo,
        z=float(mv[4]) / f_eo,
    )


def _decompose_point_pair(mv: MV) -> PointPair:
    """Grade-2 blade → 2 factor vectors = 2 conformal points."""
    grade2 = mv.grade(2)
    factors = grade2.blade_factorize()
    p1 = _factor_to_point_n3(factors[0], mv._alg)
    p2 = _factor_to_point_n3(factors[1], mv._alg)
    return PointPair(point_a=p1, point_b=p2)


def _decompose_line_or_circle(mv: MV):
    """Grade-3 blade → check for e123 to distinguish Line from Circle."""
    # Check if blade contains e123 (ID 7)
    has_e123 = abs(float(mv[7])) > 1e-15
    if has_e123:
        return _decompose_circle(mv)
    else:
        return _decompose_line(mv)


def _decompose_line(mv: MV) -> Line:
    """Grade-3 blade → 3 factors = 2 points + einf."""
    factors = mv.grade(3).blade_factorize()
    # Separate point factors from einf factor
    points = [f for f in factors if _is_conformal_point(f)]
    if len(points) != 2:
        raise ValueError(f"Expected 2 point factors for line, got {len(points)}")
    p1 = _factor_to_point_n3(points[0], mv._alg)
    p2 = _factor_to_point_n3(points[1], mv._alg)
    return Line(
        origin=p1,
        direction=Direction(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z),
    )


def _decompose_circle(mv: MV) -> Circle:
    """Grade-3 blade containing e123 → Circle."""
    ...


def _decompose_plane_or_sphere(mv: MV):
    """Grade-4 blade → check for e123o to distinguish Plane from Sphere."""
    # e123 = ID 7, em = ID 16, so e123∧em has blade ID 7|16 = 23
    has_e123o = abs(float(mv[23])) > 1e-15
    if has_e123o:
        return _decompose_sphere(mv)
    else:
        return _decompose_plane(mv)


def _decompose_plane(mv: MV) -> Plane:
    """Grade-4 blade without e123o → Plane."""
    ...


def _decompose_sphere(mv: MV) -> Sphere:
    """Grade-4 blade with e123o → Sphere."""
    ...


# --- Operator Detection ---

def analyze_operator(mv: MV):
    """Analyze an MV in N3 as a versor/operator.

    Uses blade_factorize_versor() to get (scale, [reflector_factors]).
    Classification by factor count and blade composition.
    """
    scale, factors = mv.blade_factorize_versor()
    n = len(factors)

    if n == 1:
        return _classify_single_reflector(factors[0])
    elif n == 2:
        return _classify_double_reflector(factors)
    elif n == 4:
        return _classify_quad_reflector(factors)
    else:
        raise ValueError(f"Unexpected {n} factors for N3 versor")


def _classify_single_reflector(n: MV):
    """1 factor → Reflection or Inversion.

    Reflection: {e1, e2, e3, ei} — no eo component
    Inversion:  {e1, e2, e3, ei, eo} — includes eo
    """
    has_eo = _factor_has_eo(n)
    if has_eo:
        return Inversion(origin=_factor_to_point_n3(n, n._alg))
    else:
        return Reflection(
            normal=Direction(float(n[1]), float(n[2]), float(n[4]))
        )


def _classify_double_reflector(factors):
    """2 factors → Rotor, Translator, Dilator, or GeneralDilator."""
    is_einf = [_factor_has_einf(f) for f in factors]
    is_eo = [_factor_has_eo(f) for f in factors]

    if not any(is_einf) and not any(is_eo):
        return _rotor_from_factors(factors[0], factors[1])
    elif any(is_einf) and not any(is_eo):
        return _translator_from_factors(factors)
    elif any(is_eo) and not any(is_einf):
        return Dilator(factor=1.0)  # needs proper extraction
    else:
        return GeneralDilator(factor=1.0)  # needs proper extraction


def _classify_quad_reflector(factors):
    """4 factors → Motor or GeneralRotor."""
    ...


# --- Factory Functions ---

def make_point(alg, x: float, y: float, z: float) -> MV:
    """N3 conformal point."""
    r_sq = x * x + y * y + z * z
    return alg.multivector({
        1: x,                        # e1
        2: y,                        # e2
        4: z,                        # e3
        8: 0.5 * (r_sq - 1),         # ep
        16: 0.5 * (r_sq + 1),        # em
    })


def make_translator(alg, dx: float, dy: float, dz: float) -> MV:
    """N3 translator: 1 - 0.5*(dx·e1i + dy·e2i + dz·e3i)."""
    # e1i = e1∧einf: e1∧ep=9, e1∧em=17
    return alg.multivector({
        0: 1.0,           # scalar
        9: -0.5 * dx,     # e1∧ep
        17: -0.5 * dx,    # e1∧em
        10: -0.5 * dy,    # e2∧ep
        18: -0.5 * dy,    # e2∧em
        12: -0.5 * dz,    # e3∧ep
        20: -0.5 * dz,    # e3∧em
    })


# --- Helpers ---

def _get_grades(mv: MV) -> set[int]:
    return {b.bit_count() for b in mv.blade_ids()}


def _make_einf(alg) -> MV:
    """Construct einf = ep + em."""
    return alg.multivector({8: 1.0, 16: 1.0})


def _is_conformal_point(factor: MV) -> bool:
    """Check if factor represents a conformal point (has both Euclidean and null components)."""
    has_euclidean = (
        abs(float(factor[1])) > 1e-15
        or abs(float(factor[2])) > 1e-15
        or abs(float(factor[4])) > 1e-15
    )
    has_null = (
        abs(float(factor[8])) > 1e-15
        or abs(float(factor[16])) > 1e-15
    )
    return has_euclidean and has_null


def _factor_to_point_n3(factor: MV, alg) -> Point:
    """Convert a factor vector (grade-1, conformal) to Euclidean Point."""
    einf = _make_einf(alg)
    f_eo = -float(factor.sp(einf))
    if abs(f_eo) < 1e-15:
        # Direction — should not happen for a proper point factor
        return Point(x=float(factor[1]), y=float(factor[2]), z=float(factor[4]))
    return Point(
        x=float(factor[1]) / f_eo,
        y=float(factor[2]) / f_eo,
        z=float(factor[4]) / f_eo,
    )


def _factor_has_einf(factor: MV) -> bool:
    """Check if factor has einf component (nonzero ep or em)."""
    return abs(float(factor[8])) > 1e-15 or abs(float(factor[16])) > 1e-15


def _factor_has_eo(factor: MV) -> bool:
    """Check if factor has eo component (the eo-weighted combination of ep/em).

    eo = 0.5*em - 0.5*ep. If the factor has nonzero coefficients on ep/em
    that do not cancel (i.e. are not purely einf = ep+em), then it has eo.
    
    einf = ep+em → coeff_ep = coeff_em
    eo   = 0.5*em - 0.5*ep → coeff_em = -coeff_ep
    
    A factor has eo if coeff_ep ≠ coeff_em (not purely einf).
    """
    ep = float(factor[8])
    em = float(factor[16])
    if abs(ep) < 1e-15 and abs(em) < 1e-15:
        return False  # no null components at all
    # Check if it's purely einf (ep == em)
    return abs(ep - em) > 1e-15  # not purely einf → has eo
```

---

## 6. Implementation Steps

1. Create `py/pytanga/geometry/analysis_n3.py`.
2. Implement `analyze_entity()`: 7 entity types (Point, Direction, PointPair, Line, Circle, Plane, Sphere, Space).
3. Implement Line/Circle distinction by checking for `e123` blade component.
4. Implement Plane/Sphere distinction by checking for `e123o` blade component.
5. Implement `analyze_operator()`: 8 operator types classified by factor count and blade composition.
6. Implement separation of Reflection/Inversion by eo component detection.
7. Implement factory functions for each supported entity/operator type.

## 7. Verification Checklist

- [ ] Point extraction uses SP(point, einf) to get eo weight (C++ compatible)
- [ ] Direction detected when SP(point, einf) ≈ 0
- [ ] Point pair correctly decomposes into 2 points
- [ ] Line vs Circle: e123 presence distinguishes them
- [ ] Plane vs Sphere: e123o presence distinguishes them
- [ ] Reflection vs Inversion: eo component presence distinguishes them
- [ ] Rotor, Translator, Dilator, GeneralDilator correctly classified by factor composition
- [ ] Motor and GeneralRotor correctly classified by 4-factor composition
- [ ] Round-trip for each entity/operator type